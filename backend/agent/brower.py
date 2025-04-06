"""
LLMNightRun 브라우저 에이전트 모듈

웹 브라우저 자동화를 수행하는 에이전트를 정의합니다.
"""

import asyncio
import base64
from typing import List, Optional, Dict, Any
import os

from pydantic import Field

from backend.agent.base import BaseAgent
from backend.models.enums import AgentState
from backend.models.agent import Message, ToolResult
from backend.logger import get_logger
from backend.config import settings

logger = get_logger(__name__)


class BrowserAgent(BaseAgent):
    """브라우저 에이전트
    
    웹 브라우저 자동화를 수행하는 에이전트입니다.
    웹사이트 방문, 스크린샷 촬영, 정보 추출 등의 작업을 수행합니다.
    """
    
    name: str = "browser"
    description: str = "웹 브라우저 자동화 에이전트"
    
    system_prompt: str = """당신은 웹 브라우저 자동화 에이전트입니다.
웹사이트를 방문하고, 정보를 수집하고, 작업을 수행할 수 있습니다.
웹 페이지의 내용을 분석하고 사용자의 요청에 따라 적절한 행동을 취하세요."""
    
    url: str = Field(default="")
    screenshot_base64: Optional[str] = None
    cookies: Dict[str, str] = Field(default_factory=dict)
    
    async def step(self) -> str:
        """단일 단계 실행
        
        Returns:
            str: 실행 결과
        """
        if not self.messages or len(self.messages) == 0:
            return "사용자 메시지가 없습니다."
        
        # 마지막 메시지 확인
        user_msg = self.messages[-1] if self.messages[-1].role == "user" else None
        if not user_msg:
            return "마지막 메시지가 사용자 메시지가 아닙니다."
        
        content = user_msg.content or ""
        
        # 브라우저 작업 수행
        try:
            # LLM에 질문하여 무엇을 할지 결정
            response = await self.llm.ask(
                messages=self.messages,
                system_msgs=[Message.system_message(self.system_prompt)] if self.system_prompt else None
            )
            
            # 응답 저장
            self.memory.add_message(Message.assistant_message(response))
            
            # URL 탐지 및 처리
            if "http://" in content or "https://" in content or "visit" in content.lower() or "go to" in content.lower():
                # URL 추출
                import re
                urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', content)
                
                if urls:
                    self.url = urls[0]
                    result = await self._visit_url(self.url)
                    # 스크린샷이 있으면 메시지에 추가
                    if result.base64_image:
                        self.screenshot_base64 = result.base64_image
                        self.memory.add_message(
                            Message.assistant_message(f"URL 방문 결과: {result.output}")
                        )
                        return f"URL '{self.url}' 방문 완료. 스크린샷이 첨부되었습니다."
                    return f"URL '{self.url}' 방문 완료: {result.output}"
            
            return response
        except Exception as e:
            logger.error(f"브라우저 단계 실행 중 오류 발생: {e}")
            self.state = AgentState.ERROR
            return f"오류: {str(e)}"
    
    async def _visit_url(self, url: str) -> ToolResult:
        """URL 방문
        
        Args:
            url: 방문할 URL
            
        Returns:
            ToolResult: 방문 결과
        """
        try:
            # 이 부분은 실제 브라우저 자동화 라이브러리를 사용해야 합니다.
            # 여기서는 모의 구현만 제공합니다.
            
            # 모의 결과
            return ToolResult(
                output=f"URL '{url}'에 성공적으로 접속했습니다.",
                # 모의 스크린샷 생성 (실제로는 브라우저에서 촬영한 스크린샷을 사용해야 함)
                base64_image=self._generate_mock_screenshot()
            )
        except Exception as e:
            logger.error(f"URL 방문 중 오류 발생: {e}")
            return ToolResult(
                output="",
                error=f"URL 방문 중 오류 발생: {str(e)}"
            )
    
    def _generate_mock_screenshot(self) -> str:
        """모의 스크린샷 생성 (실제 구현에서는 사용하지 않음)
        
        Returns:
            str: Base64로 인코딩된 이미지
        """
        # 실제 구현에서는 브라우저의 스크린샷을 사용해야 합니다.
        # 이 함수는 임시 구현입니다.
        mock_image_path = os.path.join(settings.base_dir, "static", "mock_screenshot.png")
        if os.path.exists(mock_image_path):
            with open(mock_image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        
        # 모의 이미지가 없는 경우 빈 문자열 반환
        return ""