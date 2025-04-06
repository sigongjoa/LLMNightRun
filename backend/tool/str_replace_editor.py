"""
LLMNightRun 문자열 대체 에디터 도구 모듈

파일 내용을 수정하는 문자열 대체 에디터 도구를 정의합니다.
"""

import os
from pathlib import Path
from typing import Optional

from backend.config import settings
from backend.logger import get_logger
from backend.models.agent import ToolResult
from backend.tool.base import BaseTool


logger = get_logger(__name__)


class StrReplaceEditor(BaseTool):
    """문자열 대체 에디터 도구
    
    파일 내용을 문자열 대체 방식으로 수정하는 도구입니다.
    특정 문자열을 다른 문자열로 바꾸거나, 전체 내용을 새로운 내용으로 교체할 수 있습니다.
    """
    
    name: str = "str_replace_editor"
    description: str = """
    파일을 편집하는 도구입니다.
    특정 문자열을 다른 문자열로 바꾸거나, 전체 내용을 새로운 내용으로 교체할 수 있습니다.
    작업 공간 경로를 기준으로 상대 경로나 절대 경로를 사용할 수 있습니다.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        """에디터 도구 초기화
        
        Args:
            workspace_root: 작업 공간 루트 경로 (선택 사항)
        """
        self.workspace_root = workspace_root or settings.workspace_root
    
    async def execute(
        self,
        filepath: str,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        new_content: Optional[str] = None,
    ) -> ToolResult:
        """도구 실행
        
        Args:
            filepath: 파일 경로
            old_str: 대체할 문자열 (new_str와 함께 사용)
            new_str: 새 문자열 (old_str와 함께 사용)
            new_content: 전체 내용을 대체할 새 내용
            
        Returns:
            ToolResult: 실행 결과
            
        Raises:
            ValueError: 파라미터가 잘못된 경우
            FileNotFoundError: 파일이 없는 경우
        """
        # 절대 경로 해석
        abs_path = self._resolve_path(filepath)
        
        # 파일 존재 여부 확인
        if not os.path.isfile(abs_path):
            return ToolResult(
                output="",
                error=f"파일을 찾을 수 없습니다: {filepath}"
            )
        
        # 파일 읽기
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ToolResult(
                output="",
                error=f"파일 읽기 오류: {str(e)}"
            )
        
        # 편집 모드 결정
        if new_content is not None:
            # 전체 내용 교체 모드
            updated_content = new_content
            changes = f"전체 내용이 새로운 내용으로 대체되었습니다."
        elif old_str is not None and new_str is not None:
            # 부분 대체 모드
            if old_str not in content:
                return ToolResult(
                    output="",
                    error=f"지정한 문자열을 찾을 수 없습니다: '{old_str}'"
                )
            updated_content = content.replace(old_str, new_str)
            changes = f"'{old_str}'가 '{new_str}'로 대체되었습니다."
        else:
            return ToolResult(
                output="",
                error="old_str와 new_str 모두 또는 new_content를 지정해야 합니다."
            )
        
        # 변경 사항이 있는지 확인
        if content == updated_content:
            return ToolResult(output=f"변경 사항이 없습니다: {filepath}")
        
        # 파일 쓰기
        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
        except Exception as e:
            return ToolResult(
                output="",
                error=f"파일 쓰기 오류: {str(e)}"
            )
        
        return ToolResult(output=f"파일 '{filepath}'이(가) 업데이트되었습니다. {changes}")
    
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