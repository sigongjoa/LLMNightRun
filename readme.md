# LLMNightRun

멀티 LLM 통합 자동화 플랫폼

## 프로젝트 소개

LLMNightRun은 여러 LLM(Large Language Model)을 통합하여 코드 생성, 분석, 리팩토링 등의 작업을 자동화하는 플랫폼입니다.

## 시작하기

### 필수 요구사항

- Python 3.9 이상
- Node.js 16 이상
- npm 8 이상

### 설치 방법

1. 저장소 클론

```bash
git clone <repository-url>
cd LLMNightRun
```

2. 백엔드 설정

```bash
cd backend
pip install -r requirements.txt
python setup.py  # 데이터베이스 초기화 및 테스트 계정 생성
```

3. 프론트엔드 설정

```bash
cd frontend
npm install
```

### 실행 방법

1. 백엔드 서버 실행

```bash
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

2. 프론트엔드 서버 실행

```bash
cd frontend
npm run dev
```

3. 브라우저에서 접속: http://localhost:3000

### 기본 계정 정보

- 관리자 계정: `admin` / `admin123`
- 일반 사용자 계정: `user` / `user123`

## 주요 기능

- 멀티 LLM 통합 (OpenAI, Claude, 로컬 LLM 등)
- 코드 생성 및 분석
- GitHub 통합
- 프롬프트 엔지니어링 도구
- 에이전트 기반 자동화
- 코드베이스 인덱싱 및 검색

## 라이선스

이 프로젝트는 [라이선스 이름] 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 문의 및 기여

문의 사항이나 기여 방법에 대해서는 [이슈 트래커]를 이용해주세요.
