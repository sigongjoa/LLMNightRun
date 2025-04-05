"""
LLM API 연동 모듈

이 모듈은 LLM API와의 통신을 관리하며 문서 생성을 위한 프롬프트를 처리합니다.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

# 로깅 설정
logger = logging.getLogger(__name__)


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
        # 기본 프롬프트 템플릿
        base_prompt = f"""
당신은 소프트웨어 문서화 전문가입니다. 제공된 코드 분석 정보를 기반으로 {doc_type}.md 문서를 작성해주세요.
문서는 마크다운 형식으로 작성되어야 하며, 내용은 명확하고 구조적이어야 합니다.

### 문서 유형: {doc_type}

### 코드 분석 데이터:
```json
{json.dumps(code_analysis, indent=2, ensure_ascii=False)}
```
"""

        # 문서 유형별 추가 지침
        type_specific_instructions = {
            "README": """
README.md 파일은 다음 내용을 포함해야 합니다:
1. 프로젝트 제목 및 간단한 설명
2. 주요 기능 목록
3. 설치 방법
4. 사용 방법
5. 프로젝트 구조
6. 기여 방법
7. 라이선스 정보

사용자가 프로젝트를 이해하고 시작하는 데 필요한 모든 정보를 포함해주세요.
""",
            "API": """
API.md 파일은 다음 내용을 포함해야 합니다:
1. API 개요
2. 엔드포인트 목록 (경로, 메서드, 설명)
3. 각 엔드포인트의 상세 정보 (요청 파라미터, 응답 형식, 예제)
4. 오류 코드 및 처리 방법
5. 인증 정보 (필요한 경우)

모든 API 엔드포인트를 명확하게 문서화하고, 개발자가 API를 쉽게 이해하고 사용할 수 있도록 작성해주세요.
""",
            "MODELS": """
MODELS.md 파일은 다음 내용을 포함해야 합니다:
1. 데이터 모델 개요
2. 각 모델의 상세 설명 (필드, 타입, 관계)
3. 모델 간의 관계 다이어그램 (마크다운으로 표현)
4. 모델 사용 예제

모든 데이터 모델을 명확하게 문서화하고, 개발자가 데이터 구조를 쉽게 이해할 수 있도록 작성해주세요.
""",
            "DATABASE": """
DATABASE.md 파일은 다음 내용을 포함해야 합니다:
1. 데이터베이스 스키마 개요
2. 테이블 구조 (필드, 타입, 제약 조건)
3. 테이블 간의 관계
4. 인덱스 정보
5. 마이그레이션 정보

데이터베이스 구조를 명확하게 문서화하고, 개발자가 데이터베이스를 쉽게 이해하고 사용할 수 있도록 작성해주세요.
""",
            "ARCHITECTURE": """
ARCHITECTURE.md 파일은 다음 내용을 포함해야 합니다:
1. 시스템 아키텍처 개요
2. 주요 컴포넌트 설명
3. 모듈 간의 의존성 및 상호작용
4. 디렉토리 구조 및 설명
5. 설계 패턴 및 원칙

시스템 아키텍처를 명확하게 문서화하고, 개발자가 시스템 구조를 쉽게 이해할 수 있도록 작성해주세요.
""",
            "TESTING": """
TESTING.md 파일은 다음 내용을 포함해야 합니다:
1. 테스트 전략 개요
2. 테스트 환경 설정 방법
3. 테스트 실행 방법
4. 테스트 구조 및 설명
5. 테스트 커버리지 정보

테스트 방법을 명확하게 문서화하고, 개발자가 테스트를 쉽게 실행하고 이해할 수 있도록 작성해주세요.
""",
            "CHANGELOG": """
CHANGELOG.md 파일은 다음 내용을 포함해야 합니다:
1. 버전별 변경 사항 목록 (최신 버전부터)
2. 각 변경 사항의 유형 (추가, 수정, 제거, 버그 수정 등)
3. 각 변경 사항에 대한 간단한 설명
4. 변경 날짜

