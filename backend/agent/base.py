"""
LLMNightRun 기본 에이전트 모듈

모든 에이전트의 기본 클래스를 정의합니다.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from backend.logger import get_logger
from backend.llm import LLM
from backend.schema import AgentState, Memory, Message, ROLE_TYPE
import uuid
from typing import Dict, Any, Optional, List, Union

logger = get_logger(__name__)


class BaseAgent(BaseModel, ABC):
    """에이전트 기본 추상 클래스
    
    모든 에이전트의 기본 기능과 상태 관리를 제공합니다.
    """

    # 기본 속성
    name: str = Field(..., description="에이전트 이름")
    description: Optional[str] = Field(None, description="에이전트 설명")

    # 프롬프트
    system_prompt: Optional[str] = Field(None, description="시스템 지시 프롬프트")
    next_step_prompt: Optional[str] = Field(None, description="다음 단계 결정 프롬프트")

    # 의존성
    llm: LLM = Field(default_factory=LLM, description="LLM 인스턴스")
    memory: Memory = Field(default_factory=Memory, description="에이전트 메모리")
    state: AgentState = Field(default=AgentState.IDLE, description="현재 상태")

    # 실행 제어
    max_steps: int = Field(default=10, description="최대 실행 단계 수")
    current_step: int = Field(default=0, description="현재 실행 단계")

    # 중복 탐지 임계값
    duplicate_threshold: int = 2

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # 하위 클래스에서 추가 필드 허용

    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """에이전트 초기화"""
        if self.llm is None:
            self.llm = LLM(config_name=self.name.lower())
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self

    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """상태 전환 컨텍스트 관리자
        
        Args:
            new_state: 새로운 상태
            
        Yields:
            None: 새 상태에서 실행 허용
            
        Raises:
            ValueError: 잘못된 상태인 경우
        """
        if not isinstance(new_state, AgentState):
            raise ValueError(f"잘못된 상태: {new_state}")

        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR  # 오류 발생 시 ERROR 상태로 전환
            raise e
        finally:
            self.state = previous_state  # 이전 상태로 복원

    def update_memory(
        self,
        role: ROLE_TYPE,
        content: str,
        base64_image: Optional[str] = None,
        **kwargs,
    ) -> None:
        """에이전트 메모리에 메시지 추가
        
        Args:
            role: 메시지 역할 (사용자, 시스템, 어시스턴트, 도구)
            content: 메시지 내용
            base64_image: Base64 인코딩된 이미지 (선택 사항)
            **kwargs: 추가 인자
            
        Raises:
            ValueError: 지원하지 않는 역할인 경우
        """
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content, **kw: Message.tool_message(content, **kw),
        }

        if role not in message_map:
            raise ValueError(f"지원하지 않는 메시지 역할: {role}")

        # 역할에 따라 적절한 인자로 메시지 생성
        kwargs = {"base64_image": base64_image, **(kwargs if role == "tool" else {})}
        self.memory.add_message(message_map[role](content, **kwargs))

    async def run(self, request: Optional[str] = None) -> str:
        """에이전트 메인 루프 실행
        
        Args:
            request: 초기 사용자 요청 (선택 사항)
            
        Returns:
            실행 결과 요약 문자열
            
        Raises:
            RuntimeError: 에이전트가 IDLE 상태가 아닌 경우
        """
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"상태 {self.state}에서 에이전트를 실행할 수 없습니다")

        if request:
            self.update_memory("user", request)

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while (
                self.current_step < self.max_steps and self.state != AgentState.FINISHED
            ):
                self.current_step += 1
                logger.info(f"단계 {self.current_step}/{self.max_steps} 실행 중")
                step_result = await self.step()

                # 반복 탐지
                if self.is_stuck():
                    self.handle_stuck_state()

                results.append(f"단계 {self.current_step}: {step_result}")

            if self.current_step >= self.max_steps:
                self.current_step = 0
                self.state = AgentState.IDLE
                results.append(f"종료: 최대 단계 수({self.max_steps})에 도달")
        
        # 임시: 자원 정리 함수 호출
        await self.cleanup()
        
        return "\n".join(results) if results else "실행된 단계 없음"

    @abstractmethod
    async def step(self) -> str:
        """단일 단계 실행
        
        하위 클래스에서 구현해야 합니다.
        """
        pass

    def handle_stuck_state(self):
        """반복 상태 처리"""
        stuck_prompt = "\
        반복된 응답이 감지되었습니다. 새로운 전략을 고려하고 이미 시도했던 비효율적인 경로를 반복하지 마세요."
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt}"
        logger.warning(f"에이전트가 반복 상태를 감지했습니다. 프롬프트 추가: {stuck_prompt}")

    def is_stuck(self) -> bool:
        """반복 탐지"""
        if len(self.memory.messages) < 2:
            return False

        last_message = self.memory.messages[-1]
        if not last_message.content:
            return False

        # 동일 내용 개수 확인
        duplicate_count = sum(
            1
            for msg in reversed(self.memory.messages[:-1])
            if msg.role == "assistant" and msg.content == last_message.content
        )

        return duplicate_count >= self.duplicate_threshold

    async def cleanup(self):
        """자원 정리"""
        logger.info(f"에이전트 '{self.name}' 자원 정리 중...")

    @property
    def messages(self) -> List[Message]:
        """에이전트 메모리의 메시지 목록 반환"""
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        """에이전트 메모리의 메시지 목록 설정"""
        self.memory.messages = value

        