# LLM Night Run

로컬 LLM, 벡터 검색, 대화 관리를 위한 통합 AI/ML 개발 환경입니다.

## 기능 소개

LLM Night Run은 다음과 같은 주요 기능을 제공합니다:

- **대화 관리**: 로컬 LLM과의 대화를 저장하고 관리할 수 있습니다.
- **벡터 검색**: 벡터 데이터베이스를 통한 의미 기반 검색 기능을 제공합니다.
- **Arxiv 논문 관리**: Arxiv API를 통해 논문을 검색, 다운로드, 관리할 수 있습니다.
- **GitHub 문서 자동생성**: GitHub 저장소 분석 및 문서 자동 생성 기능을 제공합니다.
- **GitHub AI 설정**: GitHub 저장소에 AI/ML 환경 설정을 자동으로 구성합니다.
- **플러그인 시스템**: 사용자 정의 기능을 추가할 수 있는 플러그인 시스템을 지원합니다.

## 시스템 요구사항

- Python 3.7 이상
- 필수 패키지:
  - numpy
  - requests
  - pyyaml
  - tkinter (Python과 함께 설치)
- 권장 패키지:
  - sentence-transformers (벡터 인코딩)
  - arxiv (Arxiv API 사용)
  - pygithub (GitHub API 사용)
  - torch/tensorflow (기계학습 지원)

## 설치 및 실행

### 설치

1. 저장소 복제:
   ```
   git clone https://github.com/username/LLMNightRun.git
   cd LLMNightRun
   ```

2. 실행 (의존성 자동 확인 및 설치):
   ```
   python run.py
   ```

### 실행 옵션

다음과 같은 실행 옵션을 사용할 수 있습니다:

- `--config [파일경로]`: 사용자 지정 설정 파일 경로
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: 로그 레벨 설정
- `--simplified`: 간소화된 UI 모드로 실행
- `--temp-dir [디렉토리]`: 임시 파일용 디렉토리 지정

예시:
```
python run.py --simplified --log-level DEBUG
```

## 주요 모듈 설명

### 대화 관리 (Conversation)

- 로컬 LLM과의 대화 저장 및 관리
- JSON/마크다운 형식으로 대화 내보내기
- 대화 검색 및 복원 기능

### 벡터 DB (Vector DB)

- 벡터 데이터베이스 기반 의미 검색 지원
- 다양한 문서 형식 지원 (텍스트, 마크다운, 논문 등)
- 커스텀 인코더 사용 가능

### Arxiv 논문 모듈 (Arxiv Module)

- Arxiv API를 이용한 논문 검색
- PDF 다운로드 및 관리
- 논문 컬렉션 기능
- 벡터 DB 통합으로 의미 기반 논문 검색

### GitHub 문서 생성 (GitHub Docs)

- GitHub 저장소 코드 분석
- 주요 구성 요소 (함수, 클래스 등) 추출
- 다양한 템플릿 기반 문서 자동 생성
- 벡터 DB 통합으로 생성된 문서 검색

### GitHub AI 설정 (GitHub AI Setup)

- GitHub 저장소 AI/ML 관련 구성 요소 분석
- AI/ML 환경 설정 자동 생성 (requirements.txt, Dockerfile 등)
- 다양한 AI 프레임워크 지원 (PyTorch, TensorFlow, Hugging Face 등)
- ML 모델 설정 파일 자동 생성

### 로컬 LLM 연동 (Local LLM)

- 로컬에서 실행 중인 LLM 서버와 연동
- 다양한 모델 지원
- 모델 파라미터 조정 가능

### 플러그인 시스템 (Plugin System)

- 사용자 정의 기능 추가 지원
- 이벤트 기반 프로그래밍 모델
- 모듈 간 느슨한 결합을 위한 이벤트 버스 사용

## 설정

기본 설정 파일은 `config/config.yaml`에 있으며, 다음과 같은 주요 설정 항목이 있습니다:

- **core**: 핵심 시스템 설정 (로그 레벨, 데이터 디렉토리 등)
- **local_llm**: 로컬 LLM 연결 설정
- **vector_db**: 벡터 데이터베이스 설정
- **conversation**: 대화 관리 설정
- **arxiv_module**: Arxiv 모듈 설정
- **github_docs**: GitHub 문서 모듈 설정
- **github_ai_setup**: GitHub AI 설정 모듈 설정
- **gui**: GUI 관련 설정 (테마, 폰트 크기 등)
- **plugin_system**: 플러그인 시스템 설정

## 개발 가이드

### 이벤트 시스템 사용

모듈 간 통신은 이벤트 시스템을 통해 이루어집니다:

```python
from core.events import subscribe, publish

# 이벤트 구독
subscribe("event_type", callback_function)

# 이벤트 발행
publish("event_type", param1=value1, param2=value2)
```

### 새 모듈 추가

1. 적절한 디렉토리에 모듈 생성
2. `__init__.py`에 필요한 함수/클래스 노출
3. 이벤트 시스템 사용하여 다른 모듈과 통합
4. GUI 탭 생성 (필요한 경우)

### GUI 탭 추가

1. `gui/components/modules/` 디렉토리에 탭 컴포넌트 생성
2. `gui/app_simplified.py`에 탭 통합

## 프로젝트 구조

```
LLMNightRun/
│
├── config/               # 설정 파일
├── logs/                 # 로그 파일
├── data/                 # 데이터 파일
│   ├── vector_db/        # 벡터 DB 데이터
│   ├── conversations/    # 대화 데이터
│   ├── arxiv/            # Arxiv 논문 데이터
│   ├── github_docs/      # GitHub 문서 데이터
│   └── github_ai/        # GitHub AI 설정 데이터
│
├── core/                 # 핵심 기능
│   ├── config.py         # 설정 관리
│   ├── events.py         # 이벤트 시스템
│   ├── logging.py        # 로깅 유틸리티
│   └── __init__.py
│
├── local_llm/            # 로컬 LLM 연동
├── conversation/         # 대화 관리
├── vector_db/            # 벡터 데이터베이스
├── arxiv_module/         # Arxiv 논문 관리
├── github_docs/          # GitHub 문서 생성
├── github_ai_setup/      # GitHub AI 설정
├── plugin_system/        # 플러그인 시스템
│
├── gui/                  # GUI 컴포넌트
│   ├── app.py            # 메인 앱
│   ├── app_simplified.py # 간소화된 앱
│   ├── components/       # UI 컴포넌트
│   └── __init__.py
│
├── plugins/              # 사용자 플러그인
├── main.py               # 기본 진입점
├── run.py                # 실행 스크립트
└── requirements.txt      # 의존성 목록
```

## 라이선스

MIT 라이선스로 배포됩니다.
