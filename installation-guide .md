# LLMNightRun 설치 및 실행 가이드

이 문서는 LLMNightRun 애플리케이션을 설치하고 실행하는 과정을 설명합니다.

## 사전 요구사항

- Python 3.8 이상
- Node.js 16 이상과 npm
- Git

## 1. 저장소 복제

```bash
git clone https://github.com/your-username/LLMNightRun.git
cd LLMNightRun
```

## 2. 백엔드 설정

### 가상환경 생성 및 활성화

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 환경 변수 설정

`backend/.env` 파일에 필요한 API 키와 설정을 입력하세요:

```
# LLMNightRun 환경 변수 설정

# 데이터베이스 설정
DATABASE_URL=sqlite:///./llmnightrun.db

# API 키
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GitHub 설정
GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username
GITHUB_REPO=your_repository_name

# 웹 크롤링 설정
OPENAI_USERNAME=your_openai_username
OPENAI_PASSWORD=your_openai_password
CLAUDE_USERNAME=your_claude_username
CLAUDE_PASSWORD=your_claude_password
HEADLESS=true

# 서버 설정
PORT=8000
HOST=0.0.0.0
DEBUG=true
```

### 데이터베이스 초기화

```bash
cd backend
python -c "from database.connection import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 백엔드 서버 실행

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

백엔드 서버가 실행되면 `http://localhost:8000/docs`에서 API 문서를 확인할 수 있습니다.

## 3. 프론트엔드 설정

### 의존성 설치

```bash
cd frontend
npm install
```

### 환경 변수 설정

`frontend/.env.local` 파일을 생성하고 다음 내용을 추가하세요:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 프론트엔드 개발 서버 실행

```bash
cd frontend
npm run dev
```

프론트엔드 개발 서버가 실행되면 `http://localhost:3000`에서 애플리케이션을 확인할 수 있습니다.

## 4. 애플리케이션 사용하기

1. 브라우저에서 `http://localhost:3000`에 접속합니다.
2. 대시보드에서 시스템 상태를 확인합니다.
3. '설정' 페이지에서 API 키를 구성합니다.
4. '질문 제출' 페이지에서 새 질문을 제출합니다.
5. '결과' 페이지에서 다양한 LLM의 응답을 비교합니다.
6. '코드 관리' 페이지에서 생성된 코드 스니펫을 관리합니다.

## 5. 문제 해결

### 백엔드 관련 문제

- **모듈을 찾을 수 없음**:
  Python 모듈 경로를 확인하세요. 필요하다면 `PYTHONPATH` 설정:
  ```bash
  # Linux/macOS
  export PYTHONPATH=$PYTHONPATH:$(pwd)
  # Windows
  set PYTHONPATH=%PYTHONPATH%;%cd%
  ```

- **데이터베이스 문제**:
  데이터베이스 파일 권한과 경로를 확인하세요.

### 프론트엔드 관련 문제

- **API 연결 오류**:
  백엔드 서버가 실행 중인지 확인하고, `.env.local` 파일에서 API URL이 올바르게 설정되었는지 확인하세요.

- **빌드 오류**:
  노드 모듈을 삭제하고 다시 설치해보세요:
  ```bash
  rm -rf node_modules
  npm install
  ```

## 6. 프로덕션 배포

### 백엔드 배포

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 프론트엔드 빌드 및 배포

```bash
cd frontend
npm run build
npm run start
```

## 7. 추가 정보

- API 문서: `http://localhost:8000/docs`
- 소스 코드 구조 및 기능에 대한 자세한 내용은 `readme.md`를 참조하세요.
