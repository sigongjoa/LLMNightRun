# LLMNightRun

## 소개

LLMNightRun은 멀티 LLM 통합 자동화 플랫폼입니다. 여러 LLM(Large Language Model)을 효율적으로 통합하고 관리하며, 개발 워크플로우를 자동화하는 도구입니다.

## 주요 기능

- **멀티 LLM 연동**: 다양한 LLM 서비스와 연동하여 최적의 결과 제공
- **코드 생성 및 관리**: 프롬프트 기반으로 코드 생성 및 관리
- **에이전트 자동화**: 반복적인 작업을 에이전트를 통해 자동화
- **자동 디버깅**: 코드 문제 자동 분석 및 해결 제안
- **로컬 LLM 연동**: 오프라인 환경에서도 사용 가능한 로컬 LLM 통합
- **문서 자동화**: 코드 및 구조 분석을 통한 문서 자동 생성
- **GitHub 연동**: 생성된 문서 및 코드의 자동 커밋 및 푸시

## 시작하기

### 설치

```bash
# 저장소 클론
git clone https://github.com/username/llmnightrun.git
cd llmnightrun

# 의존성 설치
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 실행

백엔드와 프론트엔드를 각각 실행:

```bash
# 백엔드 실행
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 프론트엔드 실행
cd frontend
npm run dev
```

### 테스트 실행

```bash
# 테스트 의존성 설치
pip install -r tests/requirements-test.txt

# 모든 테스트 실행
python run_tests.py

# 단위 테스트만 실행
python run_tests.py --unit

# 통합 테스트만 실행
python run_tests.py --integration

# 커버리지 리포트 생성
python run_tests.py --coverage

# 특정 테스트 파일 실행
python run_tests.py --test-file tests/unit/test_llm_service.py
```

## 프로젝트 구조

주요 디렉토리 구조:

```
LLMNightRun/
├── backend/         # 백엔드 코드 (FastAPI)
├── docs/            # 프로젝트 문서
│   └── features/    # 기능별 상세 문서
├── frontend/        # 프론트엔드 코드 (Next.js)
├── tests/           # 테스트 코드
│   ├── unit/        # 단위 테스트
│   └── integration/ # 통합 테스트
└── scripts/         # 유틸리티 스크립트
```

## 기술 스택

- **백엔드**: FastAPI, Python
- **프론트엔드**: Next.js, React, TypeScript, Material-UI
- **데이터베이스**: SQLite
- **LLM 통합**: OpenAI API, Anthropic API, 로컬 LLM
