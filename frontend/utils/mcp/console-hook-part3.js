  /**
   * 자바스크립트 실행 결과 처리
   * @private
   * @param {object} message - 실행 결과 메시지
   */
  _handleExecutionResult(message) {
    const executionId = message.execution_id;
    if (this.pendingExecutions.has(executionId)) {
      const { resolve } = this.pendingExecutions.get(executionId);
      this.pendingExecutions.delete(executionId);

      if (message.status === 'success') {
        resolve(message.result);
      } else {
        resolve({
          error: message.error,
          result: null,
          status: 'error'
        });
      }
    }
  }

  /**
   * 오류 메시지 처리
   * @private
   * @param {object} message - 오류 메시지
   */
  _handleError(message) {
    const executionId = message.execution_id;
    if (executionId && this.pendingExecutions.has(executionId)) {
      const { reject } = this.pendingExecutions.get(executionId);
      this.pendingExecutions.delete(executionId);
      reject(new Error(message.message || '알 수 없는 오류'));
    } else {
      console.error('[MCP] 오류:', message.message);
    }
  }

  /**
   * 콘솔 메서드 후킹
   * @private
   */
  _hookConsole() {
    // console.log 후킹
    console.log = (...args) => {
      this._sendLogMessage('info', args);
      this.originalConsole.log(...args);
    };

    // console.warn 후킹
    console.warn = (...args) => {
      this._sendLogMessage('warn', args);
      this.originalConsole.warn(...args);
    };

    // console.error 후킹
    console.error = (...args) => {
      this._sendLogMessage('error', args);
      this.originalConsole.error(...args);
    };

    // console.info 후킹
    console.info = (...args) => {
      this._sendLogMessage('info', args);
      this.originalConsole.info(...args);
    };

    // console.debug 후킹
    console.debug = (...args) => {
      this._sendLogMessage('debug', args);
      this.originalConsole.debug(...args);
    };

    // 전역 오류 후킹
    window.addEventListener('error', (event) => {
      this._sendLogMessage('error', [`Uncaught ${event.error}: ${event.message} at ${event.filename}:${event.lineno}:${event.colno}`]);
    });

    // Promise 오류 후킹
    window.addEventListener('unhandledrejection', (event) => {
      this._sendLogMessage('error', [`Unhandled Promise Rejection: ${event.reason}`]);
    });
  }
