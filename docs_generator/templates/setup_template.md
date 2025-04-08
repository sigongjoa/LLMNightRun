# 설치 및 설정 가이드

## 시스템 요구사항

* **운영체제**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
* **Python**: 3.8 이상
* **Node.js**: 14.0 이상
* **데이터베이스**: SQLite (기본), MySQL 5.7+ 또는 PostgreSQL 12+ (선택)

## 설치 방법

### 1. 저장소 복제

```bash
git clone https://github.com/username/project.git
cd project
```

### 2. 백엔드 설정

```bash
# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 환경 변수 설정

# 데이터베이스 초기화
python migrate.py
```

### 3. 프론트엔드 설정

```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env.local
# .env.local 파일을 편집하여 필요한 환경 변수 설정
```

## 실행 방법

### 개발 모드

백엔드와 프론트엔드를 별도의 터미널에서 실행합니다.

#### 백엔드 실행

```bash
# 프로젝트 루트 디렉토리에서
source venv/bin/activate  # Windows: venv\Scripts\activate
python run.py
```

#### 프론트엔드 실행

```bash
# frontend 디렉토리에서
npm run dev
```

개발 서버가 다음 주소에서 실행됩니다:
* 백엔드: http://localhost:8000
* 프론트엔드: http://localhost:3000

### 프로덕션 모드

#### Docker Compose 사용

```bash
# 프로젝트 루트 디렉토리에서
docker-compose up -d
```

## 환경 변수

### 백엔드 (.env)

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| DEBUG | 디버그 모드 활성화 | True |
| SECRET_KEY | 애플리케이션 비밀 키 | random_string |
| DATABASE_URL | 데이터베이스 연결 문자열 | sqlite:///db.sqlite3 |
| ALLOWED_HOSTS | 허용된 호스트 목록 | localhost,127.0.0.1 |

### 프론트엔드 (.env.local)

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| NEXT_PUBLIC_API_URL | 백엔드 API URL | http://localhost:8000 |
| NEXT_PUBLIC_ENV | 환경 설정 | development |

## 문제 해결

### 일반적인 문제

#### 백엔드 연결 오류

1. 백엔드 서버가 실행 중인지 확인
2. .env.local의 NEXT_PUBLIC_API_URL이 올바른지 확인
3. CORS 설정이 올바른지 확인

#### 데이터베이스 마이그레이션 오류

1. 데이터베이스 연결 문자열이 올바른지 확인
2. 마이그레이션 파일이 최신인지 확인
3. 필요한 경우 마이그레이션을 재설정: `python reset_migrations.py`
