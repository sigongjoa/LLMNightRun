/**
 * MCP 터미널 클라이언트 (비활성화됨)
 * 
 * 이 파일은 LLMNightRun에서 터미널 기능을 비활성화하기 위해 수정되었습니다.
 */

class MCPTerminalClient {
  constructor() {
    console.log("[MCP] 터미널 기능이 비활성화되었습니다.");
  }

  async createSession() {
    return "dummy-session";
  }

  async deleteSession() {
    return true;
  }

  async executeCommand() {
    return {
      stdout: "터미널 기능이 비활성화되었습니다.",
      stderr: "",
      exit_code: 0
    };
  }

  async workingDirectory() {
    return "D:\\";
  }

  async connectWebSocket() {
    console.log("[MCP] 터미널 WebSocket 기능이 비활성화되었습니다.");
    return false;
  }

  disconnectWebSocket() {}
}

// 더미 인스턴스 생성
const MCPTerminalInstance = new MCPTerminalClient();

// 브라우저 환경에서만 전역 객체에 등록
if (typeof window !== 'undefined') {
  window.MCPTerminal = MCPTerminalInstance;
  window.MCP = window.MCP || {};
  window.MCP.terminal = MCPTerminalInstance;
}

export default MCPTerminalInstance;
