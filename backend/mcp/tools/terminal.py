"""
윈도우 터미널 MCP 도구

윈도우 명령 프롬프트나 PowerShell과 같은 터미널에서 명령어를 실행하는 기능을 제공합니다.
"""

import os
import uuid
import asyncio
import subprocess
import logging
import platform
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

logger = logging.getLogger("mcp.tools.terminal")

class TerminalSession:
    """터미널 세션
    
    단일 터미널 인스턴스를 나타내는 클래스입니다.
    명령어 실행 기록과 작업 디렉터리를 관리합니다.
    """
    
    def __init__(self, session_id: str, working_dir: str = None):
        """터미널 세션 초기화
        
        Args:
            session_id: 세션 ID
            working_dir: 초기 작업 디렉터리 (기본값: 시스템 임시 디렉터리)
        """
        self.session_id = session_id
        self.working_dir = working_dir or tempfile.gettempdir()
        self.history = []
        self.env_vars = os.environ.copy()
        self.created_at = datetime.utcnow().isoformat()
        self.last_accessed = self.created_at
    
    def add_to_history(self, command: str, result: Dict[str, Any]):
        """명령어 실행 기록 추가
        
        Args:
            command: 실행한 명령어
            result: 실행 결과
        """
        self.history.append({
            "command": command,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_accessed = datetime.utcnow().isoformat()


class TerminalTool:
    """윈도우 터미널 도구
    
    윈도우 명령 프롬프트나 PowerShell과 같은 터미널에서 명령어를 실행하는 기능을 제공합니다.
    """
    
    def __init__(self, max_sessions: int = 10, default_timeout: int = 30):
        """터미널 도구 초기화
        
        Args:
            max_sessions: 최대 세션 수
            default_timeout: 기본 명령어 실행 제한 시간 (초)
        """
        self._sessions: Dict[str, TerminalSession] = {}
        self._max_sessions = max_sessions
        self._default_timeout = default_timeout
        
        # 허용된 명령어 목록 (보안을 위해)
        self._allowed_commands = {
            "cmd", "powershell", "dir", "ls", "cd", "pwd", 
            "echo", "type", "cat", "python", "pip",
            "git", "npm", "node", "ping"
        }
        
        # 금지된 명령어 및 옵션 목록
        self._forbidden_commands = {
            "rm -rf", "deltree", "format", "dd", 
            "shutdown", "reboot", "taskkill"
        }
    
    def create_session(self, working_dir: str = None) -> str:
        """터미널 세션 생성
        
        Args:
            working_dir: 초기 작업 디렉터리
            
        Returns:
            str: 세션 ID
        """
        # 최대 세션 수 확인
        if len(self._sessions) >= self._max_sessions:
            # 가장 오래된 세션 제거
            oldest_session_id = sorted(
                self._sessions.keys(),
                key=lambda sid: self._sessions[sid].last_accessed
            )[0]
            del self._sessions[oldest_session_id]
        
        # 새 세션 ID 생성
        session_id = str(uuid.uuid4())
        
        # 세션 생성
        self._sessions[session_id] = TerminalSession(session_id, working_dir)
        logger.info(f"Terminal session created: {session_id}")
        
        return session_id
    
    def delete_session(self, session_id: str) -> bool:
        """터미널 세션 삭제
        
        Args:
            session_id: 세션 ID
            
        Returns:
            bool: 세션 삭제 성공 여부
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Terminal session deleted: {session_id}")
            return True
        return False
    
    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """터미널 세션 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Optional[TerminalSession]: 터미널 세션 (없으면 None)
        """
        return self._sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """터미널 세션 목록 조회
        
        Returns:
            List[Dict[str, Any]]: 세션 정보 목록
        """
        return [
            {
                "session_id": session.session_id,
                "working_dir": session.working_dir,
                "created_at": session.created_at,
                "last_accessed": session.last_accessed,
                "command_count": len(session.history)
            }
            for session in self._sessions.values()
        ]
    
    def _is_command_allowed(self, command: str) -> bool:
        """명령어 허용 여부 확인
        
        보안을 위해 실행 가능한 명령어를 제한합니다.
        
        Args:
            command: 명령어
            
        Returns:
            bool: 명령어 허용 여부
        """
        # 명령어 추출 (옵션 제외)
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return False
        
        base_cmd = cmd_parts[0].lower()
        
        # 금지된 명령어 확인
        for forbidden in self._forbidden_commands:
            if forbidden in command.lower():
                return False
        
        # 허용된 명령어 확인
        return base_cmd in self._allowed_commands
    
    async def execute_command(
        self, 
        session_id: str, 
        command: str, 
        timeout: int = None,
        working_dir: str = None
    ) -> Dict[str, Any]:
        """명령어 실행
        
        지정된 세션에서 터미널 명령어를 실행합니다.
        
        Args:
            session_id: 세션 ID
            command: 실행할 명령어
            timeout: 실행 제한 시간 (초)
            working_dir: 작업 디렉터리 (None인 경우 세션 기본값 사용)
            
        Returns:
            Dict[str, Any]: 실행 결과
            
        Raises:
            ValueError: 잘못된 세션 또는 명령어인 경우
            TimeoutError: 실행 시간 초과인 경우
        """
        # 세션 확인
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Terminal session not found: {session_id}")
        
        # 명령어 유효성 확인
        if not command or not command.strip():
            raise ValueError("Command is empty")
        
        # 명령어 허용 여부 확인
        if not self._is_command_allowed(command):
            return {
                "stdout": "",
                "stderr": "Command not allowed for security reasons",
                "exit_code": 1,
                "error": "COMMAND_NOT_ALLOWED"
            }
        
        # 작업 디렉터리 설정
        work_dir = working_dir or session.working_dir
        
        # 실행 제한 시간 설정
        cmd_timeout = timeout or self._default_timeout
        
        try:
            # 명령어 구성
            if platform.system() == "Windows":
                cmd = ["cmd", "/c", command]
            else:
                cmd = ["/bin/sh", "-c", command]
            
            # 명령어 실행
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=session.env_vars
            )
            
            try:
                # 결과 대기
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=cmd_timeout
                )
                
                # 결과 처리
                result = {
                    "stdout": stdout.decode('utf-8', errors='ignore').strip(),
                    "stderr": stderr.decode('utf-8', errors='ignore').strip(),
                    "exit_code": process.returncode,
                    "error": None
                }
            except asyncio.TimeoutError:
                # 시간 초과 처리
                try:
                    process.kill()
                except:
                    pass
                
                result = {
                    "stdout": "",
                    "stderr": f"Command execution timed out after {cmd_timeout} seconds",
                    "exit_code": -1,
                    "error": "TIMEOUT"
                }
        
        except Exception as e:
            # 예외 처리
            result = {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "error": "EXECUTION_ERROR"
            }
        
        # 'cd' 명령어 처리 (세션 작업 디렉터리 업데이트)
        if command.strip().startswith("cd ") and result["exit_code"] == 0:
            new_dir = command.strip()[3:].strip()
            if os.path.isabs(new_dir):
                session.working_dir = new_dir
            else:
                session.working_dir = os.path.normpath(os.path.join(work_dir, new_dir))
        
        # 명령어 실행 기록 추가
        session.add_to_history(command, result)
        
        return result
    
    def get_history(self, session_id: str, count: int = None) -> List[Dict[str, Any]]:
        """명령어 실행 기록 조회
        
        지정된 세션의 명령어 실행 기록을 조회합니다.
        
        Args:
            session_id: 세션 ID
            count: 조회할 기록 수 (None인 경우 모두 조회)
            
        Returns:
            List[Dict[str, Any]]: 명령어 실행 기록 목록
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        history = session.history
        
        # 개수 제한
        if count is not None and count > 0:
            history = history[-count:]
        
        return history
    
    def get_working_directory(self, session_id: str) -> Optional[str]:
        """작업 디렉터리 조회
        
        지정된 세션의 현재 작업 디렉터리를 조회합니다.
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Optional[str]: 작업 디렉터리 (세션이 없으면 None)
        """
        session = self.get_session(session_id)
        return session.working_dir if session else None
    
    def set_working_directory(self, session_id: str, working_dir: str) -> bool:
        """작업 디렉터리 설정
        
        지정된 세션의 작업 디렉터리를 설정합니다.
        
        Args:
            session_id: 세션 ID
            working_dir: 작업 디렉터리
            
        Returns:
            bool: 설정 성공 여부
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # 디렉터리 존재 확인
        if not os.path.isdir(working_dir):
            return False
        
        session.working_dir = working_dir
        session.last_accessed = datetime.utcnow().isoformat()
        return True
