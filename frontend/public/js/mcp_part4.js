    /**
     * 버퍼에 있는 메시지 전송
     * @private
     */
    _flushBuffer() {
      if (!this.connected || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
        return;
      }

      while (this.buffer.length > 0) {
        const message = this.buffer.shift();
        try {
          this.socket.send(JSON.stringify(message));
        } catch (error) {
          this.originalConsole.error('[MCP] 버퍼 메시지 전송 중 오류:', error);
          break;
        }
      }
    }

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

  /**
   * MCP 터미널 클라이언트 클래스
   */
  class MCPTerminalClient {
    /**
     * MCP 터미널 클라이언트 초기화
     * @param {string} baseUrl - MCP 서버 API 기본 URL
     * @param {string} wsBaseUrl - MCP 서버 WebSocket 기본 URL
     */
    constructor(baseUrl, wsBaseUrl) {
      this.baseUrl = baseUrl || '/mcp/';
      if (!this.baseUrl.endsWith('/')) {
        this.baseUrl += '/';
      }
      
      this.wsBaseUrl = wsBaseUrl || ((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + 
                      window.location.host + '/mcp/ws/');
      if (!this.wsBaseUrl.endsWith('/')) {
        this.wsBaseUrl += '/';
      }
      
      this.activeSession = null;
      this.socket = null;
      this.connected = false;
      this.messageHandlers = new Map();
      this.messageId = 0;
    }
