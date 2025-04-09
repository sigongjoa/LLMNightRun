# LLMNightRun 프론트엔드 리팩토링 가이드

## 업데이트 내용 요약

LLMNightRun 프론트엔드가 다음과 같이 리팩토링되었습니다:

1. **프로젝트 구조 개선**
   - 소스 코드를 src/ 디렉토리로 이동하여 구조화
   - 백엔드 태그 기준(core, agent, data, system)으로 기능 분리
   - 컴포넌트, API, 훅 등을 명확하게 모듈화

2. **기술 스택 업그레이드**
   - 패키지 의존성 최신 버전으로 업데이트
   - React Query 도입으로 서버 상태 관리 개선
   - Zustand 도입으로 클라이언트 상태 관리 
   - TypeScript 타입 개선

3. **API 통신 계층 재구축**
   - 기능별 API 모듈화로 유지보수성 향상
   - 에러 처리 강화 및 표준화
   - 백엔드 v2 API 지원

4. **커스텀 훅 시스템**
   - React Query 기반 데이터 조회 및 변경 훅 개발
   - 기능별 로직 캡슐화로 코드 재사용성 강화

5. **UI/UX 개선**
   - 다크 모드 지원
   - 오류 처리 및 로딩 상태 시각화 개선
   - 일관된 디자인 시스템 적용

## 설치 및 실행 방법

1. **패키지 설치**
   ```bash
   cd frontend
   npm install
   ```

2. **개발 모드 실행**
   ```bash
   npm run dev
   ```
   개발 서버가 http://localhost:3000에서 실행됩니다.

3. **프로덕션 빌드 및 실행**
   ```bash
   npm run build
   npm run start
   ```

## 백엔드 연결 설정

백엔드 API URL 설정은 `.env.local` 파일에서 관리됩니다:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

필요한 경우 이 파일을 수정하여 다른 백엔드 URL을 지정할 수 있습니다.

## 폴더 구조 가이드

```
frontend/src/
├── api/                # API 클라이언트 모듈
│   ├── core/           # 질문, 응답, 코드 관련 API
│   ├── agent/          # 에이전트 관련 API
│   ├── data/           # 데이터 관리 API
│   ├── system/         # 시스템 관리 API
│   └── index.ts        # API 모듈 내보내기
│
├── components/         # React 컴포넌트
│   ├── core/           # 핵심 기능 컴포넌트
│   ├── agent/          # 에이전트 관련 컴포넌트
│   ├── data/           # 데이터 관리 컴포넌트
│   ├── system/         # 시스템 관리 컴포넌트
│   ├── layout/         # 레이아웃 컴포넌트
│   ├── ui/             # 공통 UI 컴포넌트
│   └── index.ts        # 컴포넌트 내보내기
│
├── contexts/           # React 컨텍스트
├── hooks/              # 커스텀 훅
├── pages/              # Next.js 페이지
├── store/              # 상태 관리 저장소
├── styles/             # 스타일 및 테마
├── types/              # TypeScript 타입 정의
└── utils/              # 유틸리티 함수
```

## 주요 변경사항 상세 설명

### 1. API 통신 계층

API 요청은 이제 기능별로 분리된 모듈을 통해 이루어집니다:

```typescript
// 예시: 질문 생성
import { QuestionApi } from '../api';
import { useCreateQuestion } from '../hooks';

// 직접 API 사용
const createQuestion = async () => {
  try {
    const result = await QuestionApi.createQuestion({ content: "질문 내용" });
    console.log(result);
  } catch (error) {
    console.error(error);
  }
};

// 훅 사용 (권장)
const { mutate: createQuestion, isLoading } = useCreateQuestion();
createQuestion(
  { content: "질문 내용" },
  {
    onSuccess: (data) => console.log(data),
    onError: (error) => console.error(error)
  }
);
```

### 2. 상태 관리 시스템

React Query와 Zustand를 활용한 상태 관리:

```typescript
// 서버 상태 관리 (React Query)
const { data: questions, isLoading } = useQuestions({ limit: 10 });

// 클라이언트 상태 관리 (향후 Zustand 구현 예정)
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
}

const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
```

