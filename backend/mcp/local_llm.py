"""
로컬 LLM 연동 모듈

이 모듈은 로컬에서 실행되는 LLM(Large Language Model)과 MCP(Model Control Panel)를 
연동하기 위한 기능을 제공합니다.
"""

import aiohttp
import logging
import json
import os
from typing import Dict, Any, List, Optional, Union
import asyncio
from datetime import datetime

logger = logging.getLogger("mcp.local_llm")

class LocalLLMTool:
    """로컬 LLM 연동을 위한 클래스"""

    def __init__(self):
        self.active_sessions = {}
        self.cache = {}

    async def initialize_session(self, config: Dict[str, Any]) -> str:
        """로컬 LLM 세션 초기화

        Args:
            config: LLM 구성 정보 (baseUrl, apiKey, model 등)

        Returns:
            str: 세션 ID
        """
        session_id = f"llm-{datetime.now().timestamp()}"
        
        # 구성 저장
        self.active_sessions[session_id] = {
            "config": config,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": datetime.utcnow().isoformat(),
            "history": [],
        }
        
        # 연결 테스트
        try:
            test_result = await self.test_connection(session_id)
            if not test_result.get("success", False):
                logger.warning(f"LLM connection test failed: {test_result.get('error')}")
                self.active_sessions[session_id]["status"] = "error"
                self.active_sessions[session_id]["error"] = test_result.get("error")
            else:
                self.active_sessions[session_id]["status"] = "ready"
                logger.info(f"LLM session {session_id} initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLM session: {str(e)}")
            self.active_sessions[session_id]["status"] = "error"
            self.active_sessions[session_id]["error"] = str(e)
        
        return session_id

    async def test_connection(self, session_id: str) -> Dict[str, Any]:
        """LLM 연결 테스트

        Args:
            session_id: 세션 ID

        Returns:
            Dict[str, Any]: 테스트 결과
        """
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = self.active_sessions[session_id]
        config = session["config"]
        
        # 구성에서 필요한 정보 추출
        base_url = config.get("baseUrl", "http://localhost:1234/v1")
        if not base_url.endswith('/v1'):
            base_url = f"{base_url.rstrip('/')}/v1"
            
        api_key = config.get("apiKey", "")
        model = config.get("model", "local-model")
        
        # 간단한 테스트 요청
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        test_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, are you working?"}
            ],
            "max_tokens": 10
        }
        
        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    f"{base_url}/chat/completions", 
                    json=test_data,
                    headers=headers,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "model": result.get("model", model),
                            "response": result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM API error: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status} - {error_text}"
                        }
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {str(e)}")
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }
        except asyncio.TimeoutError:
            logger.error("LLM API request timed out")
            return {
                "success": False,
                "error": "Request timed out"
            }
        except Exception as e:
            logger.error(f"Unexpected error testing LLM connection: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    async def generate_completion(
        self, 
        session_id: str, 
        prompt: Union[str, List[Dict[str, Any]]],
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """LLM에 완성 요청

        Args:
            session_id: 세션 ID
            prompt: 프롬프트 (문자열 또는 메시지 목록)
            options: 생성 옵션 (온도, 최대 토큰 수 등)

        Returns:
            Dict[str, Any]: 생성 결과
        """
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = self.active_sessions[session_id]
        config = session["config"]
        
        # 구성에서 필요한 정보 추출
        base_url = config.get("baseUrl", "http://localhost:1234/v1")
        if not base_url.endswith('/v1'):
            base_url = f"{base_url.rstrip('/')}/v1"
            
        api_key = config.get("apiKey", "")
        model = config.get("model", "local-model")
        
        # 기본 옵션 설정
        if options is None:
            options = {}
        
        # 요청 데이터 준비
        if isinstance(prompt, str):
            # 문자열 프롬프트를 메시지 형식으로 변환
            messages = [
                {"role": "user", "content": prompt}
            ]
            endpoint = f"{base_url}/chat/completions"
        else:
            # 이미 메시지 형식인 경우
            messages = prompt
            endpoint = f"{base_url}/chat/completions"
        
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": options.get("max_tokens", 1024),
            "temperature": options.get("temperature", 0.7),
            "stream": options.get("stream", False),
        }
        
        # 추가 옵션 설정
        for key, value in options.items():
            if key not in ["max_tokens", "temperature", "stream"]:
                request_data[key] = value
        
        # 헤더 설정
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 요청 보내기
        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    endpoint,
                    json=request_data,
                    headers=headers,
                    timeout=60  # 긴 응답을 위해 타임아웃 증가
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 응답 정리
                        if "choices" in result and len(result["choices"]) > 0:
                            content = result["choices"][0].get("message", {}).get("content", "")
                            finish_reason = result["choices"][0].get("finish_reason", "")
                            
                            # 히스토리에 저장
                            history_entry = {
                                "timestamp": datetime.utcnow().isoformat(),
                                "prompt": prompt,
                                "response": content,
                                "finish_reason": finish_reason,
                                "model": result.get("model", model),
                                "usage": result.get("usage", {})
                            }
                            session["history"].append(history_entry)
                            session["last_used"] = datetime.utcnow().isoformat()
                            
                            return {
                                "success": True,
                                "content": content,
                                "finish_reason": finish_reason,
                                "model": result.get("model", model),
                                "usage": result.get("usage", {}),
                                "raw_response": result
                            }
                        else:
                            logger.error(f"Unexpected LLM response format: {result}")
                            return {
                                "success": False,
                                "error": "Unexpected response format",
                                "raw_response": result
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM API error: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status} - {error_text}"
                        }
        except Exception as e:
            logger.error(f"Error generating LLM completion: {str(e)}")
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }

    async def generate_stream(
        self, 
        session_id: str, 
        prompt: Union[str, List[Dict[str, Any]]],
        options: Dict[str, Any] = None
    ):
        """LLM에 스트리밍 완성 요청 (제너레이터 반환)

        Args:
            session_id: 세션 ID
            prompt: 프롬프트 (문자열 또는 메시지 목록)
            options: 생성 옵션 (온도, 최대 토큰 수 등)

        Yields:
            Dict[str, Any]: 스트리밍 응답 청크
        """
        if session_id not in self.active_sessions:
            yield {
                "success": False,
                "error": f"Session {session_id} not found"
            }
            return
        
        session = self.active_sessions[session_id]
        config = session["config"]
        
        # 구성에서 필요한 정보 추출
        base_url = config.get("baseUrl", "http://localhost:1234/v1")
        if not base_url.endswith('/v1'):
            base_url = f"{base_url.rstrip('/')}/v1"
            
        api_key = config.get("apiKey", "")
        model = config.get("model", "local-model")
        
        # 기본 옵션 설정
        if options is None:
            options = {}
        
        # 요청 데이터 준비
        if isinstance(prompt, str):
            # 문자열 프롬프트를 메시지 형식으로 변환
            messages = [
                {"role": "user", "content": prompt}
            ]
            endpoint = f"{base_url}/chat/completions"
        else:
            # 이미 메시지 형식인 경우
            messages = prompt
            endpoint = f"{base_url}/chat/completions"
        
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": options.get("max_tokens", 1024),
            "temperature": options.get("temperature", 0.7),
            "stream": True,  # 스트리밍 항상 활성화
        }
        
        # 추가 옵션 설정
        for key, value in options.items():
            if key not in ["max_tokens", "temperature", "stream"]:
                request_data[key] = value
        
        # 헤더 설정
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 요청 보내기
        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    endpoint,
                    json=request_data,
                    headers=headers,
                    timeout=300  # 스트리밍을 위해 긴 타임아웃
                ) as response:
                    if response.status == 200:
                        accumulated_text = ""
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line:
                                if line.startswith('data: '):
                                    line = line[6:]  # 'data: ' 접두사 제거
                                    if line == '[DONE]':
                                        # 스트리밍 완료
                                        break
                                    
                                    try:
                                        data = json.loads(line)
                                        # 스트리밍 청크에서 텍스트 추출
                                        if 'choices' in data and len(data['choices']) > 0:
                                            if 'delta' in data['choices'][0]:
                                                delta = data['choices'][0]['delta']
                                                if 'content' in delta:
                                                    content = delta['content']
                                                    accumulated_text += content
                                                    yield {
                                                        "success": True,
                                                        "chunk": content,
                                                        "accumulated_text": accumulated_text,
                                                        "finish_reason": data['choices'][0].get('finish_reason'),
                                                        "model": data.get('model', model)
                                                    }
                                    except json.JSONDecodeError:
                                        logger.warning(f"Failed to parse streaming response: {line}")
                        
                        # 히스토리에 저장
                        history_entry = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "prompt": prompt,
                            "response": accumulated_text,
                            "model": model
                        }
                        session["history"].append(history_entry)
                        session["last_used"] = datetime.utcnow().isoformat()
                        
                        # 완료 메시지
                        yield {
                            "success": True,
                            "complete": True,
                            "accumulated_text": accumulated_text
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM API stream error: {response.status} - {error_text}")
                        yield {
                            "success": False,
                            "error": f"API error: {response.status} - {error_text}"
                        }
        except Exception as e:
            logger.error(f"Error in streaming LLM completion: {str(e)}")
            yield {
                "success": False,
                "error": f"Error: {str(e)}"
            }

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """세션 정보 조회

        Args:
            session_id: 세션 ID

        Returns:
            Dict[str, Any]: 세션 정보
        """
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = self.active_sessions[session_id]
        
        # 보안을 위해 API 키는 마스킹
        safe_config = session["config"].copy()
        if "apiKey" in safe_config:
            safe_config["apiKey"] = "****" if safe_config["apiKey"] else ""
        
        return {
            "success": True,
            "session_id": session_id,
            "created_at": session["created_at"],
            "last_used": session["last_used"],
            "status": session.get("status", "unknown"),
            "config": safe_config,
            "history_count": len(session["history"])
        }

    def list_sessions(self) -> Dict[str, Any]:
        """활성 세션 목록 조회
        
        Returns:
            Dict[str, Any]: 세션 목록
        """
        sessions = []
        for session_id, session in self.active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "created_at": session["created_at"],
                "last_used": session["last_used"],
                "status": session.get("status", "unknown"),
                "model": session["config"].get("model", "unknown"),
                "base_url": session["config"].get("baseUrl", "unknown")
            })
        
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }

    def get_session_history(self, session_id: str, count: int = None) -> Dict[str, Any]:
        """세션 히스토리 조회
        
        Args:
            session_id: 세션 ID
            count: 조회할 기록 수 (None이면 모두 조회)
            
        Returns:
            Dict[str, Any]: 세션 히스토리
        """
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = self.active_sessions[session_id]
        history = session["history"]
        
        if count is not None:
            history = history[-count:]
        
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }

    async def update_session_settings(self, session_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """세션 설정 업데이트
        
        Args:
            session_id: 세션 ID
            settings: 업데이트할 설정
            
        Returns:
            Dict[str, Any]: 업데이트 결과
        """
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = self.active_sessions[session_id]
        
        # 기존 config 복사 후 업데이트
        updated_config = session["config"].copy()
        
        # 시스템 프롬프트 업데이트
        if "system_prompt" in settings:
            # 현재는 config에 시스템 프롬프트를 직접 저장하지 않으므로 별도 저장
            session["system_prompt"] = settings["system_prompt"]
        
        # 온도 업데이트
        if "temperature" in settings:
            updated_config["temperature"] = settings["temperature"]
        
        # 최대 토큰 수 업데이트
        if "max_tokens" in settings:
            updated_config["max_tokens"] = settings["max_tokens"]
        
        # top_p 업데이트
        if "top_p" in settings:
            updated_config["top_p"] = settings["top_p"]
        
        # 기타 설정 업데이트
        for key, value in settings.items():
            if key not in ["system_prompt", "temperature", "max_tokens", "top_p"]:
                # 직접 config에 저장하지 않고 별도의 session 항목으로 저장
                session[key] = value
        
        # 설정 업데이트
        session["config"] = updated_config
        session["last_updated"] = datetime.utcnow().isoformat()
        
        logger.info(f"Session {session_id} settings updated")
        
        return {
            "success": True,
            "message": f"Session {session_id} settings updated",
            "updated_settings": settings
        }

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """세션 삭제
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Dict[str, Any]: 삭제 결과
        """
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        # 세션 삭제
        del self.active_sessions[session_id]
        
        return {
            "success": True,
            "message": f"Session {session_id} deleted"
        }
