import os
import openai
import requests
import json
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.models import LLMType
from backend.database.operations import get_settings
from backend.database.connection import SessionLocal

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 설정 가져오기
def get_api_keys():
    """데이터베이스에서 API 키를 가져옵니다."""
    db = SessionLocal()
    try:
        settings = get_settings(db)
        if settings:
            return {
                "openai_api_key": settings.openai_api_key,
                "claude_api_key": settings.claude_api_key
            }
        return {}
    finally:
        db.close()

def get_llm_response(llm_type: LLMType, prompt: str) -> str:
    """
    지정된 LLM에 프롬프트를 전송하고 응답을 받아옵니다.
    
    Args:
        llm_type: LLM 유형
        prompt: 질문 내용
        
    Returns:
        LLM의 응답 텍스트
    """
    if llm_type == LLMType.OPENAI_API:
        return get_openai_response(prompt)
    elif llm_type == LLMType.CLAUDE_API:
        return get_claude_response(prompt)
    else:
        raise ValueError(f"API를 통한 요청이 지원되지 않는 LLM 유형입니다: {llm_type}")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_openai_response(prompt: str) -> str:
    """
    OpenAI API를 사용하여 응답을 가져옵니다.
    
    Args:
        prompt: 질문 내용
        
    Returns:
        OpenAI의 응답 텍스트
    """
    # API 키 가져오기
    api_keys = get_api_keys()
    api_key = api_keys.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
    
    openai.api_key = api_key
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # 또는 다른 모델 (gpt-3.5-turbo 등)
            messages=[
                {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API 호출 중 오류 발생: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_claude_response(prompt: str) -> str:
    """
    Claude API를 사용하여 응답을 가져옵니다.
    
    Args:
        prompt: 질문 내용
        
    Returns:
        Claude의 응답 텍스트
    """
    # API 키 가져오기
    api_keys = get_api_keys()
    api_key = api_keys.get("claude_api_key") or os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise ValueError("Claude API 키가 설정되지 않았습니다.")
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": "claude-2",  # 또는 다른 모델
        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
        "max_tokens_to_sample": 1500,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/complete",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logger.error(f"Claude API 오류: {response.status_code}, {response.text}")
            raise Exception(f"Claude API 호출 실패: {response.status_code}")
        
        result = response.json()
        return result.get("completion", "").strip()
    except Exception as e:
        logger.error(f"Claude API 호출 중 오류 발생: {str(e)}")
        raise

# 추가 LLM 통합을 위한 함수
def get_custom_llm_response(
    prompt: str, 
    api_url: str, 
    api_key: str, 
    headers: Optional[Dict[str, str]] = None,
    payload_template: Optional[Dict[str, Any]] = None
) -> str:
    """
    커스텀 LLM API를 호출하는 일반 함수
    
    Args:
        prompt: 질문 내용
        api_url: API 엔드포인트 URL
        api_key: API 키
        headers: 요청 헤더 (선택 사항)
        payload_template: 요청 본문 템플릿 (선택 사항)
        
    Returns:
        LLM의 응답 텍스트
    """
    if not headers:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    if not payload_template:
        payload_template = {
            "prompt": prompt,
            "max_tokens": 1500,
            "temperature": 0.7
        }
    else:
        # 프롬프트를 템플릿에 삽입
        for key, value in payload_template.items():
            if isinstance(value, str) and "{prompt}" in value:
                payload_template[key] = value.format(prompt=prompt)
    
    try:
        response = requests.post(api_url, headers=headers, json=payload_template)
        
        if response.status_code != 200:
            logger.error(f"API 오류: {response.status_code}, {response.text}")
            raise Exception(f"API 호출 실패: {response.status_code}")
        
        result = response.json()
        
        # 응답 구조에 따라 결과 추출 방법 커스터마이징 필요
        if "text" in result:
            return result["text"]
        elif "output" in result:
            return result["output"]
        elif "content" in result:
            return result["content"]
        else:
            logger.warning(f"응답에서 결과를 추출할 수 없습니다: {result}")
            return json.dumps(result)
            
    except Exception as e:
        logger.error(f"API 호출 중 오류 발생: {str(e)}")
        raise