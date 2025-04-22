"""
대화 로그 분석 유틸리티
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.llm_client import LLMClient

class ConversationAnalyzer:
    """대화 내용 분석 및 처리를 위한 클래스"""
    
    def __init__(self, llm_client: LLMClient):
        """
        ConversationAnalyzer 초기화
        
        Args:
            llm_client: LLM API 클라이언트 인스턴스
        """
        self.llm_client = llm_client
        
    def load_conversation(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        대화 로그 파일 로드
        
        Args:
            file_path: 대화 로그 JSON 파일 경로
            
        Returns:
            대화 내용을 담은 딕셔너리. 실패 시 None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"대화 로그 로드 실패: {str(e)}")
            return None
    
    def get_conversation_text(self, conversation: Dict[str, Any]) -> str:
        """
        대화 로그를 텍스트로 변환
        
        Args:
            conversation: 대화 내용 딕셔너리
            
        Returns:
            대화 내용을 텍스트로 변환한 결과
        """
        if "logs" not in conversation:
            return ""
            
        logs = conversation["logs"]
        text_parts = []
        
        for log in logs:
            role = log.get("role", "")
            content = log.get("content", "")
            
            if role and content:
                text_parts.append(f"{role.capitalize()}: {content}")
                
        return "\n\n".join(text_parts)
    
    def extract_intent(self, conversation: Dict[str, Any], intent_prompt: str) -> Dict[str, Any]:
        """
        대화 내용에서 의도 추출
        
        Args:
            conversation: 대화 내용 딕셔너리
            intent_prompt: 의도 추출을 위한 프롬프트 템플릿
            
        Returns:
            추출된 의도 정보 (keywords, intent, doc_type)
        """
        conversation_text = self.get_conversation_text(conversation)
        
        # 기본값 설정
        result = {
            "keywords": [],
            "intent": "문서 생성",
            "doc_type": "README"
        }
        
        if not conversation_text:
            return result
            
        # 프롬프트 생성 및 LLM 호출
        prompt = intent_prompt.format(conversation=conversation_text)
        messages = [{"role": "user", "content": prompt}]
        
        response = self.llm_client.chat_completion(messages, temperature=0.3)
        if not response:
            return result
            
        # JSON 응답 추출
        json_data = self.llm_client.extract_json_from_text(response)
        if json_data:
            # 키가 있는 경우만 업데이트
            for key in ["keywords", "intent", "doc_type"]:
                if key in json_data:
                    result[key] = json_data[key]
                    
        return result
    
    def generate_document(self, 
                         conversation: Dict[str, Any], 
                         doc_type: str, 
                         template: str, 
                         doc_prompt: str) -> str:
        """
        대화 내용을 기반으로 문서 생성
        
        Args:
            conversation: 대화 내용 딕셔너리
            doc_type: 문서 유형
            template: 문서 템플릿
            doc_prompt: 문서 생성을 위한 프롬프트 템플릿
            
        Returns:
            생성된 문서 내용
        """
        conversation_text = self.get_conversation_text(conversation)
        
        if not conversation_text:
            return f"# {doc_type} 문서\n\n대화 내용이 없습니다."
            
        # 프롬프트 생성 및 LLM 호출
        prompt = doc_prompt.format(
            conversation=conversation_text,
            doc_type=doc_type,
            template=template
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_client.chat_completion(
            messages, 
            temperature=0.7, 
            max_tokens=4000  # 문서 생성은 긴 응답이 필요할 수 있음
        )
        
        if not response:
            return f"# {doc_type} 문서\n\n문서 생성에 실패했습니다."
            
        # 마크다운 코드 블록 처리 (```로 시작하는 경우 제거)
        if response.startswith("```") and "\n" in response:
            first_newline = response.index("\n")
            if "md" in response[:first_newline].lower() or "markdown" in response[:first_newline].lower():
                response = response[first_newline+1:]
                
            if response.endswith("```"):
                response = response[:-3]
                
        return response.strip()
    
    def generate_commit_message(self, 
                               doc_type: str, 
                               doc_content: str,
                               conversation: Dict[str, Any],
                               commit_prompt: str) -> Dict[str, str]:
        """
        커밋 메시지 생성
        
        Args:
            doc_type: 문서 유형
            doc_content: 문서 내용
            conversation: 대화 내용 딕셔너리
            commit_prompt: 커밋 메시지 생성을 위한 프롬프트 템플릿
            
        Returns:
            생성된 커밋 메시지 정보 (type, scope, message)
        """
        conversation_text = self.get_conversation_text(conversation)
        
        # 기본값 설정
        result = {
            "type": "docs",
            "scope": doc_type.lower(),
            "message": f"Add {doc_type} documentation"
        }
        
        # 내용이 너무 길면 줄임
        if len(doc_content) > 2000:
            doc_content = doc_content[:1000] + "\n...[내용 일부 생략]...\n" + doc_content[-1000:]
            
        # 프롬프트 생성 및 LLM 호출
        prompt = commit_prompt.format(
            doc_type=doc_type,
            doc_content=doc_content,
            conversation=conversation_text
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_client.chat_completion(messages, temperature=0.5)
        
        if not response:
            return result
            
        # JSON 응답 추출
        json_data = self.llm_client.extract_json_from_text(response)
        if json_data:
            # 키가 있는 경우만 업데이트
            for key in ["type", "scope", "message"]:
                if key in json_data:
                    result[key] = json_data[key]
                    
        return result
