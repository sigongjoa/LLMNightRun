"""
로컬 LLM 연동 테스트 스크립트

이 스크립트는 로컬 LLM 서버와 MCP 통합을 테스트합니다.
"""

import requests
import json
import time
import sys
import argparse
import logging
from typing import Dict, Any, List, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_test")

# MCP API 기본 URL
MCP_BASE_URL = "http://localhost:8000/mcp/v1"

def create_llm_session(
    base_url: str = "http://localhost:1234/v1",
    api_key: str = "",
    model: str = "local-model"
) -> Dict[str, Any]:
    """LLM 세션 생성"""
    endpoint = f"{MCP_BASE_URL}/llm/sessions"
    
    data = {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "context_length": 4096,
        "additional_config": {
            "description": "로컬 LLM 테스트 세션"
        }
    }
    
    try:
        response = requests.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating LLM session: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return {"success": False, "error": str(e)}

def test_llm_connection(session_id: str) -> Dict[str, Any]:
    """LLM 연결 테스트"""
    endpoint = f"{MCP_BASE_URL}/llm/sessions/{session_id}/test"
    
    try:
        response = requests.post(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error testing LLM connection: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return {"success": False, "error": str(e)}

def generate_text(
    session_id: str,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """텍스트 생성"""
    endpoint = f"{MCP_BASE_URL}/llm/sessions/{session_id}/generate"
    
    data = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    try:
        response = requests.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating text: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return {"success": False, "error": str(e)}

def chat_completion(
    session_id: str,
    messages: List[Dict[str, Any]],
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """채팅 완성"""
    endpoint = f"{MCP_BASE_URL}/llm/sessions/{session_id}/chat"
    
    data = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    try:
        response = requests.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating chat completion: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return {"success": False, "error": str(e)}

def list_sessions() -> Dict[str, Any]:
    """LLM 세션 목록 조회"""
    endpoint = f"{MCP_BASE_URL}/llm/sessions"
    
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error listing LLM sessions: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return {"success": False, "error": str(e)}

def get_session(session_id: str) -> Dict[str, Any]:
    """LLM 세션 정보 조회"""
    endpoint = f"{MCP_BASE_URL}/llm/sessions/{session_id}"
    
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting LLM session: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return {"success": False, "error": str(e)}

def delete_session(session_id: str) -> Dict[str, Any]:
    """LLM 세션 삭제"""
    endpoint = f"{MCP_BASE_URL}/llm/sessions/{session_id}"
    
    try:
        response = requests.delete(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error deleting LLM session: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return {"success": False, "error": str(e)}

def run_full_test(base_url: str, api_key: str, model: str):
    """전체 테스트 실행"""
    # 1. 세션 생성
    logger.info(f"Creating LLM session with base_url={base_url}, model={model}")
    session_result = create_llm_session(base_url, api_key, model)
    
    if not session_result.get("success", False):
        logger.error("Failed to create LLM session")
        return
    
    session_id = session_result.get("session_id")
    logger.info(f"Created LLM session: {session_id}")
    
    # 2. 연결 테스트
    logger.info("Testing LLM connection...")
    test_result = test_llm_connection(session_id)
    
    if not test_result.get("success", False):
        logger.error("Failed to connect to LLM")
        return
    
    logger.info("LLM connection test successful!")
    
    # 3. 텍스트 생성 테스트
    logger.info("Testing text generation...")
    generate_result = generate_text(
        session_id, 
        "Hello, I'm testing the LLM integration with LLMNightRun. Please tell me about MCP (Model Control Panel).",
        max_tokens=500,
        temperature=0.7
    )
    
    if not generate_result.get("success", False):
        logger.error("Failed to generate text")
        return
    
    logger.info(f"Generated text: {generate_result.get('content')}")
    
    # 4. 채팅 완성 테스트
    logger.info("Testing chat completion...")
    chat_result = chat_completion(
        session_id,
        [
            {"role": "system", "content": "You are a helpful assistant that provides concise responses."},
            {"role": "user", "content": "What is MCP in LLMNightRun? Keep it brief."}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    if not chat_result.get("success", False):
        logger.error("Failed to generate chat completion")
        return
    
    logger.info(f"Chat completion: {chat_result.get('content')}")
    
    # 5. 세션 목록 조회
    logger.info("Listing LLM sessions...")
    list_result = list_sessions()
    
    if not list_result.get("success", False):
        logger.error("Failed to list LLM sessions")
    else:
        logger.info(f"Found {list_result.get('count', 0)} active sessions")
    
    # 6. 세션 정보 조회
    logger.info(f"Getting session info for {session_id}...")
    session_info = get_session(session_id)
    
    if not session_info.get("success", False):
        logger.error("Failed to get session info")
    else:
        logger.info(f"Session info: {json.dumps(session_info, indent=2)}")
    
    # 7. 세션 삭제 (선택적)
    if input("Delete session? (y/n): ").lower() == "y":
        logger.info(f"Deleting session {session_id}...")
        delete_result = delete_session(session_id)
        
        if not delete_result.get("success", False):
            logger.error("Failed to delete session")
        else:
            logger.info("Session deleted successfully")
    
    logger.info("Test completed!")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="로컬 LLM 연동 테스트")
    
    parser.add_argument("--url", type=str, default="http://localhost:1234/v1",
                        help="LLM API 기본 URL (기본값: http://localhost:1234/v1)")
    parser.add_argument("--api-key", type=str, default="",
                        help="LLM API 키 (옵션)")
    parser.add_argument("--model", type=str, default="local-model",
                        help="사용할 모델 이름 (기본값: local-model)")
    parser.add_argument("--session-id", type=str,
                        help="기존 세션 ID (지정하면 새 세션을 만들지 않음)")
    parser.add_argument("--action", type=str, choices=["test", "generate", "chat", "list", "get", "delete"],
                        help="수행할 특정 작업 (미지정 시 전체 테스트 실행)")
    parser.add_argument("--prompt", type=str,
                        help="생성에 사용할 프롬프트")
    
    args = parser.parse_args()
    
    # 특정 작업 수행
    if args.action:
        if args.action == "list":
            result = list_sessions()
            print(json.dumps(result, indent=2))
            return
        
        # 세션 ID가 필요한 작업
        if not args.session_id:
            logger.error("--session-id 인수가 필요합니다")
            return
        
        if args.action == "test":
            result = test_llm_connection(args.session_id)
            print(json.dumps(result, indent=2))
        elif args.action == "generate":
            if not args.prompt:
                logger.error("--prompt 인수가 필요합니다")
                return
            result = generate_text(args.session_id, args.prompt)
            print(json.dumps(result, indent=2))
        elif args.action == "chat":
            if not args.prompt:
                logger.error("--prompt 인수가 필요합니다")
                return
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": args.prompt}
            ]
            result = chat_completion(args.session_id, messages)
            print(json.dumps(result, indent=2))
        elif args.action == "get":
            result = get_session(args.session_id)
            print(json.dumps(result, indent=2))
        elif args.action == "delete":
            result = delete_session(args.session_id)
            print(json.dumps(result, indent=2))
    else:
        # 전체 테스트 실행
        if args.session_id:
            logger.info(f"Using existing session: {args.session_id}")
            # 간단한 연결 테스트만 수행
            test_result = test_llm_connection(args.session_id)
            print(json.dumps(test_result, indent=2))
        else:
            # 전체 테스트 실행
            run_full_test(args.url, args.api_key, args.model)

if __name__ == "__main__":
    main()
