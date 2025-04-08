# LLMNightRun

## 소개

LLMNightRun은 멀티 LLM 통합 자동화 플랫폼입니다. 여러 LLM(Large Language Model)을 효율적으로 통합하고 관리하며, 개발 워크플로우를 자동화하는 도구입니다.

## 주요 기능

- **멀티 LLM 연동**: 다양한 LLM 서비스와 연동하여 최적의 결과 제공
- **코드 생성 및 관리**: 프롬프트 기반으로 코드 생성 및 관리
- **에이전트 자동화**: 반복적인 작업을 에이전트를 통해 자동화
- **인덱싱 및 검색**: 코드와 문서의 효율적인 인덱싱 및 검색
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

### 환경 설정

1. `.env` 파일을 생성하여 필요한 환경 변수 설정
2. LLM API 키 설정 (OpenAI, Anthropic 등)
3. 데이터베이스 연결 설정

### 실행

백엔드와 프론트엔드를 각각 실행:

```bash
# 백엔드 실행
python -m run_backend.py

# 프론트엔드 실행
cd frontend
npm run dev
```

## 프로젝트 구조

```
LLMNightRun/
├── backend/            # 백엔드 애플리케이션 코드
│   ├── api/            # API 엔드포인트
│   ├── services/       # 비즈니스 로직
│   ├── models/         # 데이터 모델
│   └── ...
├── frontend/           # 프론트엔드 애플리케이션 코드
│   ├── components/     # 리액트 컴포넌트
│   ├── pages/          # 페이지 정의
│   └── ...
├── docs_generator/     # 문서 생성 시스템
├── scripts/            # 유틸리티 스크립트
└── ...
```

## 기술 스택

- **백엔드**: FastAPI, Python
- **프론트엔드**: Next.js, React, TypeScript
- **데이터베이스**: SQLite/PostgreSQL
- **LLM 통합**: OpenAI API, Anthropic API, Hugging Face, 로컬 LLM
- **문서화**: Markdown, 자동화된 도구

## 문서화

자세한 문서는 아래를 참조하세요:

- [API 문서](docs/API.md)
- [아키텍처 개요](docs/ARCHITECTURE.md)
- [개발 가이드](docs/DEVELOPMENT.md)
- [배포 가이드](docs/DEPLOYMENT.md)

## 기여하기

프로젝트에 기여하고 싶으신 분들은 다음 단계를 참고하세요:

1. 저장소를 포크하세요.
2. 기능 브랜치를 생성하세요 (`git checkout -b feature/amazing-feature`).
3. 변경사항을 커밋하세요 (`git commit -m 'Add amazing feature'`).
4. 브랜치에 푸시하세요 (`git push origin feature/amazing-feature`).
5. Pull Request를 생성하세요.

## 라이선스

이 프로젝트는 [LICENSE] 라이선스 하에 배포됩니다.

## 연락처

프로젝트 관리자: [이메일]

GitHub: [저장소 URL]
