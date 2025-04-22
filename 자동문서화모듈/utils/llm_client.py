"""
LLM API 클라이언트 (LM Studio 호출용)
"""

import json
import requests
from typing import Dict, List, Any, Optional

class LLMClient:
    """LLM API와 통신하기 위한 클라이언트 클래스"""
    
    def __init__(self, api_url: str, model_name: str):
        """
        LLM 클라이언트 초기화
        
        Args:
            api_url: API 서버 URL (예: http://127.0.0.1:1234)
            model_name: 사용할 모델 이름
        """
        self.api_url = api_url
        self.model_name = model_name
        
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       temperature: float = 0.7,
                       max_tokens: int = 2000) -> Optional[str]:
        """
        ChatCompletion API 호출
        
        Args:
            messages: 메시지 목록 [{"role": "user", "content": "..."}, ...]
            temperature: 생성 온도 (0.0 ~ 1.0)
            max_tokens: 최대 토큰 수
            
        Returns:
            LLM의 응답 텍스트. 실패 시 None
        """
        endpoint = f"{self.api_url}/v1/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return content
            return None
        except Exception as e:
            print(f"LLM API 호출 실패: {str(e)}")
            return None
    
    def extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        텍스트에서 JSON 부분을 추출
        
        Args:
            text: JSON이 포함된 텍스트
            
        Returns:
            파싱된 JSON 딕셔너리. 실패 시 None
        """
        try:
            # JSON 블록을 찾음 (중괄호로 둘러싸인 부분)
            json_text = ""
            in_json = False
            braces_count = 0
            
            for char in text:
                if char == '{':
                    in_json = True
                    braces_count += 1
                    json_text += char
                elif in_json:
                    json_text += char
                    if char == '{':
                        braces_count += 1
                    elif char == '}':
                        braces_count -= 1
                        if braces_count == 0:
                            break
            
            if json_text:
                return json.loads(json_text)
            
            # 전체 텍스트가 JSON인 경우 시도
            return json.loads(text)
        except Exception as e:
            print(f"JSON 추출 실패: {str(e)}")
            # 정규식을 사용한 대체 방법 구현 가능
            return None
