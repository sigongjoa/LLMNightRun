  /**
   * 콘솔 원래 메서드로 복원
   * @private
   */
  _unhookConsole() {
    console.log = this.originalConsole.log;
    console.warn = this.originalConsole.warn;
    console.error = this.originalConsole.error;
    console.info = this.originalConsole.info;
    console.debug = this.originalConsole.debug;
  }

  /**
   * 로그 메시지 전송
   * @private
   * @param {string} level - 로그 레벨
   * @param {Array<any>} args - 로그 인자
   */
  _sendLogMessage(level, args) {
    try {
      // 인자를 문자열로 변환
      const message = args.map(arg => {
        if (arg === undefined) return 'undefined';
        if (arg === null) return 'null';
        if (typeof arg === 'object') {
          try {
            return JSON.stringify(arg);
          } catch (e) {
            return String(arg);
          }
        }
        return String(arg);
      }).join(' ');

      const logMessage = {
        type: 'log',
        level,
        message,
        timestamp: new Date().toISOString(),
        source: 'console'
      };

      if (this.connected && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify(logMessage));
      } else {
        // 연결되지 않은 경우 버퍼에 추가
        this._addToBuffer(logMessage);
      }
    } catch (error) {
      // 원래 console.error을 사용하여 오류 로깅
      this.originalConsole.error('[MCP] 로그 메시지 전송 중 오류:', error);
    }
  }

  /**
   * 메시지를 버퍼에 추가
   * @private
   * @param {object} message - 버퍼에 추가할 메시지
   */
  _addToBuffer(message) {
    this.buffer.push(message);
    // 버퍼 크기 제한
    if (this.buffer.length > this.maxBufferSize) {
      this.buffer.shift();
    }
  }

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
