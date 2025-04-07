/**
 * 브라우저 개발자 콘솔 후킹 유틸리티
 * 
 * MCP 서버와 통신하기 위해 브라우저의 console 객체 메서드를 후킹합니다.
 * WebSocket을 통해 console.log, console.warn, console.error 등의 호출을 
 * MCP 서버로 전송합니다.
 */

class BrowserConsoleHook {
  /**
   * 브라우저 콘솔 후킹 초기화
   * @param {string} serverUrl - MCP 서버 WebSocket URL (e.g., "ws://localhost:8000/mcp/ws/console/")
   */
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
    this.socket = null;
    this.sessionId = null;
    this.connected = false;
    this.originalConsole = {
      log: console.log,
      warn: console.warn,
      error: console.error,
      info: console.info,
      debug: console.debug
    };
    this.pendingExecutions = new Map();
    this.buffer = [];
    this.connecting = false;
    this.maxBufferSize = 1000;
    this.reconnectTimeout = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
  }

  /**
   * 연결 상태 확인
   * @returns {boolean} 연결 상태
   */
  isConnected() {
    return this.connected && this.socket && this.socket.readyState === WebSocket.OPEN;
  }
  
  /**
   * 세션 ID 조회
   * @returns {string|null} 세션 ID
   */
  getSessionId() {
    return this.sessionId;
  }

  /**
   * MCP 서버에 연결
   * @param {string} sessionId - 세션 ID (없으면 생성됨)
   * @returns {Promise<string>} 세션 ID
   */
  async connect(sessionId = null) {
    if (this.connected || this.connecting) {
      return this.sessionId;
    }

    this.connecting = true;
    this.sessionId = sessionId || this._generateSessionId();
    const wsUrl = `${this.serverUrl}${this.sessionId}`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.connected = true;
        this.connecting = false;
        this.reconnectAttempts = 0;
        this._flushBuffer();
        this._hookConsole();
        console.log(`[MCP] 브라우저 콘솔 후킹이 활성화되었습니다 (세션 ID: ${this.sessionId})`);
      };

      this.socket.onclose = () => {
        this.connected = false;
        this._unhookConsole();
        console.log('[MCP] 브라우저 콘솔 후킹이 비활성화되었습니다');
        this._scheduleReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('[MCP] 웹소켓 오류:', error);
      };

      this.socket.onmessage = (event) => {
        this._handleMessage(event);
      };

      // 소켓 연결 대기
      await new Promise((resolve, reject) => {
        // 연결 성공 시 콜백 설정
        const onOpenHandler = () => {
          this.socket.removeEventListener('open', onOpenHandler);
          resolve();
        };
        this.socket.addEventListener('open', onOpenHandler);

        // 연결 실패 시 콜백 설정
        const onErrorHandler = (error) => {
          this.socket.removeEventListener('error', onErrorHandler);
          reject(error);
        };
        this.socket.addEventListener('error', onErrorHandler);

        // 연결 시간 초과 처리
        setTimeout(() => {
          this.socket.removeEventListener('open', onOpenHandler);
          this.socket.removeEventListener('error', onErrorHandler);
          reject(new Error('WebSocket connection timeout'));
        }, 5000);
      });

      return this.sessionId;
    } catch (error) {
      this.connecting = false;
      console.error('[MCP] 브라우저 콘솔 WebSocket 연결 실패:', error);
      this._scheduleReconnect();
      throw error;
    }
  }

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
        case 'connected':
          console.log(`[MCP] 서버 연결 확인됨: ${message.session_id}`);
          break;
        default:
          console.log('[MCP] 알 수 없는 메시지 유형:', message.type);
      }
    } catch (error) {
      console.error('[MCP] 메시지 처리 중 오류:', error);
    }
  }

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

      if (this.connected && this.socket && this.socket.readyState === WebSocket.OPEN) {
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