변경 이력을 명확하게 문서화하고, 사용자가 변경 사항을 쉽게 이해할 수 있도록 작성해주세요.
""",
            "CONFIGURATION": """
CONFIGURATION.md 파일은 다음 내용을 포함해야 합니다:
1. 설정 파일 구조 및 위치
2. 각 설정 옵션 설명 (이름, 타입, 기본값, 설명)
3. 환경 변수 목록 및 설명
4. 설정 예제

설정 방법을 명확하게 문서화하고, 사용자가 시스템을 쉽게 구성할 수 있도록 작성해주세요.
"""
        }

        # 문서 유형별 지침 추가
        if doc_type.upper() in type_specific_instructions:
            base_prompt += type_specific_instructions[doc_type.upper()]
        else:
            base_prompt += f"\n{doc_type}.md 문서의 목적과 내용을 파악하여 적절한 구조로 작성해주세요."

        # 기존 문서가 있는 경우, 업데이트 지침 추가
        if existing_content:
            base_prompt += f"""
### 기존 문서 내용:
```markdown
{existing_content}
```

위의 기존 문서를 참고하여 내용을 업데이트해주세요. 기존의 중요한 정보는 유지하면서 새로운 코드 분석 정보를 반영해주세요.
가능한 한 문서의 톤과 스타일을 일관되게 유지해주세요.
"""
        else:
            base_prompt += "\n새로운 문서를 처음부터 작성해주세요."

        # 응답 형식 지침 추가
        base_prompt += """
### 응답 형식:
마크다운 형식으로만 문서를 작성해주세요. 문법적으로 정확하고 가독성이 좋은 문서를 작성해주세요.
추가 설명 없이 바로 마크다운 문서 내용만 반환해주세요.
"""

        return base_prompt

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
        prompt = f"""
당신은 명확하고 유용한 Git 커밋 메시지를 작성하는 전문가입니다.
다음 변경 내역과 코드 분석 정보를 바탕으로 적절한 커밋 메시지를 작성해주세요.

### 변경된 파일 목록:
```json
{json.dumps(changes, indent=2, ensure_ascii=False)}
```

### 코드 분석 결과:
```json
{json.dumps(code_analysis, indent=2, ensure_ascii=False)}
```

다음 규칙에 따라 커밋 메시지를 작성해주세요:
1. 첫 줄에 변경의 요약을 50자 이내로 작성 (제목)
2. 제목 다음에 빈 줄 추가
3. 그 다음에 변경 내용에 대한 자세한 설명 (본문)
4. 변경 유형에 따라 접두사 사용:
   - feat: 새로운 기능 추가
   - fix: 버그 수정
   - docs: 문서 변경
   - style: 코드 포맷팅, 세미콜론 누락 등 (코드 변경 없음)
   - refactor: 코드 리팩토링
   - test: 테스트 코드 추가 또는 수정
   - chore: 빌드 프로세스 또는 보조 도구 및 라이브러리 변경

### 응답 형식:
커밋 메시지만 반환해주세요. 추가 설명이나 마크다운 형식은 필요 없습니다.
"""
        return prompt

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
                "temperature": 0.2,  # 낮은 온도로 일관된 출력 유도
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
        # 간략한 요약을 위한 프롬프트
        prompt = f"""
다음은 Git 저장소의 변경 내용입니다. 이 변경 내용을 간결하게 요약해주세요.

### 변경된 파일 diff:
```
{json.dumps(file_diffs, indent=2, ensure_ascii=False)}
```

다음 형식으로 요약해주세요:
1. 전체 변경 내용에 대한 1-2문장 설명
2. 주요 변경 사항 3-5개를 간략히 나열 (변경 유형과 내용)

응답은 간결하게 작성해주세요. 마크다운 형식이나 추가 설명 없이 텍스트만 반환해주세요.
"""
        
        return self._call_llm_api(prompt)