"""
Local LLM 시스템 테스트

로컬 LLM 시스템의 기능을 테스트합니다.
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock

# 테스트 대상 모듈 임포트
import sys
import os
import json

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from local_llm.api import (
    ping, get_status, update_config, chat, 
    LocalLLMChatRequest, Message
)


class TestLocalLLM(unittest.TestCase):
    """로컬 LLM 시스템 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 비동기 이벤트 루프 설정
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """테스트 정리"""
        self.loop.close()
    
    def test_ping(self):
        """핑 기능 테스트"""
        # ping 함수 호출
        result = self.loop.run_until_complete(ping())
        
        # 결과 검증
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["message"], "pong")
    
    @patch('local_llm.api.httpx.AsyncClient')
    def test_get_status_connected(self, mock_client):
        """연결 상태 확인 테스트 - 연결됨"""
        # 모의 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "deepseek-r1-distill-qwen-7b", "name": "DeepSeek Model"}
            ]
        }
        
        # 비동기 컨텍스트 매니저 설정
        mock_async_client = MagicMock()
        mock_async_client.__aenter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_async_client
        
        # 함수 호출
        result = self.loop.run_until_complete(get_status())
        
        # 결과 검증
        self.assertTrue(result["enabled"])
        self.assertTrue(result["connected"])
        self.assertEqual(result["model_id"], "deepseek-r1-distill-qwen-7b")
    
    @patch('local_llm.api.httpx.AsyncClient')
    def test_get_status_disconnected(self, mock_client):
        """연결 상태 확인 테스트 - 연결 안됨"""
        # 예외 발생 설정
        mock_async_client = MagicMock()
        mock_async_client.__aenter__.return_value.get.side_effect = Exception("Connection refused")
        mock_client.return_value = mock_async_client
        
        # 함수 호출
        result = self.loop.run_until_complete(get_status())
        
        # 결과 검증
        self.assertTrue(result["enabled"])
        self.assertFalse(result["connected"])
        self.assertIsNotNone(result["error"])
    
    def test_update_config(self):
        """구성 업데이트 테스트"""
        # 새 구성 데이터
        config_update = {
            "enabled": True,
            "base_url": "http://localhost:8080",
            "model_id": "test-model",
            "temperature": 0.5,
            "max_tokens": 500
        }
        
        # 함수 호출
        result = self.loop.run_until_complete(update_config(config_update))
        
        # 결과 검증
        self.assertEqual(result["base_url"], "http://localhost:8080")
        self.assertEqual(result["model_id"], "test-model")
        self.assertEqual(result["temperature"], 0.5)
        self.assertEqual(result["max_tokens"], 500)
    
    @patch('local_llm.api.LLM.ask')
    def test_chat(self, mock_ask):
        """채팅 기능 테스트"""
        # 모의 응답 설정
        mock_ask.return_value = "This is a test response from the LLM."
        
        # 채팅 요청 데이터
        request = LocalLLMChatRequest(
            messages=[Message(role="user", content="Hello, LLM!")],
            temperature=0.7,
            max_tokens=1000
        )
        
        # 함수 호출
        result = self.loop.run_until_complete(chat(request))
        
        # 결과 검증
        self.assertEqual(result["content"], "This is a test response from the LLM.")
        self.assertIsNotNone(result["model_id"])
        
        # mock_ask가 올바른 인자로 호출되었는지 확인
        mock_ask.assert_called_once()
        args, kwargs = mock_ask.call_args
        self.assertEqual(kwargs["max_tokens"], 1000)
        self.assertEqual(kwargs["temperature"], 0.7)
        self.assertEqual(args[0][0].content, "Hello, LLM!")


if __name__ == '__main__':
    unittest.main()
