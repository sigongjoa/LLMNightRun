"""
LLMNightRun MCP(Model Context Protocol) 에이전트 모듈

Model Context Protocol 서버와 상호 작용하는 에이전트를 정의합니다.
"""

import aiohttp
import logging
import json
import os
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from pydantic import Field

from backend.agent.base import BaseAgent
from backend.models.enums import AgentState
from backend.models.agent import Message, ToolResult
from backend.logger import get_logger

logger = get_logger(__name__)


class MCPAgent(BaseAgent):
    """MCP(Model Context Protocol) 에이전트
    
    Model Context Protocol 서버와 상호 작용하는 에이전트입니다.
    MCP 서버의 도구, 리소스, 프롬프트를 활용하여 다양한 작업을 수행합니다.
    """
    
    name: str = "mcp"
    description: str = "Model Context Protocol 에이전트"
    
    system_prompt: str = """당신은 Model Context Protocol(MCP) 서버와 상호 작용하는 에이전트입니다.
MCP 서버를 통해 파일 시스템, 데이터베이스, API 등 다양한 리소스와 도구에 접근할 수 있습니다.
사용자의 요청에 따라 적절한 MCP 서버의 도구와 리소스를 활용하여 작업을 수행하세요."""
    
    servers: Dict[str, Any] = Field(default_factory=dict)
    current_server: Optional[str] = Field(default=None)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._load_mcp_servers()
    
    def _load_mcp_servers(self):
        """설정에서 MCP 서버 로드"""
        try:
            config_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "config" / "mcp_config.json"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.servers = config.get("servers", {})
                    # 기본 서버 설정
                    if "default_server" in config and config["default_server"] in self.servers:
                        self.current_server = config["default_server"]
                    logger.info(f"MCP 서버 {len(self.servers)}개 로드됨")
                    if self.current_server:
                        logger.info(f"기본 MCP 서버 '{self.current_server}' 선택됨")
            else:
                logger.warning(f"MCP 설정 파일을 찾을 수 없음: {config_path}")
        except Exception as e:
            logger.error(f"MCP 서버 로드 중 오류: {e}")
    
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
            # 서버 선택 명령 확인
            if content.lower().startswith("서버 선택:") or content.lower().startswith("select server:"):
                server_name = content.split(":", 1)[1].strip()
                return await self._select_server(server_name)
            
            # 이용 가능한 서버 목록 요청 확인
            if "서버 목록" in content.lower() or "list servers" in content.lower():
                return self._list_servers()
            
            # 이용 가능한 리소스 목록 요청 확인
            if "리소스 목록" in content.lower() or "list resources" in content.lower():
                return await self._list_resources()
            
            # 이용 가능한 도구 목록 요청 확인
            if "도구 목록" in content.lower() or "list tools" in content.lower():
                return await self._list_tools()
            
            # 도구 호출 확인
            if "도구 호출:" in content.lower() or "call tool:" in content.lower():
                tool_call = content.split(":", 1)[1].strip()
                return await self._call_tool(tool_call)
                
            # LM Studio 직접 쿼리 (기본 동작)
            if self.current_server:
                # 채팅 메시지 형식으로 변환
                formatted_messages = []
                # 시스템 메시지 추가
                if self.system_prompt:
                    formatted_messages.append({
                        "role": "system",
                        "content": self.system_prompt
                    })
                
                # 대화 기록 추가
                for msg in self.messages:
                    if msg.role in ["user", "assistant", "system"]:
                        formatted_message = {
                            "role": msg.role,
                            "content": msg.content or ""
                        }
                        formatted_messages.append(formatted_message)
                
                # LM Studio에 직접 요청
                response = await self._communicate_with_lmstudio(formatted_messages)
                
                # 응답 저장
                self.memory.add_message(Message.assistant_message(response))
                return response
            else:
                # LLM에 질문하여 무엇을 할지 결정 (서버가 선택되지 않은 경우)
                response = await self.llm.ask(
                    messages=self.messages,
                    system_msgs=[Message.system_message(self.system_prompt)] if self.system_prompt else None
                )
                
                # 응답 저장
                self.memory.add_message(Message.assistant_message(response))
                return response
                
        except Exception as e:
            logger.error(f"MCP 단계 실행 중 오류 발생: {e}")
            self.state = AgentState.error
            return f"오류: {str(e)}"
    
    async def _communicate_with_lmstudio(self, messages: List[Dict[str, Any]]) -> str:
        """
        LM Studio API와 통신하여 응답을 받습니다.
        
        Args:
            messages: 메시지 목록
            
        Returns:
            str: LLM 응답
        """
        if not self.current_server or self.current_server not in self.servers:
            return "서버가 선택되지 않았거나 유효하지 않습니다."
        
        server = self.servers[self.current_server]
        base_url = server.get("base_url", "http://localhost:1234/v1")
        api_key = server.get("api_key", "")
        model = server.get("model", "local-model")
        
        # API 요청 준비
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        logger.info(f"LM Studio에 요청 전송: {base_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("LM Studio로부터 응답 수신 성공")
                        # 응답 처리
                        if "choices" in result and len(result["choices"]) > 0:
                            content = result["choices"][0]["message"]["content"]
                            return content
                        else:
                            return "응답을 처리하는 중 오류가 발생했습니다."
                    else:
                        error_text = await response.text()
                        logger.error(f"LM Studio API 오류: {response.status} - {error_text}")
                        return f"API 오류: {response.status} - {error_text[:100]}"
        except Exception as e:
            logger.error(f"LM Studio 통신 중 오류: {e}")
            return f"통신 오류: {str(e)}"
    
    async def _select_server(self, server_name: str) -> str:
        """MCP 서버 선택
        
        Args:
            server_name: 선택할 서버 이름
            
        Returns:
            str: 결과 메시지
        """
        if server_name in self.servers:
            self.current_server = server_name
            return f"'{server_name}' 서버가 선택되었습니다."
        else:
            return f"'{server_name}' 서버를 찾을 수 없습니다. 사용 가능한 서버: {', '.join(self.servers.keys())}"
    
    def _list_servers(self) -> str:
        """사용 가능한 MCP 서버 목록 반환
        
        Returns:
            str: 서버 목록
        """
        if not self.servers:
            return "등록된 MCP 서버가 없습니다."
        
        result = "사용 가능한 MCP 서버 목록:\n\n"
        for name, server in self.servers.items():
            status = "활성" if server.get("status") == "active" else "비활성"
            description = server.get("description", "설명 없음")
            result += f"- **{name}**: {description} [{status}]\n"
        
        result += f"\n현재 선택된 서버: {self.current_server or '없음'}"
        return result
    
    async def _list_resources(self) -> str:
        """현재 선택된 서버의 리소스 목록 반환
        
        Returns:
            str: 리소스 목록
        """
        if not self.current_server:
            return "먼저 MCP 서버를 선택해주세요. 예: '서버 선택: 서버이름'"
        
        # 실제로는 여기서 MCP API를 통해 리소스 목록을 가져와야 함
        # 여기서는 모의 구현만 제공
        resources = [
            {"name": "파일 시스템", "uri": "file://workspace", "description": "작업 공간 파일 접근"},
            {"name": "데이터베이스", "uri": "db://main", "description": "기본 데이터베이스 접근"},
            {"name": "API", "uri": "api://github", "description": "GitHub API 접근"}
        ]
        
        result = f"'{self.current_server}' 서버의 리소스 목록:\n\n"
        for res in resources:
            result += f"- **{res['name']}** ({res['uri']}): {res['description']}\n"
        
        return result
    
    async def _list_tools(self) -> str:
        """현재 선택된 서버의 도구 목록 반환
        
        Returns:
            str: 도구 목록
        """
        if not self.current_server:
            return "먼저 MCP 서버를 선택해주세요. 예: '서버 선택: 서버이름'"
        
        # 실제로는 여기서 MCP API를 통해 도구 목록을 가져와야 함
        # 여기서는 구성에서 도구를 가져오거나 기본값 제공
        tools = self.servers[self.current_server].get("tools", [
            "read_file", "write_file", "list_directory", "execute_query"
        ])
        
        tool_descriptions = {
            "read_file": "파일 내용 읽기",
            "write_file": "파일에 내용 쓰기",
            "list_directory": "디렉토리 내용 나열",
            "execute_query": "데이터베이스 쿼리 실행"
        }
        
        result = f"'{self.current_server}' 서버의 도구 목록:\n\n"
        for tool_name in tools:
            description = tool_descriptions.get(tool_name, "설명 없음")
            result += f"- **{tool_name}**: {description}\n"
        
        return result
    
    async def _call_tool(self, tool_call: str) -> str:
        """도구 호출
        
        Args:
            tool_call: 도구 호출 문자열 (JSON 형식)
            
        Returns:
            str: 호출 결과
        """
        if not self.current_server:
            return "먼저 MCP 서버를 선택해주세요. 예: '서버 선택: 서버이름'"
        
        try:
            # 도구 호출 파싱 시도
            tool_data = json.loads(tool_call)
            tool_name = tool_data.get("name")
            arguments = tool_data.get("arguments", {})
            
            if not tool_name:
                return "도구 이름을 지정해주세요. 예: '{\"name\": \"read_file\", \"arguments\": {\"path\": \"example.txt\"}}'"
            
            # 실제로는 여기서 MCP API를 통해 도구를 호출해야 함
            # 여기서는 모의 구현만 제공
            if tool_name == "read_file":
                path = arguments.get("path", "")
                if not path:
                    return "파일 경로를 지정해주세요."
                return f"'{path}' 파일 내용:\n\n```\n예시 파일 내용입니다.\n```"
            
            elif tool_name == "write_file":
                path = arguments.get("path", "")
                content = arguments.get("content", "")
                if not path or not content:
                    return "파일 경로와 내용을 모두 지정해주세요."
                return f"'{path}' 파일에 내용이 성공적으로 저장되었습니다."
            
            elif tool_name == "list_directory":
                path = arguments.get("path", "")
                if not path:
                    return "디렉토리 경로를 지정해주세요."
                return f"'{path}' 디렉토리 내용:\n- file1.txt\n- file2.json\n- subfolder/"
            
            elif tool_name == "execute_query":
                query = arguments.get("query", "")
                if not query:
                    return "SQL 쿼리를 지정해주세요."
                return f"쿼리 실행 결과:\n\n```\n[{{'id': 1, 'name': 'example'}}]\n```"
            
            return f"알 수 없는 도구: {tool_name}"
        except json.JSONDecodeError:
            return "잘못된 도구 호출 형식입니다. JSON 형식으로 지정해주세요. 예: '{\"name\": \"read_file\", \"arguments\": {\"path\": \"example.txt\"}}'"
        except Exception as e:
            logger.error(f"도구 호출 중 오류: {e}")
            return f"도구 호출 중 오류가 발생했습니다: {str(e)}"
