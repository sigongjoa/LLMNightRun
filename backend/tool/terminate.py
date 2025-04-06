"""
LLMNightRun 종료 도구 모듈

에이전트 실행을 종료하는 도구를 정의합니다.
"""

from typing import Optional

from backend.models.agent import ToolResult
from backend.tool.base import BaseTool


class Terminate(BaseTool):
    """종료 도구
    
    에이전트 실행을 종료하는 도구입니다.
    에이전트가 작업을 완료했을 때 사용됩니다.
    """
    
    name: str = "terminate"
    description: str = "작업이 완료되면 이 도구를 호출하여 에이전트 실행을 종료합니다."
    
    async def execute(self, reason: Optional[str] = "작업 완료") -> ToolResult:
        """도구 실행
        
        Args:
            reason: 종료 이유 (선택 사항)
            
        Returns:
            ToolResult: 실행 결과
        """
        return ToolResult(output=f"에이전트 실행이 종료되었습니다: {reason}")