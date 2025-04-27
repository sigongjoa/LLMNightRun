"""
CodeListener is responsible for detecting and processing code blocks in model responses.
It can extract code, detect file paths, recognize execution commands, save code to files,
and execute code in appropriate environments.
"""

import os
import re
import json
import logging
import tempfile
import subprocess
from typing import Dict, List, Optional, Union, Any

# DO NOT CHANGE CODE: Core code listener functionality
# TEMP: Current implementation works but will be refactored later

class CodeListener:
    def __init__(self, code_dir: str = None):
        """
        Initialize the CodeListener with the directory to save code files.
        
        Args:
            code_dir: Directory to save code files
        """
        self.code_dir = code_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "code")
        
        # Ensure code directory exists
        os.makedirs(self.code_dir, exist_ok=True)
        
        # Dictionary to store language-specific execution commands
        self.language_executors = {
            "python": "python",
            "javascript": "node",
            "js": "node",
            "bash": "bash",
            "sh": "bash",
            "shell": "bash",
            "cmd": "cmd /c",
            "powershell": "powershell -Command",
            "ps1": "powershell -Command",
            "batch": "cmd /c",
            "r": "Rscript",
            "ruby": "ruby",
            "perl": "perl",
            "php": "php",
            "java": self._run_java,  # Java needs special handling
            "cpp": self._run_cpp,    # C++ needs special handling
            "c": self._run_c         # C needs special handling
        }
    
    def process_response(self, response_text: str) -> Dict:
        """
        Process a model response to extract and handle code blocks.
        
        Args:
            response_text: Text of the model response
            
        Returns:
            Dictionary with processing results
        """
        results = {
            "code_blocks": [],
            "files_saved": [],
            "execution_results": []
        }
        
        # Extract code blocks
        code_blocks = self.extract_code_blocks(response_text)
        results["code_blocks"] = code_blocks
        
        # Extract file paths
        file_paths = self.extract_file_paths(response_text)
        
        # Extract execution commands
        execute_commands = self.extract_execution_commands(response_text)
        
        # Process each code block
        for i, block in enumerate(code_blocks):
            language = block.get("language", "").lower()
            code = block.get("code", "")
            
            # Skip empty blocks
            if not code.strip():
                continue
            
            # Determine file path
            file_path = None
            if i < len(file_paths):
                file_path = file_paths[i]
            else:
                # Generate a default file path based on language
                extension = self._get_extension_for_language(language)
                file_path = os.path.join(self.code_dir, f"code_{i + 1}{extension}")
            
            # Save code to file
            if file_path:
                try:
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                    
                    # Save code to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(code)
                    
                    # Add to files saved
                    results["files_saved"].append({
                        "path": file_path,
                        "language": language
                    })
                    
                    # Execute code if needed
                    should_execute = i < len(execute_commands) and execute_commands[i]
                    if should_execute:
                        execution_result = self.execute_code(language, file_path)
                        results["execution_results"].append(execution_result)
                
                except Exception as e:
                    logging.error(f"Error processing code block: {e}")
                    results["execution_results"].append({
                        "success": False,
                        "output": str(e),
                        "language": language,
                        "path": file_path
                    })
        
        # Check for tool calls
        tool_calls = self.extract_tool_calls(response_text)
        if tool_calls:
            results["tool_calls"] = tool_calls
        
        return results
    
    def extract_code_blocks(self, text: str) -> List[Dict]:
        """
        Extract code blocks from text.
        
        Args:
            text: Text to extract code blocks from
            
        Returns:
            List of dictionaries with language and code
        """
        code_blocks = []
        
        # Regex pattern to match code blocks (```language\ncode\n```)
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            language = match.group(1).strip().lower() or "text"
            code = match.group(2).strip()
            code_blocks.append({
                "language": language,
                "code": code
            })
        
        return code_blocks
    
    def extract_file_paths(self, text: str) -> List[str]:
        """
        Extract file paths from text.
        
        Args:
            text: Text to extract file paths from
            
        Returns:
            List of file paths
        """
        file_paths = []
        
        # Regex patterns to match file paths
        patterns = [
            r'(?:file path|filepath|path|save to|save as|write to):\s*(.+\.[\w]+)',
            r'(?:create file|new file|create a file at):\s*(.+\.[\w]+)',
            r'(?:save|write)\s+this\s+(?:code|file)\s+(?:to|as)\s+(.+\.[\w]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                path = match.group(1).strip()
                
                # Check if the path is absolute, if not make it relative to code_dir
                if not os.path.isabs(path):
                    path = os.path.join(self.code_dir, path)
                
                file_paths.append(path)
        
        return file_paths
    
    def extract_execution_commands(self, text: str) -> List[bool]:
        """
        Extract execution commands from text.
        
        Args:
            text: Text to extract execution commands from
            
        Returns:
            List of booleans indicating whether each code block should be executed
        """
        # 코드 블록 먼저 추출하여 각 블록에 대한 실행 여부를 개별적으로 결정
        code_blocks = self.extract_code_blocks(text)
        execution_flags = [False] * len(code_blocks)  # 기본적으로 모든 블록은 실행하지 않음
        
        if not code_blocks:
            return []
        
        # 전체 텍스트에서 실행 관련 구문 검색을 위한 패턴
        general_patterns = [
            r'(?:run|execute|try)\s+(?:this|the|all)\s+(?:code|script)',
            r'(?:run|execute|try)\s+(?:the|all)\s+(?:above|following)\s+(?:code|script)',
            r'(?:to\s+run|to\s+execute)\s+(?:this|the)\s+(?:code|script)',
            r'(?:you\s+can\s+run|you\s+can\s+execute)\s+(?:this|the)\s+(?:code|script)'
        ]
        
        # 전체 텍스트에 대한 전역 실행 명령이 있는지 확인
        global_execute = any(re.search(pattern, text, re.IGNORECASE) for pattern in general_patterns)
        
        # 코드 블록 주변 컨텍스트 확인을 위한 윈도우 크기 (문자 수)
        window_size = 200  # 코드 블록 전후 200자 내의 텍스트를 확인
        
        # 코드 블록 시작과 끝 위치 찾기
        starts_ends = []
        pattern = r'```(\w*)\n(.*?)```'
        for match in re.finditer(pattern, text, re.DOTALL):
            starts_ends.append((match.start(), match.end()))
        
        # 각 코드 블록에 대해 주변 컨텍스트 확인
        for i, (start, end) in enumerate(starts_ends):
            if i >= len(execution_flags):
                break
                
            # 코드 블록 주변 컨텍스트 추출
            before_text = text[max(0, start-window_size):start]
            after_text = text[end:min(end+window_size, len(text))]
            context = before_text + after_text
            
            # 컨텍스트에서 실행 관련 문구 확인
            block_patterns = [
                r'(?:run|execute|try)\s+this\s+(?:code|script)',
                r'(?:to\s+run|to\s+execute)\s+this',
                r'you\s+(?:can|should)\s+(?:run|execute)\s+(?:this|the)\s+(?:code|script)'
            ]
            
            # 이 특정 블록에 대한 실행 지시가 있는지 확인
            block_execute = any(re.search(pattern, context, re.IGNORECASE) for pattern in block_patterns)
            
            # 전역 실행 명령이 있거나 블록별 실행 지시가 있으면 실행
            execution_flags[i] = global_execute or block_execute
        
        # 모든 블록에 대한 실행 여부 반환
        return execution_flags
    
    def extract_tool_calls(self, text: str) -> List[Dict]:
        """
        Extract tool calls from text.
        
        Args:
            text: Text to extract tool calls from
            
        Returns:
            List of tool call dictionaries
        """
        tool_calls = []
        
        # Regex pattern to match JSON tool calls
        pattern = r'```json\s*(.*?)```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            json_str = match.group(1).strip()
            try:
                tool_call = json.loads(json_str)
                
                # Check if it looks like a tool call (has function and arguments)
                if isinstance(tool_call, dict) and "function" in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                # Not valid JSON, skip
                continue
        
        return tool_calls
    
    def execute_code(self, language: str, file_path: str) -> Dict:
        """
        Execute code in an appropriate environment.
        
        Args:
            language: Language of the code
            file_path: Path to the file containing the code
            
        Returns:
            Dictionary with execution results
        """
        try:
            language = language.lower()
            result = {
                "success": False,
                "output": "",
                "language": language,
                "path": file_path
            }
            
            # Check if we have an executor for this language
            executor = self.language_executors.get(language)
            if not executor:
                result["output"] = f"Execution not supported for language: {language}"
                return result
            
            # If executor is a function, call it
            if callable(executor):
                success, output = executor(file_path)
                result["success"] = success
                result["output"] = output
                return result
            
            # Otherwise, use subprocess to execute
            command = f"{executor} {file_path}"
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for process to complete (with timeout)
            stdout, stderr = process.communicate(timeout=30)
            
            # Check if execution was successful
            if process.returncode == 0:
                result["success"] = True
                result["output"] = stdout
            else:
                result["output"] = stderr if stderr else stdout
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "Execution timed out after 30 seconds",
                "language": language,
                "path": file_path
            }
        except Exception as e:
            return {
                "success": False,
                "output": str(e),
                "language": language,
                "path": file_path
            }
    
    def _get_extension_for_language(self, language: str) -> str:
        """
        Get the file extension for a language.
        
        Args:
            language: Language to get extension for
            
        Returns:
            File extension for the language
        """
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "js": ".js",
            "bash": ".sh",
            "sh": ".sh",
            "shell": ".sh",
            "cmd": ".cmd",
            "batch": ".bat",
            "powershell": ".ps1",
            "ps1": ".ps1",
            "ruby": ".rb",
            "perl": ".pl",
            "php": ".php",
            "java": ".java",
            "cpp": ".cpp",
            "c": ".c",
            "csharp": ".cs",
            "cs": ".cs",
            "go": ".go",
            "rust": ".rs",
            "r": ".R",
            "html": ".html",
            "css": ".css",
            "sql": ".sql"
        }
        
        return extensions.get(language.lower(), ".txt")
    
    def _run_java(self, file_path: str) -> tuple:
        """
        Run a Java file (compile and execute).
        
        Args:
            file_path: Path to the Java file
            
        Returns:
            Tuple of (success, output)
        """
        try:
            # Get the class name from the file
            class_name = os.path.basename(file_path).replace(".java", "")
            directory = os.path.dirname(file_path)
            
            # Compile the Java file
            compile_process = subprocess.Popen(
                f"javac {file_path}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            compile_stdout, compile_stderr = compile_process.communicate(timeout=30)
            
            if compile_process.returncode != 0:
                return False, f"Compilation failed:\n{compile_stderr}"
            
            # Run the compiled class
            run_process = subprocess.Popen(
                f"java -cp {directory} {class_name}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            run_stdout, run_stderr = run_process.communicate(timeout=30)
            
            if run_process.returncode != 0:
                return False, f"Execution failed:\n{run_stderr}"
            
            return True, run_stdout
            
        except Exception as e:
            return False, str(e)
    
    def _run_cpp(self, file_path: str) -> tuple:
        """
        Run a C++ file (compile and execute).
        
        Args:
            file_path: Path to the C++ file
            
        Returns:
            Tuple of (success, output)
        """
        try:
            # Generate output file name
            output_file = os.path.splitext(file_path)[0]
            if os.name == 'nt':  # Windows
                output_file += ".exe"
            
            # Compile the C++ file
            compile_process = subprocess.Popen(
                f"g++ {file_path} -o {output_file}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            compile_stdout, compile_stderr = compile_process.communicate(timeout=30)
            
            if compile_process.returncode != 0:
                return False, f"Compilation failed:\n{compile_stderr}"
            
            # Run the compiled executable
            run_process = subprocess.Popen(
                output_file,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            run_stdout, run_stderr = run_process.communicate(timeout=30)
            
            if run_process.returncode != 0:
                return False, f"Execution failed:\n{run_stderr}"
            
            return True, run_stdout
            
        except Exception as e:
            return False, str(e)
    
    def _run_c(self, file_path: str) -> tuple:
        """
        Run a C file (compile and execute).
        
        Args:
            file_path: Path to the C file
            
        Returns:
            Tuple of (success, output)
        """
        try:
            # Generate output file name
            output_file = os.path.splitext(file_path)[0]
            if os.name == 'nt':  # Windows
                output_file += ".exe"
            
            # Compile the C file
            compile_process = subprocess.Popen(
                f"gcc {file_path} -o {output_file}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            compile_stdout, compile_stderr = compile_process.communicate(timeout=30)
            
            if compile_process.returncode != 0:
                return False, f"Compilation failed:\n{compile_stderr}"
            
            # Run the compiled executable
            run_process = subprocess.Popen(
                output_file,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            run_stdout, run_stderr = run_process.communicate(timeout=30)
            
            if run_process.returncode != 0:
                return False, f"Execution failed:\n{run_stderr}"
            
            return True, run_stdout
            
        except Exception as e:
            return False, str(e)
