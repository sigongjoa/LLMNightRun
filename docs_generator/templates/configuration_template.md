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
