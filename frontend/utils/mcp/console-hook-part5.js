  /**
   * 자동 재연결 스케줄링
   * @private
   */
  _scheduleReconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.originalConsole.error(`[MCP] 최대 재연결 시도 횟수 (${this.maxReconnectAttempts})를 초과했습니다`);
      return;
    }

    // 지수 백오프로 재연결 대기 시간 계산
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    this.reconnectTimeout = setTimeout(async () => {
      this.originalConsole.log(`[MCP] 재연결 시도 #${this.reconnectAttempts}...`);
      try {
        await this.connect(this.sessionId);
      } catch (error) {
        this.originalConsole.error('[MCP] 재연결 실패:', error);
      }
    }, delay);
  }

  /**
   * 세션 ID 생성
   * @private
   * @returns {string} 세션 ID
   */
  _generateSessionId() {
    return 'console-' + Math.random().toString(36).substring(2, 15);
  }

  /**
   * 실행 ID 생성
   * @private
   * @returns {string} 실행 ID
   */
  _generateExecutionId() {
    return 'exec-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7);
  }
}

// 전역 인스턴스 생성 (기본 MCP 서버 URL 사용)
const defaultMCPServerUrl = window.location.origin.replace(/^http/, 'ws') + '/mcp/ws/console/';
window.MCPConsole = new BrowserConsoleHook(defaultMCPServerUrl);

// 페이지 로드 시 자동 연결 (필요한 경우)
window.addEventListener('load', () => {
  // 자동 연결이 필요한 경우 주석 해제
  // window.MCPConsole.connect();
});

// 페이지 언로드 시 연결 해제
window.addEventListener('beforeunload', () => {
  if (window.MCPConsole) {
    window.MCPConsole.disconnect();
  }
});

export default window.MCPConsole;
