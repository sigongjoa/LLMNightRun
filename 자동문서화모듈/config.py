"""
자동 문서화 모듈의 설정 파일
"""

import os
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"
GENERATED_DOCS_DIR = BASE_DIR / "generated_docs"

# LLM API 설정
LLM_API_URL = "http://127.0.0.1:1234"
COMPLETIONS_ENDPOINT = "/v1/chat/completions"
MODEL_NAME = "deepseek-ai-Distill-Open-7B"  # 기본 모델 이름

# 문서 타입 및 확장자 매핑
DOC_TYPES = {
    "README": {
        "file_ext": "md",
        "template_file": "readme_template.md",
        "triggers": ["프로젝트", "소개", "설치", "overview"]
    },
    "INSTALL": {
        "file_ext": "md",
        "template_file": "install_template.md",
        "triggers": ["설치", "환경설정", "패키지", "install", "setup"]
    },
    "USAGE": {
        "file_ext": "md",
        "template_file": "usage_template.md", 
        "triggers": ["사용법", "예제", "명령어", "usage", "example"]
    },
    "API": {
        "file_ext": "md",
        "template_file": "api_template.md",
        "triggers": ["API", "엔드포인트", "endpoint", "parameter"]
    },
    "MODULE": {
        "file_ext": "md",
        "template_file": "module_template.md",
        "triggers": ["모듈", "함수", "클래스", "module", "class", "function"]
    },
    "RESULTS": {
        "file_ext": "md",
        "template_file": "results_template.md",
        "triggers": ["결과", "실험", "테스트", "result", "experiment", "test"]
    },
    "PLAN": {
        "file_ext": "md",
        "template_file": "plan_template.md",
        "triggers": ["계획", "기획", "설계", "plan", "design", "feature"]
    },
    "CHANGELOG": {
        "file_ext": "md",
        "template_file": "changelog_template.md",
        "triggers": ["변경", "이력", "버전", "change", "version", "release"]
    },
    "DEPLOY": {
        "file_ext": "md",
        "template_file": "deploy_template.md",
        "triggers": ["배포", "도커", "deploy", "docker", "release"]
    }
}

# Git 설정
GIT_ENABLED = False  # GUI에서 토글 가능하도록 기본값 False
GIT_COMMIT_TEMPLATE = "docs({doc_type}): Add {file_name}"

# GUI 설정
GUI_TITLE = "NightRun 자동 문서화 모듈"
GUI_WIDTH = 1024
GUI_HEIGHT = 768

# LLM 프롬프트 템플릿
INTENT_EXTRACTION_PROMPT = """
다음은 사용자와 AI 간의 대화 기록입니다. 이 대화를 분석하여 다음을 추출해주세요:

1. 주요 키워드 (쉼표로 구분)
2. 대화의 주요 의도/목적
3. 이 대화를 어떤 유형의 문서로 요약하는 것이 가장 적합한지 (README, INSTALL, USAGE, API, MODULE, RESULTS, PLAN, CHANGELOG, DEPLOY 중에서 선택)

대화 기록:
{conversation}

JSON 형식으로 응답해주세요:
{{
    "keywords": ["키워드1", "키워드2", ...],
    "intent": "주요 의도/목적",
    "doc_type": "문서 유형"
}}
"""

DOC_GENERATION_PROMPT = """
다음 사용자 대화 내용을 기반으로 {doc_type} 형식의 문서를 작성해주세요.

# 대화 내용
{conversation}

# {doc_type} 문서 템플릿
{template}

위 템플릿을 참고하여 대화 내용을 바탕으로 완성된 {doc_type} 문서를 만들어주세요.
마크다운 형식으로 작성하고, 템플릿의 구조를 따라 내용을 채워주세요.
특별히 명시되지 않은 정보는 대화 내용을 바탕으로 합리적으로 추론하여 채워넣어주세요.
코드 예제가 필요하면 대화 내용에서 추출해서 적절한 위치에 배치해주세요.
"""

COMMIT_MESSAGE_PROMPT = """
다음 문서 내용과 대화 기록을 바탕으로 Git 커밋 메시지를 생성해주세요.
Conventional Commits 형식을 사용해야 합니다 (예: feat, fix, docs, style, refactor, test, chore)

# 문서 유형
{doc_type}

# 문서 내용
{doc_content}

# 대화 기록
{conversation}

다음과 같은 형식의 커밋 메시지를 JSON 형식으로 응답해주세요:
{{
    "type": "커밋 유형 (docs, feat, fix 등)",
    "scope": "영향 범위 (선택적)",
    "message": "간결한 변경 내용 설명"
}}
"""
