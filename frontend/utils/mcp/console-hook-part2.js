  /**
   * 연결 해제
   */
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket && (this.connected || this.connecting)) {
      try {
        this.socket.close();
      } catch (e) {
        console.error('[MCP] 웹소켓 연결 해제 중 오류:', e);
      }
      this.connected = false;
      this.connecting = false;
      this._unhookConsole();
    }
  }

  /**
   * 자바스크립트 코드 실행
   * @param {string} code - 실행할 자바스크립트 코드
   * @param {number} timeout - 제한 시간 (밀리초)
   * @returns {Promise<any>} 실행 결과
   */
  async executeCode(code, timeout = 30000) {
    if (!this.connected) {
      try {
        await this.connect();
      } catch (error) {
        throw new Error('MCP 서버에 연결되어 있지 않습니다');
      }
    }

    // 코드 유효성 검사
    if (!code || !code.trim()) {
      return Promise.reject(new Error('실행할 코드가 비어 있습니다'));
    }

    const executionId = this._generateExecutionId();

    // 실행 요청 메시지 전송
    try {
      this.socket.send(JSON.stringify({
        type: 'execute',
        execution_id: executionId,
        code,
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      return Promise.reject(new Error(`실행 요청 전송 실패: ${error.message}`));
    }

    // 응답을 기다리기 위한 Promise 생성
    const resultPromise = new Promise((resolve, reject) => {
      // 실행 요청 저장
      this.pendingExecutions.set(executionId, { resolve, reject });

      // 타임아웃 처리
      setTimeout(() => {
        if (this.pendingExecutions.has(executionId)) {
          this.pendingExecutions.delete(executionId);
          reject(new Error(`자바스크립트 실행 시간 초과 (${timeout}ms)`));
        }
      }, timeout);
    });

    return resultPromise;
  }

  /**
   * 웹소켓 메시지 처리
   * @private
   * @param {MessageEvent} event - 웹소켓 메시지 이벤트
   */
  _handleMessage(event) {
    try {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'execution_result':
          this._handleExecutionResult(message);
          break;
        case 'error':
          this._handleError(message);
          break;
        default:
          console.log('[MCP] 알 수 없는 메시지 유형:', message.type);
      }
    } catch (error) {
      console.error('[MCP] 메시지 처리 중 오류:', error);
    }
  }
