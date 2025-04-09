"""
LM Studio 연동 모듈

이 모듈은 LM Studio의 모델을 활용하여 GitHub 모델 설치 및 설정을 자동화합니다.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple, Union


logger = logging.getLogger(__name__)


class LMStudioConnector:
    """LM Studio와 연동하는 클래스"""
    
    def __init__(self, api_url: str = "http://localhost:1234/v1"):
        """
        초기화 함수
        
        Args:
            api_url: LM Studio API URL (기본값: "http://localhost:1234/v1")
        """
        self.api_url = api_url
    
    def test_connection(self) -> bool:
        """
        LM Studio 연결 테스트
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            response = requests.get(f"{self.api_url}/models")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error connecting to LM Studio: {str(e)}")
            return False
    
    def analyze_repository(self, repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        리포지토리 분석 결과를 바탕으로 설치 방법 생성
        
        Args:
            repo_analysis: 리포지토리 분석 결과
            
        Returns:
            Dict[str, Any]: 설치 방법 정보
        """
        try:
            # 프롬프트 생성
            prompt = self._create_repo_analysis_prompt(repo_analysis)
            
            # LM Studio 호출
            response = self._call_lm_studio(prompt)
            
            # 응답 파싱
            install_info = self._parse_install_info(response)
            
            return install_info
        except Exception as e:
            logger.error(f"Error analyzing repository with LM Studio: {str(e)}")
            return {"error": str(e)}
    
    def generate_setup_script(self, repo_analysis: Dict[str, Any], model_dir: str) -> Dict[str, Any]:
        """
        설치 스크립트 생성
        
        Args:
            repo_analysis: 리포지토리 분석 결과
            model_dir: 모델 디렉토리 경로
            
        Returns:
            Dict[str, Any]: 설치 스크립트 정보
        """
        try:
            # 프롬프트 생성
            prompt = self._create_setup_script_prompt(repo_analysis, model_dir)
            
            # LM Studio 호출
            response = self._call_lm_studio(prompt)
            
            # 응답 파싱
            script_info = self._parse_script_info(response)
            
            return script_info
        except Exception as e:
            logger.error(f"Error generating setup script with LM Studio: {str(e)}")
            return {"error": str(e)}
    
    def analyze_error_log(self, error_log: str) -> Dict[str, Any]:
        """
        에러 로그 분석
        
        Args:
            error_log: 에러 로그
            
        Returns:
            Dict[str, Any]: 분석 결과 및 해결 방안
        """
        try:
            # 프롬프트 생성
            prompt = self._create_error_analysis_prompt(error_log)
            
            # LM Studio 호출
            response = self._call_lm_studio(prompt)
            
            # 응답 파싱
            error_analysis = json.loads(response) if response.startswith("{") else {"analysis": response}
            
            return error_analysis
        except Exception as e:
            logger.error(f"Error analyzing error log with LM Studio: {str(e)}")
            return {"error": str(e)}
    
    def _create_repo_analysis_prompt(self, repo_analysis: Dict[str, Any]) -> str:
        """
        리포지토리 분석 프롬프트 생성
        
        Args:
            repo_analysis: 리포지토리 분석 결과
            
        Returns:
            str: 생성된 프롬프트
        """
        # 주요 정보 추출
        repo_url = repo_analysis.get("repo_url", "Unknown")
        repo_name = repo_analysis.get("repo_name", "Unknown")
        model_type = repo_analysis.get("model_type", {}).get("primary", "Unknown")
        
        # README 내용 추출
        readme = repo_analysis.get("readme", {}).get("content", "")
        
        # 요구사항 파일 내용 추출
        requirements = repo_analysis.get("requirements", {})
        req_content = ""
        for req_file, req_info in requirements.items():
            req_content += f"\n--- {req_file} ---\n{req_info.get('content', '')}\n"
        
        # 파일 구조 (일부만 포함)
        file_structure = repo_analysis.get("file_structure", [])
        file_structure_str = "\n".join(file_structure[:50])
        if len(file_structure) > 50:
            file_structure_str += f"\n... and {len(file_structure) - 50} more files"
        
        # 실행 스크립트
        launch_scripts = repo_analysis.get("launch_scripts", [])
        launch_scripts_str = ", ".join(launch_scripts) if launch_scripts else "None identified"
        
        # 프롬프트 조합
        prompt = f"""
You are an AI assistant specialized in analyzing GitHub repositories containing machine learning models and helping to set them up automatically.

# Repository Information
- Repository URL: {repo_url}
- Repository Name: {repo_name}
- Model Type: {model_type}

# README Content (partial)
{readme[:2000]}
{'' if len(readme) <= 2000 else '... (README continues)'}

# Requirements Files
{req_content}

# File Structure (partial)
{file_structure_str}

# Launch Scripts
{launch_scripts_str}

Based on the information above, please provide:
1. What Python dependencies need to be installed (main packages only)
2. What are the key setup steps needed to make this model run
3. How to launch/run the model (main script and typical parameters)
4. Any weight files that need to be downloaded
5. Any configuration files that need to be created or modified

Format your response as a JSON with the following structure:
```json
{{
  "dependencies": ["package1", "package2", ...],
  "setup_steps": ["step1", "step2", ...],
  "launch_command": "python script.py --param value",
  "weight_files": [
    {{
      "url": "https://example.com/weights.bin",
      "path": "weights/model.bin",
      "description": "Main model weights"
    }}
  ],
  "config_files": [
    {{
      "path": "config/config.json",
      "content": "{{...}}",
      "description": "Main configuration"
    }}
  ]
}}
```

Provide only your analysis in JSON format without any additional text.
"""
        
        return prompt
    
    def _create_setup_script_prompt(self, repo_analysis: Dict[str, Any], model_dir: str) -> str:
        """
        설치 스크립트 프롬프트 생성
        
        Args:
            repo_analysis: 리포지토리 분석 결과
            model_dir: 모델 디렉토리 경로
            
        Returns:
            str: 생성된 프롬프트
        """
        model_name = repo_analysis.get("repo_name", "Unknown")
        model_type = repo_analysis.get("model_type", {}).get("primary", "Unknown")
        
        # 설치 정보 직렬화
        install_info = repo_analysis.get("install_info", {})
        install_info_str = json.dumps(install_info, indent=2)
        
        prompt = f"""
You are an AI assistant specialized in creating setup scripts for machine learning models.

# Model Information
- Model Name: {model_name}
- Model Type: {model_type}
- Model Directory: {model_dir}

# Installation Information
```json
{install_info_str}
```

Based on the information above, please generate a Python setup script that will:
1. Install all required dependencies
2. Download necessary model weights
3. Set up the configuration files
4. Prepare everything needed to run the model

The script should be self-contained and handle errors gracefully.
It should print progress information during execution.

Format your response as a Python script without any additional markdown formatting or explanations.
Just provide the Python code that can be saved directly to a file and executed.
"""
        
        return prompt
    
    def _create_error_analysis_prompt(self, error_log: str) -> str:
        """
        에러 로그 분석 프롬프트 생성
        
        Args:
            error_log: 에러 로그
            
        Returns:
            str: 생성된 프롬프트
        """
        # 에러 로그가 너무 길면 잘라내기
        if len(error_log) > 4000:
            error_log = error_log[:4000] + "...\n(log truncated for brevity)"
        
        prompt = f"""
You are an AI assistant specialized in analyzing error logs from machine learning model setup and execution.

# Error Log
```
{error_log}
```

Please analyze this error log and provide:
1. What is the main error/issue?
2. What might be causing this error?
3. How to resolve this issue?

Format your response as a JSON with the following structure:
```json
{{
  "error_type": "Brief description of the error type",
  "analysis": "Detailed analysis of what might be causing the error",
  "solution": ["step1 to resolve", "step2 to resolve", ...],
  "severity": "high/medium/low"
}}
```

Provide only your analysis in JSON format without any additional text.
"""
        
        return prompt
    
    def _call_lm_studio(self, prompt: str) -> str:
        """
        LM Studio API 호출
        
        Args:
            prompt: 프롬프트
            
        Returns:
            str: 응답 텍스트
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4096
            }
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected response from LM Studio: {result}")
                return ""
                
        except Exception as e:
            logger.error(f"Error calling LM Studio API: {str(e)}")
            raise
    
    def _parse_install_info(self, response: str) -> Dict[str, Any]:
        """
        LM Studio 응답에서 설치 정보 파싱
        
        Args:
            response: LM Studio 응답 텍스트
            
        Returns:
            Dict[str, Any]: 파싱된 설치 정보
        """
        try:
            # JSON 부분 추출
            json_text = response
            
            # 마크다운 코드 블록으로 감싸져 있는 경우
            json_start = response.find("```json")
            if json_start != -1:
                json_end = response.find("```", json_start + 6)
                if json_end != -1:
                    json_text = response[json_start + 7:json_end].strip()
            
            # 일반 코드 블록으로 감싸져 있는 경우
            if not json_text.startswith("{"):
                json_start = response.find("```")
                if json_start != -1:
                    json_end = response.find("```", json_start + 3)
                    if json_end != -1:
                        json_text = response[json_start + 3:json_end].strip()
            
            # 여전히 JSON 형식이 아닌 경우, JSON 형식만 추출
            if not json_text.startswith("{"):
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response[json_start:json_end]
            
            install_info = json.loads(json_text)
            
            # 기본 필드 확인 및 초기화
            for field in ["dependencies", "setup_steps", "launch_command", "weight_files", "config_files"]:
                if field not in install_info:
                    install_info[field] = [] if field in ["dependencies", "setup_steps", "weight_files", "config_files"] else ""
            
            return install_info
            
        except Exception as e:
            logger.error(f"Error parsing install info from LM Studio response: {str(e)}\nResponse: {response}")
            return {
                "dependencies": [],
                "setup_steps": [],
                "launch_command": "",
                "weight_files": [],
                "config_files": []
            }
    
    def _parse_script_info(self, response: str) -> Dict[str, Any]:
        """
        LM Studio 응답에서 스크립트 정보 파싱
        
        Args:
            response: LM Studio 응답 텍스트
            
        Returns:
            Dict[str, Any]: 파싱된 스크립트 정보
        """
        try:
            # 코드 부분 추출
            script_text = response
            
            # 마크다운 코드 블록으로 감싸져 있는 경우
            python_start = response.find("```python")
            if python_start != -1:
                python_end = response.find("```", python_start + 8)
                if python_end != -1:
                    script_text = response[python_start + 8:python_end].strip()
            
            # 일반 코드 블록으로 감싸져 있는 경우
            if python_start == -1:
                code_start = response.find("```")
                if code_start != -1:
                    code_end = response.find("```", code_start + 3)
                    if code_end != -1:
                        script_text = response[code_start + 3:code_end].strip()
            
            return {
                "script": script_text,
                "filename": "setup.py"
            }
            
        except Exception as e:
            logger.error(f"Error parsing script info from LM Studio response: {str(e)}\nResponse: {response}")
            return {
                "script": "",
                "filename": "setup.py",
                "error": str(e)
            }
