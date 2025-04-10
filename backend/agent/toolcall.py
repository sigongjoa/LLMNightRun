"""
LLMNightRun 도구 호출 에이전트 모듈

도구/함수 호출을 지원하는 에이전트를 구현합니다.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from backend.agent.react import ReActAgent
from backend.exceptions import TokenLimitExceeded
from backend.logger import get_logger
from backend.models.enums import AgentState, ToolChoice
from backend.models.agent import Message, ToolCall
from backend.tool.base import ToolCollection

logger = get_logger(__name__)


TOOL_CALL_REQUIRED = "도구 호출이 필요하지만 제공되지 않았습니다"


class ToolCallAgent(ReActAgent):
    """도구 호출 에이전트
    
    도구/함수 호출을 처리하는 기능을 갖춘 에이전트 클래스입니다.
    """
    
    name: str = "toolcall"
    description: str = "도구 호출을 실행할 수 있는 에이전트."

    system_prompt: str = "당신은 도구를 사용하여 작업을 수행하는 도우미입니다."
    next_step_prompt: str = "어떤 도구를 사용할지 결정하세요. 가능한 도구 목록에서 선택하거나, 도구가 필요하지 않으면 텍스트로 응답하세요."

    available_tools: ToolCollection = Field(default_factory=ToolCollection)
    tool_choices: ToolChoice = ToolChoice.AUTO
    special_tool_names: List[str] = Field(default_factory=list)

    tool_calls: List[ToolCall] = Field(default_factory=list)
    _current_base64_image: Optional[str] = None

    max_steps: int = 30
    max_observe: Optional[Union[int, bool]] = None

    async def think(self) -> bool:
        """현재 상태를 처리하고 도구를 사용할지 결정
        
        Returns:
            bool: 도구 실행 여부
        """
        if self.next_step_prompt:
            user_msg = Message.user_message(self.next_step_prompt)
            self.messages.append(user_msg)

        try:
            # 도구 옵션과 함께 응답 요청
            response = await self.llm.ask_tool(
                messages=self.messages,
                system_msgs=(
                    [Message.system_message(self.system_prompt)]
                    if self.system_prompt
                    else None
                ),
                tools=self.available_tools.to_params() if self.available_tools else None,
                tool_choice=self.tool_choices,
            )
        except ValueError:
            raise
        except Exception as e:
            # TokenLimitExceeded 오류 확인
            if hasattr(e, "__cause__") and isinstance(e.__cause__, TokenLimitExceeded):
                token_limit_error = e.__cause__
                logger.error(f"🚨 토큰 제한 오류: {token_limit_error}")
                self.memory.add_message(
                    Message.assistant_message(
                        f"최대 토큰 제한에 도달하여 실행을 계속할 수 없습니다: {str(token_limit_error)}"
                    )
                )
                self.state = AgentState.finished
                return False
            raise

        self.tool_calls = tool_calls = (
            response.tool_calls if response and response.tool_calls else []
        )
        content = response.content if response and response.content else ""

        # 응답 로깅
        logger.info(f"✨ {self.name}의 생각: {content}")
        logger.info(f"🛠️ {self.name}이(가) {len(tool_calls) if tool_calls else 0}개의 도구를 선택했습니다")
        if tool_calls:
            logger.info(f"🧰 준비된 도구: {[call.function.name for call in tool_calls]}")
            logger.info(f"🔧 도구 인자: {tool_calls[0].function.arguments}")

        try:
            if response is None:
                raise RuntimeError("LLM에서 응답을 받지 못했습니다")

            # 도구 선택 모드 처리
            if self.tool_choices == ToolChoice.NONE:
                if tool_calls:
                    logger.warning(f"🤔 {self.name}이(가) 사용할 수 없는 도구를 사용하려고 했습니다!")
                if content:
                    self.memory.add_message(Message.assistant_message(content))
                    return True
                return False

            # 어시스턴트 메시지 생성 및 추가
            assistant_msg = (
                Message.from_tool_calls(content=content, tool_calls=self.tool_calls)
                if self.tool_calls
                else Message.assistant_message(content)
            )
            self.memory.add_message(assistant_msg)

            if self.tool_choices == ToolChoice.REQUIRED and not self.tool_calls:
                return True  # act()에서 처리될 것입니다

            # 'auto' 모드에서 도구 호출이 없지만 내용이 있으면 계속 진행
            if self.tool_choices == ToolChoice.AUTO and not self.tool_calls:
                return bool(content)

            return bool(self.tool_calls)
        except Exception as e:
            logger.error(f"🚨 {self.name}의 생각 처리 중 오류 발생: {e}")
            self.memory.add_message(
                Message.assistant_message(
                    f"처리 중 오류 발생: {str(e)}"
                )
            )
            return False

    async def act(self) -> str:
        """도구 호출 실행 및 결과 처리
        
        Returns:
            str: 실행 결과
            
        Raises:
            ValueError: 도구 호출이 요구되지만 없는 경우
        """
        if not self.tool_calls:
            if self.tool_choices == ToolChoice.REQUIRED:
                raise ValueError(TOOL_CALL_REQUIRED)

            # 도구 호출이 없으면 마지막 메시지 내용 반환
            return self.messages[-1].content or "실행할 내용이나 명령이 없습니다"

        results = []
        for command in self.tool_calls:
            # 각 도구 호출마다 base64_image 초기화
            self._current_base64_image = None

            result = await self.execute_tool(command)

            if self.max_observe:
                result = result[:self.max_observe]

            logger.info(f"🎯 도구 '{command.function.name}' 실행 완료! 결과: {result}")

            # 도구 응답을 메모리에 추가
            tool_msg = Message.tool_message(
                content=result,
                tool_call_id=command.id,
                name=command.function.name,
                base64_image=self._current_base64_image,
            )
            self.memory.add_message(tool_msg)
            results.append(result)

        return "\n\n".join(results)

    async def execute_tool(self, command: ToolCall) -> str:
        """단일 도구 호출 실행
        
        Args:
            command: 도구 호출 정보
            
        Returns:
            str: 실행 결과
            
        Raises:
            RuntimeError: 잘못된 명령 형식이나 알 수 없는 도구인 경우
        """
        if not command or not command.function or not command.function.name:
            return "오류: 잘못된 명령 형식"

        name = command.function.name
        if not self.available_tools or name not in self.available_tools.tool_map:
            return f"오류: 알 수 없는 도구 '{name}'"

        try:
            # 인자 파싱
            args = json.loads(command.function.arguments or "{}")

            # 도구 실행
            logger.info(f"🔧 도구 실행 중: '{name}'...")
            result = await self.available_tools.execute(name=name, tool_input=args)

            # 특수 도구 처리
            await self._handle_special_tool(name=name, result=result)

            # 결과에 base64_image가 있는지 확인
            if hasattr(result, "base64_image") and result.base64_image:
                # 나중에 tool_message에서 사용하기 위해 base64_image 저장
                self._current_base64_image = result.base64_image

                # 표시용 결과 포맷
                observation = (
                    f"명령어 `{name}` 실행 결과:\n{str(result)}"
                    if result
                    else f"명령어 `{name}` 실행 완료 (출력 없음)"
                )
                return observation

            # 표준 결과 포맷
            observation = (
                f"명령어 `{name}` 실행 결과:\n{str(result)}"
                if result
                else f"명령어 `{name}` 실행 완료 (출력 없음)"
            )

            return observation
        except json.JSONDecodeError:
            error_msg = f"{name} 인자 파싱 오류: 유효하지 않은 JSON 형식"
            logger.error(f"📝 '{name}'의 인자가 유효하지 않습니다 - 잘못된 JSON 형식, 인자:{command.function.arguments}")
            return f"오류: {error_msg}"
        except Exception as e:
            error_msg = f"⚠️ 도구 '{name}' 실행 중 문제 발생: {str(e)}"
            logger.exception(error_msg)
            return f"오류: {error_msg}"

    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        """특수 도구 실행 및 상태 변경 처리
        
        Args:
            name: 도구 이름
            result: 실행 결과
            **kwargs: 추가 인자
        """
        if not self._is_special_tool(name):
            return

        if self._should_finish_execution(name=name, result=result, **kwargs):
            # 에이전트 상태를 종료로 설정
            logger.info(f"🏁 특수 도구 '{name}'이(가) 작업을 완료했습니다!")
            self.state = AgentState.finished

    @staticmethod
    def _should_finish_execution(**kwargs) -> bool:
        """도구 실행이 에이전트를 종료해야 하는지 결정
        
        Returns:
            bool: 종료 여부
        """
        return True

    def _is_special_tool(self, name: str) -> bool:
        """도구 이름이 특수 도구 목록에 있는지 확인
        
        Args:
            name: 도구 이름
            
        Returns:
            bool: 특수 도구 여부
        """
        return name.lower() in [n.lower() for n in self.special_tool_names]

    async def cleanup(self):
        """에이전트의 도구가 사용한 자원 정리
        
        사용된 모든 도구의 정리 함수를 호출합니다.
        """
        logger.info(f"🧹 에이전트 '{self.name}'의 자원 정리 중...")
        
        if not self.available_tools or not self.available_tools.tool_map:
            return
            
        for tool_name, tool_instance in self.available_tools.tool_map.items():
            if hasattr(tool_instance, "cleanup") and asyncio.iscoroutinefunction(
                tool_instance.cleanup
            ):
                try:
                    logger.debug(f"🧼 도구 정리 중: {tool_name}")
                    await tool_instance.cleanup()
                except Exception as e:
                    logger.error(
                        f"🚨 도구 '{tool_name}' 정리 중 오류 발생: {e}", exc_info=True
                    )
        logger.info(f"✨ 에이전트 '{self.name}' 정리 완료.")

    async def run(self, request: Optional[str] = None) -> str:
        """자원 정리와 함께 에이전트 실행
        
        Args:
            request: 초기 사용자 요청
            
        Returns:
            str: 실행 결과
        """
        try:
            return await super().run(request)
        finally:
            await self.cleanup()