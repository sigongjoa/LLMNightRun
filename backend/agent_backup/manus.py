"""
LLMNightRun Manus 에이전트 모듈

Manus(매뉴얼) 에이전트는 수동 지침을 따르는 에이전트입니다.
"""

from typing import List, Optional, Dict, Any

from pydantic import Field

from backend.agent.base import BaseAgent
from backend.models.enums import AgentState
from backend.models.agent import Message
from backend.tool.base import BaseTool, ToolCollection
from backend.tool.github_tool import GitHubTool
from backend.tool.python_execute import PythonExecute
from backend.tool.str_replace_editor import StrReplaceEditor
from backend.tool.terminate import Terminate
from backend.logger import get_logger

logger = get_logger(__name__)


class Manus(BaseAgent):
    """Manus(매뉴얼) 에이전트
    
    사용자의 수동 지침에 따라 작업을 수행하는 간단한 에이전트입니다.
    """
    
    name: str = "manus"
    description: str = "수동 지침을 따르는 에이전트"
    
    system_prompt: str = "당신은 사용자의 수동 지침을 따르는 에이전트입니다."
    prompt_template: str = "{prompt}"
    
    available_tools: ToolCollection = Field(default_factory=ToolCollection)
    
    async def step(self) -> str:
        """단일 단계 실행
        
        Returns:
            str: 실행 결과
        """
        # 다음 단계가 없으면 종료
        if self.current_step >= self.max_steps:
            self.state = AgentState.FINISHED
            return "최대 단계 수에 도달했습니다."
        
        # 사용자 입력 처리
        if not self.messages or len(self.messages) == 0:
            return "사용자 메시지가 없습니다."
        
        user_msg = self.messages[-1] if self.messages[-1].role == "user" else None
        if not user_msg:
            return "마지막 메시지가 사용자 메시지가 아닙니다."
        
        # 사용자 입력에 대한 응답 처리
        try:
            # LLM에 질문
            response = await self.llm.ask(
                messages=self.messages,
                system_msgs=[Message.system_message(self.system_prompt)] if self.system_prompt else None
            )
            
            # 응답 저장
            self.memory.add_message(Message.assistant_message(response))
            
            return response
        except Exception as e:
            logger.error(f"단계 실행 중 오류 발생: {e}")
            self.state = AgentState.ERROR
            return f"오류: {str(e)}"
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 반환
        
        Returns:
            List[Dict[str, Any]]: 도구 정의 목록
        """
        tools = []
        if self.available_tools:
            for name, tool in self.available_tools.tool_map.items():
                tools.append({
                    "name": name,
                    "description": tool.description
                })
        return tools
    
    @classmethod
    def create_default(cls, **kwargs) -> "Manus":
        """기본 Manus 에이전트 생성
        
        Returns:
            Manus: 기본 도구가 설정된 Manus 에이전트
        """
        agent = cls(**kwargs)
        
        # 기본 도구 설정
        tools = ToolCollection(
            GitHubTool(),
            PythonExecute(),
            StrReplaceEditor(),
            Terminate()
        )
        agent.available_tools = tools
        
        return agent


# 기존 도구 패키지 내보내기
__all__ = [
    "Manus",
    "BaseTool",
    "ToolCollection",
    "GitHubTool",
    "PythonExecute",
    "StrReplaceEditor",
    "Terminate",
]