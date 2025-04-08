"""
LLM 응답 메시지 포맷팅 처리 모듈

LLM에서 생성된 응답을 특정 형식으로 변환하여 클라이언트에 전송하는 기능을 제공합니다.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger("mcp.message_formatter")

class MessageFormatter:
    """
    메시지 포맷팅 클래스
    
    LLM에서 생성된 응답을 특정 형식으로 변환하여 클라이언트에 전송합니다.
    """
    
    def __init__(self, websocket: WebSocket, llm_tool, message_id: str):
        """
        초기화
        
        Args:
            websocket (WebSocket): 웹소켓 연결
            llm_tool: LLM 도구 인스턴스
            message_id (str): 메시지 ID
        """
        self.websocket = websocket
        self.llm_tool = llm_tool
        self.message_id = message_id
        
    async def process_message(self, llm_session_id: str, messages: List[Dict[str, Any]], 
                             options: Dict[str, Any], tools: List[Dict[str, Any]]):
        """
        LLM 응답을 처리하고 클라이언트에 전송합니다.
        
        Args:
            llm_session_id (str): LLM 세션 ID
            messages (List[Dict[str, Any]]): 메시지 목록
            options (Dict[str, Any]): 옵션
            tools (List[Dict[str, Any]]): 도구 목록
        """
        try:
            # 옵션에 도구 설정 추가
            if tools:
                options["tools"] = tools
                options.setdefault("tool_choice", "auto")
            
            # 응답 시작 알림
            await self.websocket.send_json({
                "type": "chat_response_started",
                "message_id": self.message_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 응답 메시지 생성 알림 (빈 컨텐츠로 생성)
            await self.websocket.send_json({
                "type": "chat_response_create",
                "message_id": self.message_id,
                "content": "",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 전체 누적 텍스트
            full_response = ""
            last_update_time = asyncio.get_event_loop().time()
            paragraph_buffer = ""
            
            # 문장 구분자
            sentence_terminators = ['.', '!', '?', '\n\n', ':', ';']
            
            # 스트리밍 생성 시작
            async for chunk in self.llm_tool.generate_stream(llm_session_id, messages, options):
                if not chunk.get("success", False):
                    await self.websocket.send_json({
                        "type": "error",
                        "message": chunk.get("error", "Unknown error during generation"),
                        "message_id": self.message_id
                    })
                    return
                
                # 청크 처리
                if "chunk" in chunk:
                    chunk_text = chunk["chunk"]
                    full_response += chunk_text
                    paragraph_buffer += chunk_text
                    
                    now = asyncio.get_event_loop().time()
                    time_passed = now - last_update_time >= 0.5  # 0.5초 간격으로 업데이트
                    
                    # 문장 완료 여부 확인
                    sentence_complete = any(paragraph_buffer.endswith(term) for term in sentence_terminators)
                    buffer_large = len(paragraph_buffer) >= 100  # 충분히 큰 버퍼
                    
                    # 문장이 완료되었거나 일정 시간이 지났거나 버퍼가 충분히 크면 업데이트
                    if sentence_complete or time_passed or buffer_large:
                        # 전체 내용 업데이트
                        await self.websocket.send_json({
                            "type": "chat_response_update",
                            "message_id": self.message_id,
                            "content": full_response,  # 누적된 전체 텍스트 전송
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        # 버퍼 초기화 및 시간 업데이트
                        paragraph_buffer = ""
                        last_update_time = now
                        
                        # 짧은 지연
                        await asyncio.sleep(0.05)
                
                # 완료 처리
                if chunk.get("complete", False):
                    # 완료 메시지 전송
                    await self.websocket.send_json({
                        "type": "chat_response_complete",
                        "message_id": self.message_id,
                        "content": chunk.get("accumulated_text", full_response),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break
            
            # 도구 호출 감지
            await self._detect_tool_calls(full_response)
            
        except Exception as e:
            logger.exception(f"Error in message formatting: {str(e)}")
            await self.websocket.send_json({
                "type": "error",
                "message": f"Error generating response: {str(e)}",
                "message_id": self.message_id
            })
    
    async def _detect_tool_calls(self, content: str):
        """JSON 코드 블록에서 도구 호출 감지
        
        Args:
            content (str): 메시지 내용
        """
        if "```json" in content and "```" in content:
            import re
            json_blocks = re.findall(r"```json\s*\n(.*?)\n\s*```", content, re.DOTALL)
            if json_blocks:
                for json_block in json_blocks:
                    try:
                        tool_data = json.loads(json_block)
                        if isinstance(tool_data, dict) and "function" in tool_data and "name" in tool_data.get("function", {}):
                            await self.websocket.send_json({
                                "type": "tool_call_detected",
                                "message_id": self.message_id,
                                "tool_call": {
                                    "name": tool_data["function"]["name"],
                                    "arguments": tool_data["function"].get("arguments", {})
                                },
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    except json.JSONDecodeError:
                        pass

# 기존 스트리밍 방식으로 처리하는 함수
async def process_streaming(websocket: WebSocket, llm_tool, llm_session_id: str, 
                         messages: List[Dict[str, Any]], options: Dict[str, Any],
                         message_id: str, tools: List[Dict[str, Any]]):
    """
    스트리밍 방식으로 LLM 응답을 처리합니다.
    """
    try:
        result_content = ""
        
        # 옵션에 도구 설정 추가
        if tools:
            options["tools"] = tools
            options.setdefault("tool_choice", "auto")
        
        # 스트리밍 생성 시작
        chunks_buffer = []
        send_interval = 0.3  # 0.3초 간격으로 전송(더 길게 변경)
        last_send_time = asyncio.get_event_loop().time()
        sentence_ending_chars = ['.', '!', '?', '\n', ':', ';']  # 문장 종료 문자
        
        async for chunk in llm_tool.generate_stream(llm_session_id, messages, options):
            if not chunk.get("success", False):
                await websocket.send_json({
                    "type": "error",
                    "message": chunk.get("error", "Unknown error during generation"),
                    "message_id": message_id
                })
                return
                
            # 청크 처리
            if "chunk" in chunk:
                now = asyncio.get_event_loop().time()
                current_chunk = chunk["chunk"]
                chunks_buffer.append(current_chunk)
                result_content += current_chunk
                
                # 문장이 완성되었거나 일정 시간이 지났거나 버퍼가 충분히 차면 전송
                # 1. 문장 종료 문자 확인
                ends_with_sentence = any(current_chunk.endswith(char) for char in sentence_ending_chars)
                # 2. 시간 간격 확인
                time_interval_passed = now - last_send_time > send_interval
                # 3. 버퍼 크기 확인 (50자 이상으로 늘림)
                buffer_size_sufficient = len("".join(chunks_buffer)) >= 50
                
                if ends_with_sentence or time_interval_passed or buffer_size_sufficient:
                    combined_chunk = "".join(chunks_buffer)
                    # 너무 작은 청크는 보내지 않음 (문장 종료로 인한 경우 제외)
                    if len(combined_chunk) > 1 or ends_with_sentence:
                        await websocket.send_json({
                            "type": "chat_response_chunk",
                            "message_id": message_id,
                            "chunk": combined_chunk,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        chunks_buffer = []
                        last_send_time = now
                        # 전송 후 짧은 지연을 주어 클라이언트가 처리할 시간 확보
                        await asyncio.sleep(0.05)
            
            # 완료 메시지
            if chunk.get("complete", False):
                # 남은 청크 전송
                if chunks_buffer:
                    combined_chunk = "".join(chunks_buffer)
                    await websocket.send_json({
                        "type": "chat_response_chunk",
                        "message_id": message_id,
                        "chunk": combined_chunk,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # 완료 메시지 전송
                await websocket.send_json({
                    "type": "chat_response_complete",
                    "message_id": message_id,
                    "content": chunk.get("accumulated_text", result_content),
                    "timestamp": datetime.utcnow().isoformat()
                })
                break
        
        # 도구 호출 처리
        if "```json" in result_content and "```" in result_content:
            # JSON 코드 블록 추출
            import re
            json_blocks = re.findall(r"```json\s*\n(.*?)\n\s*```", result_content, re.DOTALL)
            if json_blocks:
                for json_block in json_blocks:
                    try:
                        tool_data = json.loads(json_block)
                        if isinstance(tool_data, dict) and "function" in tool_data and "name" in tool_data.get("function", {}):
                            await websocket.send_json({
                                "type": "tool_call_detected",
                                "message_id": message_id,
                                "tool_call": {
                                    "name": tool_data["function"]["name"],
                                    "arguments": tool_data["function"].get("arguments", {})
                                },
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    except json.JSONDecodeError:
                        pass
                    
    except Exception as e:
        logger.exception(f"Error in streaming process: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error generating response: {str(e)}",
            "message_id": message_id
        })
