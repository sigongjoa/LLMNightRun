# 설정 가이드

이 문서는 LLMNightRun 프로젝트의 설정 방법에 대해 설명합니다.

## 환경 변수

LLMNightRun은 다음과 같은 환경 변수를 사용합니다:

| 환경 변수 | 설명 | 기본값 | 필수 여부 |
|-----------|------|--------|----------|
| `OPENAI_API_KEY` | OpenAI API 키 | - | 필수 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - | 선택 |
| `DATABASE_URL` | 데이터베이스 연결 문자열 | `sqlite:///llmnightrun.db` | 선택 |
| `DEBUG` | 디버그 모드 활성화 | `False` | 선택 |
| `HOST` | 서버 호스트 | `0.0.0.0` | 선택 |
| `PORT` | 서버 포트 | `8000` | 선택 |
| `GITHUB_TOKEN` | GitHub API 토큰 | - | 문서 자동화 기능 사용 시 필수 |

## 설정 파일

### 백엔드 설정

백엔드 설정은 `config.py` 파일에서 관리됩니다. 주요 설정 항목은 다음과 같습니다:

```python
# 데이터베이스 설정
database_url = os.getenv("DATABASE_URL", "sqlite:///llmnightrun.db")

# LLM 설정
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# 서버 설정
debug = os.getenv("DEBUG", "False").lower() == "true"
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "8000"))
```

### 프론트엔드 설정

프론트엔드 설정은 `frontend/config.ts` 파일에서 관리됩니다:

```typescript
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
```

## LLM 설정

### OpenAI 설정

OpenAI API를 사용하기 위한 설정:

1. [OpenAI 웹사이트](https://platform.openai.com/)에서 계정 생성
2. API 키 생성
3. 환경 변수 `OPENAI_API_KEY`에 API 키 설정

### Anthropic 설정

Anthropic API를 사용하기 위한 설정:

1. [Anthropic 웹사이트](https://www.anthropic.com/)에서 계정 생성
2. API 키 생성
3. 환경 변수 `ANTHROPIC_API_KEY`에 API 키 설정

### 로컬 LLM 설정

로컬 LLM을 사용하기 위한 설정:

1. 지원되는 로컬 LLM 모델 다운로드
2. 모델 경로 설정
3. 필요한 시스템 요구사항 확인 (GPU 등)

## GitHub 연동 설정

GitHub 연동을 위한 설정:

1. [GitHub 개인 액세스 토큰](https://github.com/settings/tokens) 생성
   - 최소 권한: `repo` (저장소 접근 권한)
2. 환경 변수 `GITHUB_TOKEN`에 토큰 설정
3. UI에서 GitHub 연동 설정

## 데이터베이스 설정

기본적으로 SQLite를 사용하지만, 다른 데이터베이스 시스템으로 전환 가능:

### PostgreSQL 설정

1. PostgreSQL 서버 설치 및 설정
2. 데이터베이스 및 사용자 생성
3. 환경 변수 `DATABASE_URL`을 다음과 같이 설정:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/dbname
   ```

## 로깅 설정

로깅 설정은 `backend/logger.py`에서 관리됩니다:

```python
import logging
import os

def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)
```

로그 레벨은 환경 변수 `LOG_LEVEL`로 설정 가능합니다 (DEBUG, INFO, WARNING, ERROR, CRITICAL).

## 문서 자동화 설정

문서 자동화 설정은 `docs_generator/config.py`에서 관리됩니다:

```python
# 문서 템플릿 설정
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

# 문서 출력 경로
docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

# GitHub 설정
github_token = os.getenv("GITHUB_TOKEN")
github_repo = os.getenv("GITHUB_REPO", "username/llmnightrun")
github_branch = os.getenv("GITHUB_BRANCH", "main")

# LLM 설정
llm_model = os.getenv("DOC_LLM_MODEL", "gpt-4")
```

## 개발 환경 설정

개발 환경 설정을 위한 단계:

1. 프로젝트 클론:
   ```bash
   git clone https://github.com/username/llmnightrun.git
   cd llmnightrun
   ```

2. Python 가상 환경 생성 및 활성화:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   cd frontend
   npm install
   cd ..
   ```

4. `.env` 파일 생성:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   DEBUG=True
   ```

5. 데이터베이스 초기화:
   ```bash
   python -c "from backend.database.connection import create_tables; create_tables()"
   ```

6. 개발 서버 실행:
   ```bash
   # 백엔드
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   
   # 프론트엔드 (별도 터미널에서)
   cd frontend
   npm run dev
   ```

## 프로덕션 환경 설정

프로덕션 환경에서는 다음과 같은 추가 설정을 권장합니다:

1. HTTPS 설정:
   - SSL 인증서 구성
   - 리버스 프록시 사용 (Nginx, Apache 등)

2. 보안 강화:
   - `DEBUG=False` 설정
   - 적절한 CORS 정책 설정
   - API 키 관리 강화

3. 성능 최적화:
   - 워커 프로세스 수 조정
   - 캐싱 설정
   - 데이터베이스 인덱싱 최적화

## 문제 해결

### 일반적인 문제

1. **API 키 관련 오류**:
   - 환경 변수가 올바르게 설정되었는지 확인
   - API 키가 유효한지 확인

2. **데이터베이스 연결 문제**:
   - 데이터베이스 URL 형식 확인
   - 데이터베이스 서버 실행 여부 확인
   - 권한 설정 확인

3. **프론트엔드-백엔드 통신 문제**:
   - CORS 설정 확인
   - API 기본 URL 설정 확인
   - 네트워크 연결 확인

### 로그 확인

문제 해결을 위해 로그 파일을 확인하세요:

```bash
tail -f logs/llmnightrun.log
```

상세한 로그를 보려면 환경 변수 `LOG_LEVEL`을 `DEBUG`로 설정하세요.
