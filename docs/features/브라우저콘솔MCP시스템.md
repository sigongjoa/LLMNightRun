# 브라우저 콘솔 MCP(Memory-Command-Process) 시스템

## 개요
브라우저 콘솔 MCP 시스템은 웹 개발 환경에서 브라우저 콘솔(console.log, console.error 등)에 출력되는 로그, 경고, 오류 메시지를 자동으로 수집하여 LLM에 전달하고, 실시간 분석 결과를 제공하는 시스템입니다. 개발자가 디버깅 및 문제 해결 과정에서 AI의 도움을 실시간으로 활용할 수 있도록 설계되었습니다.

## 구성 요소

### 백엔드 구성 요소
- `cli-mcp-server/src/cli_mcp_server/browser_console_mcp.py`: 브라우저 콘솔 MCP 서버
- `cli-mcp-server/src/cli_mcp_server/llm_integrations/`: LLM 서비스 연동 모듈
  - `cli-mcp-server/src/cli_mcp_server/llm_integrations/lm_studio.py`: LM Studio 연동
  - `cli-mcp-server/src/cli_mcp_server/llm_integrations/openai.py`: OpenAI 연동
  - `cli-mcp-server/src/cli_mcp_server/llm_integrations/claude.py`: Claude 연동

### 프론트엔드 구성 요소
- `browser-console-interceptor.js`: 브라우저의 console 객체 메소드 후킹
- `mcp-client.js`: MCP 서버와 통신하는 클라이언트 
- `feedback-overlay.js`: 분석 결과를 표시하는 UI 컴포넌트

### API 엔드포인트

#### 로그 분석 요청
```
POST /analyze_log
```
**요청 본문:**
```json
{
  "type": "error",
  "message": "TypeError: Cannot read property 'value' of undefined",
  "stack": "at handleSubmit (app.js:42)\n  at HTMLFormElement.onclick (index.html:25)",
  "timestamp": "2025-04-09T14:32:45.123Z",
  "context": {
    "browser": "Chrome 125.0.0",
    "url": "http://localhost:3000/dashboard",
    "component": "UserForm"
  }
}
```
**응답:**
```json
{
  "status": "success",
  "analysis": {
    "issue": "DOM 요소 접근 전 유효성 검증 누락",
    "probable_cause": "form 요소 내 value 속성에 접근하기 전에 해당 요소의 존재 여부를 확인하지 않음",
    "suggestion": "handleSubmit 함수에서 요소 존재 여부를 확인하는 조건문 추가 필요",
    "code_example": "if (formElement && formElement.value) { /* 로직 수행 */ }"
  }
}
```

#### WebSocket 연결
```
WebSocket /ws
```
브라우저 콘솔 로그를 실시간으로 서버에 전송하고 분석 결과를 수신하기 위한 WebSocket 엔드포인트

## 주요 기능

### 콘솔 로그 수집
- **자동 인터셉트**: 모든 console.log, console.error, console.warn 호출 자동 수집
- **컨텍스트 보존**: 스택 트레이스, 실행 환경, 관련 변수 값 포함
- **필터링 기능**: 중요하지 않은 로그 필터링 옵션

### LLM 연동
- **다중 LLM 지원**: LM Studio, OpenAI, Claude 등 다양한 LLM 서비스 지원
- **컨텍스트 최적화**: 개발 환경에 맞는 프롬프트 최적화
- **캐싱 및 최적화**: 유사한 오류에 대한 분석 결과 캐싱으로 응답 시간 단축

### 실시간 피드백
- **인라인 피드백**: 콘솔 로그 바로 옆에 분석 결과 표시
- **오버레이 UI**: 독립적인 오버레이 창에서 상세 분석 정보 제공
- **코드 제안**: 문제 해결을 위한 코드 수정 제안

## 사용 예시

