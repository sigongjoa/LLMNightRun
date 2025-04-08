# 배포 가이드

## 개요

이 문서는 [프로젝트명]의 배포 방법을 설명합니다.

## 배포 환경

### 권장 사양

* **CPU**: 2+ 코어
* **메모리**: 4GB+
* **디스크**: 20GB+ SSD
* **운영체제**: Ubuntu 20.04+ LTS

## 배포 방법

### Docker Compose 배포

#### 사전 요구사항

* Docker 설치 (19.03+)
* Docker Compose 설치 (1.27+)
* Git 클라이언트 설치

#### 배포 단계

1. 저장소 복제

```bash
git clone https://github.com/username/project.git
cd project
```

2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 프로덕션 환경에 맞게 설정
```

3. Docker Compose로 빌드 및 실행

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

4. 마이그레이션 실행

```bash
docker-compose -f docker-compose.prod.yml exec backend python migrate.py
```

### 수동 배포

#### 사전 요구사항

* Python 3.8+
* Node.js 14+
* Nginx 또는 Apache
* PostgreSQL 12+

#### 백엔드 배포

1. 저장소 복제 및 의존성 설치

```bash
git clone https://github.com/username/project.git
cd project

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 프로덕션 환경에 맞게 설정
```

3. Gunicorn 또는 uWSGI 설정

```bash
# Gunicorn 예시
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

#### 프론트엔드 배포

1. 의존성 설치 및 빌드

```bash
cd frontend
npm install
npm run build
```

2. Nginx 설정으로 정적 파일 제공

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        root /path/to/project/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## CI/CD 파이프라인

### GitHub Actions

```yaml
name: CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /path/to/project
            git pull
            docker-compose -f docker-compose.prod.yml up -d --build
```

## 모니터링 및 로깅

### 로그 위치

* **애플리케이션 로그**: `/var/log/app/`
* **Nginx 로그**: `/var/log/nginx/`
* **Docker 로그**: `docker-compose logs -f`

### 모니터링 도구

* Prometheus + Grafana: 시스템 및 애플리케이션 메트릭 모니터링
* ELK Stack: 로그 집계 및 분석

## 롤백 절차

문제가 발생한 경우 다음 단계로 롤백합니다:

1. 이전 버전으로 돌아가기

```bash
git checkout <previous-tag>
docker-compose -f docker-compose.prod.yml up -d --build
```

2. 데이터베이스 롤백 (필요한 경우)

```bash
docker-compose -f docker-compose.prod.yml exec backend python migrate.py downgrade
```
