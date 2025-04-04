# LLMNightRun

LLMNightRun은 여러 LLM(대규모 언어 모델)을 통합 자동화하고 코드 베이스를 관리하는 플랫폼입니다.

## 주요 기능

- 여러 LLM API(OpenAI, Claude) 연동
- ChatGPT, Claude 웹 인터페이스 자동화
- 코드 스니펫 관리 및 버전 관리
- 결과를 GitHub에 자동 업로드
- API 및 웹 인터페이스를 통한 질문 제출

## 시스템 구성

```
LLMNightRun/
├── backend/              # FastAPI 백엔드
│   ├── main.py           # 메인 API 서버
│   ├── models.py         # 데이터 모델 정의
│   ├── llm_api.py        # LLM API 연동
│   ├── llm_crawler.py    # 웹 크롤링
│   ├── github_uploader.py # GitHub 업로드
│   ├── code_manager.py   # 코드 관리
│   ├── scheduler.py      # 자동 스케줄러
│   └── database/         # 데이터베이스 관련
├── frontend/             # 프론트엔드 (추후 구현)
├── .env                  # 환경 변수
└── README.md             # 프로젝트 설명
```

## 설치 방법

### 요구 사항

- Python 3.8 이상
- Pip 패키지 관리자
- Chrome 브라우저 (웹 크롤링용)
- GitHub 계정 및 토큰

### 설치 단계

1. 저장소 복제

```bash
git clone https://github.com/your-username/LLMNightRun.git
cd LLMNightRun
```

2. 가상 환경 설정

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

3. 의존성 설치

```bash
pip install -r requirements.txt
```

4. 환경 변수 설정

`.env` 파일을 편집하여 API 키, GitHub 토큰 등을 설정하세요.

## 사용 방법

### 백엔드 서버 실행

```bash
cd backend
# uvicorn main:app --reload
python -m backend.main --reload
```

서버가 시작되면 `http://localhost:8000`에서 API 문서를 확인할 수 있습니다.

### API 엔드포인트

- `GET /questions/`: 모든 질문 조회
- `POST /questions/`: 새 질문 추가
- `GET /responses/`: 모든 응답 조회
- `POST /responses/`: 새 응답 추가
- `POST /ask/{llm_type}`: LLM에 질문 요청
- `POST /github/upload`: GitHub에 결과 업로드
- `GET /code-snippets/`: 코드 스니펫 조회
- `POST /code-snippets/`: 새 코드 스니펫 추가

## 개발 계획

1. **프론트엔드 개발**: React 기반 UI 구현
2. **추가 LLM 지원**: 더 많은 LLM 통합
3. **코드 평가 메커니즘**: 코드 품질 평가 추가
4. **스케줄링 기능 강화**: 자동 배치 작업 지원

## 라이선스

[MIT 라이선스](LICENSE)