### 브라우저 측 설정
```javascript
// 웹 애플리케이션에 MCP 클라이언트 통합
import { initConsoleMCP } from 'browser-console-mcp';

// MCP 시스템 초기화
initConsoleMCP({
  serverUrl: 'http://localhost:5000',
  enableWebSocket: true,
  captureErrors: true,
  captureWarnings: true,
  captureLogLevel: 'info',
  showOverlay: true,
  filterPatterns: ['[HMR]', '[webpack]'] // 무시할 로그 패턴
});

// 이제 모든 콘솔 출력이 자동으로 MCP 서버로 전송됨
console.log('사용자 로그인 시도'); // MCP에 의해 인터셉트되어 분석
console.error('input value가 undefined'); // 실시간 분석 결과 제공
```

### 백엔드 서버 설정
```python
from cli_mcp_server.browser_console_mcp import BrowserConsoleMCPServer, LMStudioConfig

# LM Studio 설정
lm_config = LMStudioConfig(
    api_url="http://localhost:1234/v1/chat/completions",
    model="mistral-7b-instruct",
    system_prompt="당신은 JavaScript와 웹 개발 전문가입니다. 브라우저 콘솔 로그를 분석하여 문제의 원인과 해결 방법을 제안해주세요.",
    temperature=0.3,
    max_tokens=512
)

# MCP 서버 시작
server = BrowserConsoleMCPServer(lm_studio_config=lm_config)

# FastAPI 앱 실행
import uvicorn
uvicorn.run(server.app, host="0.0.0.0", port=5000)
```

## 실전 시나리오

### 시나리오 1: React 컴포넌트 오류 디버깅
React 애플리케이션에서 상태 업데이트 전 DOM 접근 시도로 인한 오류가 발생했을 때:

```
Console: "TypeError: Cannot read properties of null (reading 'value')"
Stack: "at handleSubmit (UserForm.jsx:45)"
```

**MCP 분석 결과:**
```
분석: React 컴포넌트에서 DOM 요소 직접 접근 문제
원인: useRef 또는 상태 변수가 초기화되기 전 접근 시도
해결책: 
1. useRef 사용 시 null 체크 추가: if (inputRef.current) { ... }
2. 상태 관리 개선: 제어 컴포넌트 사용으로 변환
3. useEffect 훅 내에서 DOM 조작 코드 이동
```

### 시나리오 2: 비동기 데이터 처리 오류
API 응답 처리 중 발생한 오류:

```
Console: "Uncaught (in promise) TypeError: response.data is undefined"
Context: { component: "UserDashboard", url: "/api/users" }
```

**MCP 분석 결과:**
```
분석: API 응답 구조 예상 불일치 또는 에러 응답 처리 누락
원인: 
1. API가 예상된 { data: [...] } 형식이 아닌 다른 형식 반환
2. 에러 케이스에 대한 적절한 처리 부재

해결책:
1. try/catch 블록 추가 및 response 구조 검증
2. 코드 예시:
   try {
     const response = await fetch('/api/users');
     const data = await response.json();
     
     // 데이터 유효성 검증
     const items = data?.data || [];
     setUsers(items);
   } catch (error) {
     console.error('Failed to fetch users:', error);
     setError('사용자 데이터를 불러오는데 실패했습니다');
   }
```

## 고급 기능

### 패턴 학습 및 프로젝트 맞춤화
- **반복 패턴 인식**: 같은 유형의 오류 패턴 학습 및 자동 인식
- **프로젝트 컨텍스트 인식**: 프로젝트 구조와 코드베이스 맥락 이해
- **팀별 설정**: 개발팀 코딩 스타일과 관행에 맞는 제안 생성

### 생산성 향상 기능
- **자동 수정 제안**: 일반적인 오류에 대한 자동 수정 코드 제공
- **문서 링크**: 관련 문서, 스택오버플로우 질문 등 참고 자료 링크
- **통계 및 트렌드**: 가장 자주 발생하는 오류 유형 분석 및 리포트

### 보안 및 데이터 관리
- **민감 정보 필터링**: 개인 정보, API 키 등 자동 수정 및 필터링
- **로컬 처리 옵션**: 민감한 개발 환경을 위한 전체 로컬 실행 모드
- **데이터 보존 정책**: 로그 보존 기간 및 익명화 설정
