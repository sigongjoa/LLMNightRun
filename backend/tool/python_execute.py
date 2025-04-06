"""
LLMNightRun Python 실행 도구 모듈

Python 코드를 안전하게 실행하는 도구를 정의합니다.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

from backend.config import settings
from backend.logger import get_logger
from backend.models.agent import ToolResult
from backend.tool.base import BaseTool


logger = get_logger(__name__)


class PythonExecute(BaseTool):
    """Python 실행 도구
    
    Python 코드를 안전하게 실행하는 도구입니다.
    코드는 임시 파일에 작성되어 별도의 프로세스에서 실행됩니다.
    """
    
    name: str = "python_execute"
    description: str = """
    Python 코드를 실행하는 도구입니다.
    제공된 코드를 실행하고 결과를 반환합니다.
    작업 공간의 파일을 읽거나 수정할 수 있습니다.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None, timeout: int = 30):
        """Python 실행 도구 초기화
        
        Args:
            workspace_root: 작업 공간 루트 경로 (선택 사항)
            timeout: 실행 시간 제한 (초)
        """
        self.workspace_root = workspace_root or settings.workspace_root
        self.timeout = timeout
    
    async def execute(
        self,
        code: str,
        args: Optional[Dict[str, Any]] = None,
        save_to: Optional[str] = None,
        pip_install: Optional[str] = None,
    ) -> ToolResult:
        """도구 실행
        
        Args:
            code: 실행할 Python 코드
            args: 코드에 전달할 인자 (선택 사항)
            save_to: 코드를 저장할 파일 경로 (선택 사항)
            pip_install: 설치할 패키지 목록 (선택 사항)
            
        Returns:
            ToolResult: 실행 결과
            
        Raises:
            ValueError: 잘못된 인자인 경우
            TimeoutError: 실행 시간 초과인 경우
        """
        # 인자 확인
        if not code or not code.strip():
            return ToolResult(
                output="",
                error="실행할 코드가 제공되지 않았습니다."
            )
        
        # 패키지 설치 (필요한 경우)
        if pip_install:
            install_result = await self._install_packages(pip_install)
            if install_result.error:
                return install_result
        
        # 코드 저장 (필요한 경우)
        if save_to:
            abs_path = self._resolve_path(save_to)
            try:
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                logger.info(f"코드를 파일에 저장했습니다: {abs_path}")
            except Exception as e:
                return ToolResult(
                    output="",
                    error=f"코드 저장 오류: {str(e)}"
                )
        
        # 인자 처리
        args_str = ""
        if args:
            args_str = f"import json; args = json.loads('''{json.dumps(args)}''')\n"
        
        # 환경 변수 설정
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(self.workspace_root).parent)
        
        # 임시 파일에 코드 쓰기
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as temp:
            temp.write(args_str)
            temp.write(code)
            temp_name = temp.name
        
        try:
            # 코드 실행
            result = subprocess.run(
                ["python", temp_name],
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # 결과 처리
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if result.returncode != 0:
                return ToolResult(
                    output=stdout,
                    error=f"코드 실행 오류 (종료 코드 {result.returncode}):\n{stderr}"
                )
            
            # 성공 결과
            output = stdout
            if stderr:
                output += f"\n\n경고:\n{stderr}"
            
            return ToolResult(output=output)
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                output="",
                error=f"실행 시간이 {self.timeout}초를 초과했습니다."
            )
        except Exception as e:
            return ToolResult(
                output="",
                error=f"코드 실행 중 오류 발생: {str(e)}"
            )
        finally:
            # 임시 파일 삭제
            try:
                os.unlink(temp_name)
            except:
                pass
    
    async def _install_packages(self, packages: str) -> ToolResult:
        """패키지 설치
        
        Args:
            packages: 설치할 패키지 목록 (공백으로 구분)
            
        Returns:
            ToolResult: 설치 결과
        """
        try:
            # 패키지 설치
            result = subprocess.run(
                ["pip", "install"] + packages.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 결과 처리
            if result.returncode != 0:
                return ToolResult(
                    output="",
                    error=f"패키지 설치 오류:\n{result.stderr}"
                )
            
            return ToolResult(output=f"패키지 설치 완료: {packages}")
            
        except Exception as e:
            return ToolResult(
                output="",
                error=f"패키지 설치 중 오류 발생: {str(e)}"
            )
    
    def _resolve_path(self, filepath: str) -> str:
        """파일 경로 해석
        
        작업 공간 루트를 기준으로 상대 경로를 절대 경로로 변환합니다.
        
        Args:
            filepath: 파일 경로
            
        Returns:
            str: 절대 파일 경로
        """
        if os.path.isabs(filepath):
            return filepath
        
        # 상대 경로인 경우 작업 공간 루트와 결합
        return os.path.normpath(os.path.join(self.workspace_root, filepath))