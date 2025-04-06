"""
LLMNightRun MCP(Multi-Cloud Platform) 에이전트 모듈

여러 클라우드 플랫폼과 상호 작용하는 에이전트를 정의합니다.
"""

from typing import List, Optional, Dict, Any, Union
import json

from pydantic import Field

from backend.agent.base import BaseAgent
from backend.models.enums import AgentState
from backend.models.agent import Message, ToolResult
from backend.logger import get_logger

logger = get_logger(__name__)


class MCPAgent(BaseAgent):
    """MCP(Multi-Cloud Platform) 에이전트
    
    여러 클라우드 플랫폼과 상호 작용하는 에이전트입니다.
    AWS, Azure, GCP 등의 클라우드 플랫폼에 접근하고 리소스를 관리합니다.
    """
    
    name: str = "mcp"
    description: str = "다중 클라우드 플랫폼 에이전트"
    
    system_prompt: str = """당신은 여러 클라우드 플랫폼과 상호 작용하는 에이전트입니다.
AWS, Azure, GCP와 같은 클라우드 플랫폼에 접근하고 리소스를 관리할 수 있습니다.
사용자의 요청에 따라 클라우드 리소스를 생성, 수정, 삭제하고 상태를 확인하세요."""
    
    platform: str = Field(default="")
    resources: Dict[str, Any] = Field(default_factory=dict)
    
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
        
        # MCP 작업 수행
        try:
            # LLM에 질문하여 무엇을 할지 결정
            response = await self.llm.ask(
                messages=self.messages,
                system_msgs=[Message.system_message(self.system_prompt)] if self.system_prompt else None
            )
            
            # 응답 저장
            self.memory.add_message(Message.assistant_message(response))
            
            # 플랫폼 명시적 언급 확인
            platforms = ["aws", "azure", "gcp", "alibaba"]
            for platform in platforms:
                if platform.lower() in content.lower():
                    self.platform = platform
                    break
            
            # 리소스 작업 감지
            operations = ["create", "update", "delete", "list", "get", "describe"]
            for operation in operations:
                if operation.lower() in content.lower():
                    result = await self._process_resource_operation(operation, content)
                    return f"리소스 작업 결과: {result}"
            
            return response
        except Exception as e:
            logger.error(f"MCP 단계 실행 중 오류 발생: {e}")
            self.state = AgentState.ERROR
            return f"오류: {str(e)}"
    
    async def _process_resource_operation(
        self, operation: str, content: str
    ) -> str:
        """리소스 작업 처리
        
        Args:
            operation: 작업 유형 (create, update, delete 등)
            content: 사용자 요청 내용
            
        Returns:
            str: 작업 결과
        """
        # 이 부분은 실제 클라우드 API를 호출해야 합니다.
        # 여기서는 모의 구현만 제공합니다.
        
        if not self.platform:
            return "작업할 클라우드 플랫폼을 지정해주세요."
        
        if operation == "create":
            resource_id = f"res-{len(self.resources) + 1}"
            self.resources[resource_id] = {
                "platform": self.platform,
                "type": "instance",  # 실제로는 요청에서 추출해야 함
                "status": "creating"
            }
            return f"리소스 '{resource_id}'를 {self.platform}에 생성 중입니다."
        
        elif operation == "list":
            if not self.resources:
                return f"{self.platform}에 생성된 리소스가 없습니다."
            
            resources_list = json.dumps(self.resources, indent=2)
            return f"{self.platform} 리소스 목록:\n{resources_list}"
        
        elif operation == "delete":
            # 실제로는 요청에서 리소스 ID를 추출해야 함
            if not self.resources:
                return f"{self.platform}에 삭제할 리소스가 없습니다."
            
            resource_id = list(self.resources.keys())[0]
            del self.resources[resource_id]
            return f"리소스 '{resource_id}'를 {self.platform}에서 삭제했습니다."
        
        return f"{self.platform}에서 '{operation}' 작업을 수행했습니다."