# MCP (Model Context Protocol) 브라우저 콘솔 및 터미널 후킹 기능

이 프로젝트는 LLMNightRun 플랫폼에 브라우저 콘솔과 윈도우 터미널을 후킹하여 MCP 서버와 통신하는 기능을 구현합니다.

## 기능

### 브라우저 콘솔 후킹
- 브라우저의 `console.log`, `console.warn`, `console.error` 등 콘솔 메서드를 후킹하여 로그를 MCP 서버로 전송
- 웹 애플리케이션에서 발생한 JavaScript 오류 캡처 및 전송
- 브라우저에서 JavaScript 코드를 원격으로 실행하고 결과를 받을 수 있는 기능

### 터미널 후킹
- 명령어 실행 및 결과 조회
- 안전한 명령어 검증 및 제한된 명령어만 실행 가능
- WebSocket을 통한 실시간 출력 및 상태 업데이트

## 구성 요소

### 백엔드
- **MCP 기본 모듈**: `backend/mcp/__init__.py`
- **WebSocket 서버**: `backend/mcp/websocket.py`
- **브라우저 콘솔 도구**: `backend/mcp/tools/browser_console.py`
- **터미널 도구**: `backend/mcp/tools/terminal.py`
- **함수 구현**: `backend/mcp/function_implementations.py`

### 프론트엔드
- **브라우저 콘솔 후킹 유틸리티**: `frontend/utils/mcp/console-hook.js`
- **터미널 클라이언트**: `frontend/utils/mcp/terminal.js`
- **MCP 클라이언트**: `frontend/utils/mcp/index.js`
- **콘솔 UI 컴포넌트**: `frontend/components/MCP/Console.jsx`

## 실행 방법

### 백엔드 서버 실행

```bash
# 프로젝트 루트 디렉터리에서
cd D:\LLMNightRun
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 개발 서버 실행

```bash
# 프론트엔드 디렉터리에서
cd D:\LLMNightRun\frontend
npm run dev
```

## 사용 예시

### 브라우저 콘솔 후킹 사용

```javascript
// MCP 초기화 및 콘솔 후킹
import MCP from '/utils/mcp';

// 콘솔 연결
const init = async () => {
  const result = await MCP.init({
    autoConnectConsole: true
  });
  console.log('MCP 초기화 결과:', result);
};

init();

// 이제 모든 콘솔 로그가 MCP 서버로 전송됩니다
console.log('이 로그는 MCP 서버로 전송됩니다');
console.error('오류도 MCP 서버로 전송됩니다');

// 자바스크립트 코드 원격 실행
const runCode = async () => {
  try {
    const result = await MCP.console.executeCode('return document.title');
    console.log('실행 결과:', result);
  } catch (error) {
    console.error('실행 오류:', error);
  }
};

runCode();
```

### 터미널 사용

```javascript
// 터미널 세션 생성 및 명령어 실행
import MCP from '/utils/mcp';

const useTerminal = async () => {
  // 터미널 세션 생성
  const sessionId = await MCP.terminal.createSession('D:\\');
  
  // 명령어 실행
  const result = await MCP.terminal.executeCommand('dir', sessionId);
  console.log('명령어 실행 결과:', result);
  
  // 명령어 실행 기록 조회
  const history = await MCP.terminal.getHistory(sessionId);
  console.log('명령어 실행 기록:', history);
  
  // 세션 삭제
  await MCP.terminal.deleteSession(sessionId);
};

useTerminal();
```

## 보안 고려사항

- 터미널 명령어는 허용된 명령어 목록에서만 실행되도록 제한됩니다.
- 쉘 연산자(`&&`, `|`, `>` 등)는 보안상의 이유로 허용되지 않습니다.
- 모든 명령어는 실행 전에 유효성 검사를 거칩니다.
- 브라우저 콘솔 후킹은 사용자의 동의하에 활성화되어야 합니다.

## 개선된 기능

1. **강화된 오류 처리**: 모든 비동기 작업에 대해 세분화된 오류 처리 로직 추가
2. **연결 안정성 향상**: 자동 재연결 메커니즘과 로그 버퍼링 구현
3. **보안 강화**: 명령어 검증 로직 개선 및 세부 오류 메시지 제공
4. **WebSocket 관리**: 중복 연결 방지 및 세션 관리 개선
5. **클라이언트 인터페이스 확장**: 유용한 상태 확인 및 관리 메서드 추가
