"""
MCP 서버와 Manus 에이전트 통합 모듈

Model Context Protocol(MCP) 서버와 Manus 에이전트를 연결하여 
실제 파일 시스템 도구 실행을 처리합니다.
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional

from .agent import ManusAgent
from .mcp_server import ManusMCPServer
from backend.models.enums import LLMType

logger = logging.getLogger(__name__)

class ManusAgentMCPIntegration:
    """
    Manus 에이전트와 MCP 서버 통합 클래스
    
    MCP 서버의 도구 호출을 LM Studio를 통해 처리하고,
    LM Studio의 도구 사용을 MCP 서버에 전달합니다.
    """
    
    def __init__(
        self,
        llm_type: LLMType = LLMType.LOCAL_LLM,
        llm_base_url: Optional[str] = None,
        model_id: Optional[str] = None
    ):
        """
        MCP-에이전트 통합 인스턴스 초기화
        
        Args:
            llm_type: LLM 유형 (기본값: LOCAL_LLM)
            llm_base_url: LLM API 서버 URL (기본값: None, 설정에서 가져옴)
            model_id: 사용할 모델 ID (기본값: None, 설정에서 가져옴)
        """
        self.agent = ManusAgent(llm_type=llm_type, llm_base_url=llm_base_url, model_id=model_id)
        self.mcp_server = ManusMCPServer()
        
        logger.info(f"Manus MCP 통합 초기화됨 - LLM 타입: {llm_type}, URL: {llm_base_url}, 모델 ID: {model_id}")
    
    async def process_query(self, query: str, with_tools: bool = True) -> Dict[str, Any]:
        """
        사용자 쿼리 처리
        
        Args:
            query: 사용자 질의 내용
            with_tools: 도구 사용 활성화 여부
            
        Returns:
            처리 결과 (응답 및 도구 호출 기록 포함)
        """
        try:
            logger.info(f"쿼리 처리 시작: '{query}'")
            
            # MCP 도구 목록 가져오기
            tools = None
            if with_tools:
                tools_result = self.mcp_server.list_tools()
                if tools_result and "tools" in tools_result:
                    tools = []
                    for tool in tools_result["tools"]:
                        # OpenAI/Claude 호환 도구 형식으로 변환
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description or "",
                                "parameters": tool.inputSchema
                            }
                        })
            
            # 에이전트로 쿼리 처리
            response, tool_calls = await self.agent.process_message(query, tools=tools)
            
            # 도구 호출 결과 기록 추가
            processed_tool_calls = []
            if tool_calls:
                for tc in tool_calls:
                    # 실제 MCP 서버에 도구 호출 요청
                    try:
                        result = self.mcp_server.call_tool(tc["name"], tc["arguments"])
                        
                        # 도구 호출 결과 텍스트 추출
                        result_text = ""
                        if "content" in result and result["content"]:
                            for content_item in result["content"]:
                                if content_item.get("type") == "text":
                                    result_text += content_item.get("text", "")
                        
                        processed_tool_calls.append({
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                            "result": result_text,
                            "success": not result.get("isError", False)
                        })
                    except Exception as e:
                        logger.error(f"도구 호출 오류 - {tc['name']}: {str(e)}")
                        processed_tool_calls.append({
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                            "result": f"오류: {str(e)}",
                            "success": False
                        })
            
            return {
                "response": response,
                "tool_calls": processed_tool_calls
            }
            
        except Exception as e:
            logger.error(f"쿼리 처리 오류: {str(e)}")
            return {
                "response": f"쿼리 처리 중 오류가 발생했습니다: {str(e)}",
                "tool_calls": [],
                "error": str(e)
            }
    
    async def process_file_operation(self, operation: str, path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        파일 작업 처리
        
        Args:
            operation: 작업 종류 ('read', 'write', 'list')
            path: 파일 경로
            content: 쓰기 작업시 파일 내용
            
        Returns:
            작업 결과
        """
        try:
            if operation == "read":
                result = self.mcp_server.call_tool("read_file", {"path": path})
                return {"success": True, "result": result}
            elif operation == "write":
                if content is None:
                    return {"success": False, "error": "파일 내용이 제공되지 않았습니다."}
                result = self.mcp_server.call_tool("write_file", {"path": path, "content": content})
                return {"success": True, "result": result}
            elif operation == "list":
                result = self.mcp_server.call_tool("list_directory", {"path": path})
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": f"지원되지 않는 작업: {operation}"}
        except Exception as e:
            logger.error(f"파일 작업 오류 - {operation} {path}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def set_model_id(self, model_id: str):
        """에이전트 모델 ID 설정"""
        self.agent.set_model_id(model_id)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """대화 기록 반환"""
        return self.agent.get_history()
    
    def clear_conversation_history(self):
        """대화 기록 초기화"""
        self.agent.clear_history()
