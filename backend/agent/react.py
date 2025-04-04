"""
LLMNightRun ReAct 에이전트 모듈

생각(Reasoning)하고 행동(Acting)하는 에이전트 패턴을 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import Field

from backend.agent.base import BaseAgent
from backend.llm import LLM
from backend.schema import AgentState, Memory


class ReActAgent(BaseAgent, ABC):
    """ReAct 패턴 기반 에이전트
    
    생각하고 행동하는 두 단계로 작업을 수행하는 에이전트 패턴을 구현합니다.
    """
    
    name: str
    description: Optional[str] = None

    system_prompt: Optional[str] = None
    next_step_prompt: Optional[str] = None

    llm: Optional[LLM] = Field(default_factory=LLM)
    memory: Memory = Field(default_factory=Memory)
    state: AgentState = AgentState.IDLE

    max_steps: int = 10
    current_step: int = 0

    @abstractmethod
    async def think(self) -> bool:
        """현재 상태를 평가하고 다음 행동 결정
        
        Returns:
            bool: 행동 수행 여부
        """
        pass

    @abstractmethod
    async def act(self) -> str:
        """결정된 행동 수행
        
        Returns:
            str: 행동 결과
        """
        pass

    async def step(self) -> str:
        """단일 단계 실행: 생각하고 행동
        
        Returns:
            str: 단계 실행 결과
        """
        should_act = await self.think()
        if not should_act:
            return "생각 완료 - 행동 불필요"
        return await self.act()