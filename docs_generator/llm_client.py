"""
LLM API 연동 모듈

이 모듈은 LLM API와의 통신을 관리하며 문서 생성을 위한 프롬프트를 처리합니다.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# 로깅 설정
logger = logging.getLogger(__name__)

# 문서 유형별 지침 매핑
DOC_TYPE_INSTRUCTIONS = {
    "README": "프로젝트 제목, 설명, 주요 기능, 설치/사용 방법, 프로젝트 구조, 기여 방법, 라이선스 정보",
    "API": "API 개요, 엔드포인트 목록(경로/메서드/설명), 상세 정보(요청/응답), 오류 코드, 인증 정보",
    "MODELS": "데이터 모델 개요, 각 모델 상세 설명(필드/타입/관계), 관계 다이어그램, 사용 예제",
    "DATABASE": "데이터베이스 스키마 개요, 테이블 구조(필드/타입/제약조건), 관계, 인덱스, 마이그레이션",
    "ARCHITECTURE": "시스템 아키텍처 개요, 주요 컴포넌트, 모듈 간 의존성/상호작용, 디렉토리 구조, 설계 패턴/원칙",
    "TESTING": "테스트 전략 개요, 테스트 환경 설정, 테스트 실행 방법, 테스트 구조, 커버리지 정보",
    "CHANGELOG": "버전별 변경 사항(최신 버전부터), 변경 유형(추가/수정/제거/버그 수정), 변경 설명, 날짜",
    "CONFIGURATION": "설정 파일 구조/위치, 설정 옵션 설명(이름/타입/기본값), 환경 변수, 설정 예제"
}

class LLMClient:
    """LLM API와 통신하기 위한 클라이언트 클래스"""

    def __init__(self, 
                api_key: Optional[str] = None, 
                api_url: Optional[str] = None,
                model: str = "gpt-4"):
        """
        LLM 클라이언트 초기화
        
        Args:
            api_key: API 키 (None인 경우 환경 변수에서 가져옴)
            api_url: API 엔드포인트 URL (None인 경우 기본값 사용)
            model: 사용할 모델 이름
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API 키가 제공되지 않았습니다. OPENAI_API_KEY 환경 변수를 설정하세요.")
            
        self.api_url = api_url or "https://api.openai.com/v1/chat/completions"
        self.model = model
        
    def generate_document(self, 
                        doc_type: str, 
                        code_analysis: Dict[str, Any], 
                        existing_content: Optional[str] = None) -> str:
        """
        코드 분석 결과를 기반으로 문서 생성
        
        Args:
            doc_type: 문서 유형 (README, API, MODELS 등)
            code_analysis: 코드 분석 결과 데이터
            existing_content: 기존 문서 내용 (있는 경우)
            
        Returns:
            생성된 문서 내용
        """
        prompt = self._create_prompt(doc_type, code_analysis, existing_content)
        return self._call_llm_api(prompt)
    
    def generate_commit_message(self, 
                             changes: Dict[str, Any],
                             code_analysis: Dict[str, Any]) -> str:
        """
        변경 내역을 기반으로 커밋 메시지 생성
        
        Args:
            changes: 변경된 파일 및 내용 정보
            code_analysis: 코드 분석 결과
            
        Returns:
            생성된 커밋 메시지
        """
        prompt = self._create_commit_message_prompt(changes, code_analysis)
        return self._call_llm_api(prompt)
    
    def _create_prompt(self, 
                     doc_type: str, 
                     code_analysis: Dict[str, Any], 
                     existing_content: Optional[str] = None) -> str:
        """
        문서 유형에 따른 프롬프트 생성
        
        Args:
            doc_type: 문서 유형
            code_analysis: 코드 분석 결과
            existing_content: 기존 문서 내용
            
        Returns:
            생성된 프롬프트
        """
        doc_type_upper = doc_type.upper()
        doc_instructions = DOC_TYPE_INSTRUCTIONS.get(
            doc_type_upper, 
            f"{doc_type}.md 문서의 목적과 내용에 맞는 구조"
        )
        
        # 간소화된 기본 프롬프트 템플릿
        prompt = [
            f"당신은 소프트웨어 문서화 전문가입니다. {doc_type}.md 문서를 작성해주세요.",
            "문서는 마크다운 형식으로 작성하고, 명확하고 구조적이어야 합니다.",
            f"이 문서에는 다음 내용이 포함되어야 합니다: {doc_instructions}",
            "\n### 코드 분석 데이터:",
            f"```json\n{json.dumps(code_analysis, indent=2, ensure_ascii=False)}\n```"
        ]
        
        # 기존 문서가 있는 경우, 업데이트 지침 추가
        if existing_content:
            prompt.extend([
                "\n### 기존 문서 내용:",
                f"```markdown\n{existing_content}\n```",
                "기존 문서를 참고하여 내용을 업데이트하고, 중요 정보는 유지하면서 새 코드 분석 정보를 반영해주세요.",
                "문서의 톤과 스타일을 일관되게 유지해주세요."
            ])
        else:
            prompt.append("\n새로운 문서를 처음부터 작성해주세요.")
        
        # 응답 형식 지침 추가
        prompt.append("\n마크다운 형식으로만, 추가 설명 없이 바로 문서 내용만 반환해주세요.")
        
        return "\n".join(prompt)

    def _create_commit_message_prompt(self, 
                                   changes: Dict[str, Any],
                                   code_analysis: Dict[str, Any]) -> str:
        """
        커밋 메시지 생성을 위한 프롬프트 생성
        
        Args:
            changes: 변경 내역 정보
            code_analysis: 코드 분석 결과
            
        Returns:
            생성된 프롬프트
        """
        # 간소화된 커밋 메시지 프롬프트
        prompt = [
            "다음 변경 내역과 코드 분석 정보를 바탕으로 Git 커밋 메시지를 작성해주세요.",
            "\n### 변경된 파일 목록:",
            f"```json\n{json.dumps(changes, indent=2, ensure_ascii=False)}\n```",
            "\n### 코드 분석 결과:",
            f"```json\n{json.dumps(code_analysis, indent=2, ensure_ascii=False)}\n```",
            "\n커밋 메시지 규칙:",
            "1. 제목 줄: 50자 이내 변경 요약",
            "2. 빈 줄",
            "3. 본문: 변경 내용 상세 설명",
            "4. 접두사 사용: feat(기능), fix(버그), docs(문서), style(포맷), refactor(리팩토링), test(테스트), chore(기타)",
            "\n커밋 메시지만 반환해주세요."
        ]
        
        return "\n".join(prompt)

    def _call_llm_api(self, prompt: str) -> str:
        """
        LLM API 호출
        
        Args:
            prompt: 프롬프트 문자열
            
        Returns:
            LLM 응답 텍스트
            
        Raises:
            RuntimeError: API 호출 실패 시
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful documentation expert."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 4000
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"API 호출 실패: {response.status_code} - {response.text}")
                raise RuntimeError(f"API 호출 실패: {response.status_code}")
                
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"LLM API 호출 중 오류 발생: {str(e)}")
            raise RuntimeError(f"LLM API 호출 실패: {str(e)}")

    def get_diff_summary(self, file_diffs: Dict[str, str]) -> str:
        """
        파일 변경 내용 요약 생성
        
        Args:
            file_diffs: 파일별 diff 내용
            
        Returns:
            변경 내용 요약
        """
        # 간소화된 요약 프롬프트
        prompt = [
            "다음 Git 변경 내용을 간결하게 요약해주세요:",
            f"```\n{json.dumps(file_diffs, indent=2, ensure_ascii=False)}\n```",
            "전체 변경에 대한 1-2문장 설명과 주요 변경사항 3-5개를 간략히 나열해주세요.",
            "추가 설명 없이 텍스트만 반환해주세요."
        ]
        
        return self._call_llm_api("\n".join(prompt))