### 3. 컴포넌트 시스템

공통 UI 컴포넌트를 활용하여 일관된 사용자 경험 제공:

```tsx
import { LoadingIndicator, CodeBlock, ConfirmDialog, Notification } from '../components/ui';

// 로딩 표시
{isLoading && <LoadingIndicator message="데이터 로딩 중..." />}

// 코드 블록 표시
<CodeBlock 
  code="console.log('Hello, World!');" 
  language="javascript" 
  title="예제 코드" 
/>

// 확인 대화상자
<ConfirmDialog
  open={dialogOpen}
  title="삭제 확인"
  message="정말로 이 항목을 삭제하시겠습니까?"
  onConfirm={handleDelete}
  onCancel={() => setDialogOpen(false)}
/>
```

### 4. 레이아웃 시스템

일관된 레이아웃을 위한 컴포넌트:

```tsx
import Layout from '../components/layout/Layout';

const SomePage: React.FC = () => {
  return (
    <Layout title="페이지 제목">
      {/* 페이지 내용 */}
    </Layout>
  );
};
```

### 5. 오류 처리 및 알림 시스템

전역 오류 처리 및 알림 관리:

```tsx
import { useNotification } from '../contexts';

const SomeComponent: React.FC = () => {
  const { showNotification } = useNotification();
  
  const handleAction = () => {
    try {
      // 작업 수행
      showNotification('작업이 성공적으로 완료되었습니다.', 'success');
    } catch (error) {
      showNotification(`오류 발생: ${error.message}`, 'error');
    }
  };
  
  return (
    // ...
  );
};
```

## 백엔드와의 마이그레이션 순서

1. **패키지 설치**
   ```
   npm install
   ```

2. **백엔드 실행**
   ```
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **프론트엔드 개발 서버 실행**
   ```
   npm run dev
   ```

4. **기능 테스트**
   - 메인 페이지 로드 확인
   - 질문-응답 기능 테스트
   - 에이전트 기능 테스트
   - 코드 관리 기능 테스트
   - 데이터 관리 기능 테스트

5. **문제 해결**
   - 대부분의 컴포넌트가 아직 구현 중이므로, 필요에 따라 기존 컴포넌트를 새 구조로 마이그레이션
   - 에러 로그를 확인하며 API 연결 문제 해결

## 향후 개발 계획

1. **남은 페이지 구현**
   - `/code`, `/agent`, `/data`, `/github`, `/settings` 등

2. **컴포넌트 마이그레이션**
   - 기존 컴포넌트를 새 구조로 점진적 마이그레이션

3. **테스트 추가**
   - 단위 테스트 및 통합 테스트 작성

4. **문서화**
   - 컴포넌트 문서화 (향후 Storybook 도입 고려)

## 주의사항

1. API 호출 시 백엔드 URL 확인
2. 코드를 수정할 때는 타입 안전성 유지
3. 기존 코드를 리팩토링할 때는 기능 테스트 병행
4. 현재 구현된 기능 중 일부는 백엔드 변경에 맞춰 추가 수정이 필요할 수 있음

## 문제 해결

문제가 발생한 경우 다음 순서로 디버깅:

1. 개발자 도구 콘솔 로그 확인
2. React Query DevTools로 API 요청/응답 확인
3. 백엔드 API 엔드포인트 정상 작동 확인
4. 타입 정의 불일치 확인

## 결론

이번 리팩토링으로 프론트엔드 코드의 구조가 크게 개선되었습니다. 백엔드 태그 기준으로 재구성된 코드 구조와 상태 관리 시스템 도입, 타입 개선 등을 통해 유지보수성과 확장성이 향상되었습니다. React Query와 같은 최신 라이브러리 도입으로 데이터 관리 효율성도 높아졌습니다.

리팩토링은 점진적으로 진행될 예정이며, 일부 기능은 계속해서 개선될 것입니다. 기존 코드에서 새 구조로의 마이그레이션은 기능별로 순차적으로 진행할 계획입니다.
