# LLMNightRun Frontend

LLMNightRun의 프론트엔드 애플리케이션입니다. Next.js와 Material-UI를 기반으로 구축되었습니다.

## 주요 변경사항 (2025-04-09 업데이트)

### 프로젝트 구조 개선
- 소스 코드를 src/ 디렉토리로 이동하여 구조화
- 기능별 폴더 구조 도입 (api, components, hooks, contexts 등)
- 백엔드 태그 기준(core, agent, data, system)으로 코드 재구성

### 의존성 업데이트
- Next.js, React, Material-UI 등 패키지 최신 버전으로 업데이트
- React Query 도입으로 서버 상태 관리 개선
- Zustand 도입으로 클라이언트 상태 관리 개선

### API 레이어 개선
- 기능별 API 모듈 분리
- 타입 정의 개선 및 에러 처리 강화
- 백엔드 v2 API 지원 추가

### 커스텀 훅 도입
- 기능별 커스텀 훅으로 비즈니스 로직 캡슐화
- React Query 활용한 데이터 캐싱 및 동기화
- 코드 재사용성 향상

### 컴포넌트 구조 개선
- 레이아웃 컴포넌트 재구성
- 재사용 가능한 UI 컴포넌트 개발
- 오류 처리 컴포넌트 추가

### 성능 최적화
- 코드 스플리팅 및 지연 로딩 적용
- 메모이제이션을 통한 불필요한 리렌더링 방지
- Next.js 기능 활용 최적화

### 테마 및 스타일 개선
- 다크 모드 지원 추가
- 일관된 스타일 시스템 적용
- 반응형 디자인 강화

## 프로젝트 구조

```
frontend/
├── .next/                # Next.js 빌드 디렉토리
├── node_modules/         # npm 패키지
├── public/               # 정적 파일
├── src/                  # 소스 코드
│   ├── api/              # API 모듈
│   │   ├── core/         # 핵심 기능 API (질문, 응답, 코드)
│   │   ├── agent/        # 에이전트 관련 API
│   │   ├── data/         # 데이터 관리 API
│   │   ├── system/       # 시스템 관리 API
│   │   └── index.ts      # API 모듈 내보내기
│   │
│   ├── components/       # React 컴포넌트
│   │   ├── core/         # 핵심 기능 컴포넌트
│   │   ├── agent/        # 에이전트 관련 컴포넌트
│   │   ├── data/         # 데이터 관리 컴포넌트
│   │   ├── system/       # 시스템 관리 컴포넌트
│   │   ├── layout/       # 레이아웃 컴포넌트
│   │   ├── ui/           # 공통 UI 컴포넌트
│   │   └── index.ts      # 컴포넌트 내보내기
│   │
│   ├── contexts/         # React 컨텍스트
│   ├── hooks/            # 커스텀 훅
│   ├── pages/            # Next.js 페이지
│   ├── store/            # 상태 관리 저장소
│   ├── styles/           # 스타일 및 테마
│   ├── types/            # TypeScript 타입 정의
│   └── utils/            # 유틸리티 함수
│
├── .env.local            # 환경 변수
├── .gitignore            # Git 무시 파일
├── jest.config.js        # Jest 설정
├── next.config.js        # Next.js 설정
├── package.json          # npm 패키지 정보
├── README.md             # 프로젝트 문서
└── tsconfig.json         # TypeScript 설정
```

## 설치 및 실행

### 개발 환경 설정

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 빌드 및 배포

```bash
# 프로덕션 빌드
npm run build

# 프로덕션 서버 실행
npm run start
```

### 테스트

```bash
# 단위 테스트 실행
npm test

# 테스트 감시 모드
npm run test:watch

# E2E 테스트 실행
npm run cypress
```

## 주요 기능

- **질문 & 응답**: 다양한 LLM에 질문하고 응답 관리
- **코드 관리**: 코드 스니펫 및 템플릿 관리
- **에이전트**: 자동화 에이전트 기능
- **데이터 관리**: 인덱싱 및 내보내기 기능
- **GitHub 연동**: GitHub 저장소 연동
- **설정**: 시스템 설정 관리

## 백엔드 연결

기본적으로 `http://localhost:8000`에서 실행 중인 백엔드 API를 사용합니다. 다른 백엔드 URL을 사용하려면 `.env.local` 파일에서 `NEXT_PUBLIC_API_URL`을 수정하세요.

## 기여

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치를 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다
