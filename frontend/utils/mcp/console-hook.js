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
   * MCP 서버 연결 해제
   */
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    this.connected = false;
    this._unhookConsole();
    this.sessionId = null;
  }

  /**
   * 코드 실행 요청
   * @param {string} code - 실행할 JavaScript 코드
   * @returns {Promise<any>} 실행 결과
   */
  async execute(code) {
    if (!this.isConnected()) {
      throw new Error('연결되지 않았습니다. execute를 호출하기 전에 connect() 호출이 필요합니다.');
    }

    // 요청 ID 생성
    const requestId = this._generateRequestId();
    
    // 요청 메시지 생성
    const message = {
      type: 'execute',
      requestId,
      code,
      timestamp: new Date().toISOString()
    };
    
    // 응답 대기를 위한 프라미스 생성
    const resultPromise = new Promise((resolve, reject) => {
      this.pendingExecutions.set(requestId, { resolve, reject });
      
      // 타임아웃 처리
      setTimeout(() => {
        if (this.pendingExecutions.has(requestId)) {
          this.pendingExecutions.delete(requestId);
          reject(new Error('코드 실행 타임아웃'));
        }
      }, 30000); // 30초 타임아웃
    });
    
    // 메시지 전송
    this.socket.send(JSON.stringify(message));
    
    // 결과 반환
    return resultPromise;
  }

  /**
   * WebSocket에서 받은 메시지 처리
   * @private
   * @param {MessageEvent} event - WebSocket 메시지 이벤트
   */
  _handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      
      // 실행 결과 처리
      if (message.type === 'execute_result' && message.requestId) {
        const pending = this.pendingExecutions.get(message.requestId);
        
        if (pending) {
          this.pendingExecutions.delete(message.requestId);
          
          if (message.error) {
            pending.reject(new Error(message.error));
          } else {
            pending.resolve(message.result);
          }
        }
      }
    } catch (error) {
      console.error('[MCP] 메시지 처리 오류:', error);
    }
  }

  /**
   * 콘솔 메서드 후킹
   * @private
   */
  _hookConsole() {
    // 이미 후킹된 경우 건너뜀
    if (console.__mcp_hooked__) {
      return;
    }
    
    // 후킹 플래그 설정
    console.__mcp_hooked__ = true;
    
    // 각 콘솔 메서드 후킹
    for (const method of Object.keys(this.originalConsole)) {
      console[method] = (...args) => {
        // 원본 메서드 호출
        this.originalConsole[method](...args);
        
        // MCP 서버로 로그 전송
        this._sendLog(method, args);
      };
    }
  }
  
  /**
   * 콘솔 후킹 해제
   * @private
   */
  _unhookConsole() {
    if (!console.__mcp_hooked__) {
      return;
    }
    
    // 각 콘솔 메서드 원복
    for (const method of Object.keys(this.originalConsole)) {
      console[method] = this.originalConsole[method];
    }
    
    // 후킹 플래그 제거
    delete console.__mcp_hooked__;
  }
  
  /**
   * 로그를 MCP 서버로 전송
   * @private
   * @param {string} method - 콘솔 메서드 이름 (log, warn, error 등)
   * @param {Array<any>} args - 콘솔 메서드 인자
   */
  _sendLog(method, args) {
    // 연결되지 않은 경우 버퍼에 추가
    if (!this.isConnected()) {
      if (this.buffer.length < this.maxBufferSize) {
        this.buffer.push({ method, args, timestamp: new Date().toISOString() });
      }
      return;
    }
    
    try {
      // 로그 메시지 생성
      const logMessage = {
        type: 'console',
        method,
        args: args.map(arg => this._serializeArg(arg)),
        timestamp: new Date().toISOString()
      };
      
      // 메시지 전송
      this.socket.send(JSON.stringify(logMessage));
    } catch (error) {
      // 오류 발생 시 원본 콘솔로 출력 (무한 재귀 방지를 위해 originalConsole 사용)
      this.originalConsole.error('[MCP] 로그 전송 실패:', error);
    }
  }
  
  /**
   * 인자 직렬화
   * @private
   * @param {any} arg - 직렬화할 인자
   * @returns {any} 직렬화된 인자
   */
  _serializeArg(arg) {
    try {
      // 에러 객체 변환
      if (arg instanceof Error) {
        return {
          __type__: 'Error',
          name: arg.name,
          message: arg.message,
          stack: arg.stack
        };
      }
      
      // 기본 타입은 그대로 전달
      if (arg === null || arg === undefined || 
          typeof arg === 'string' || 
          typeof arg === 'number' || 
          typeof arg === 'boolean') {
        return arg;
      }
      
      // 기타 객체는 JSON으로 변환하여 전달
      return JSON.parse(JSON.stringify(arg, (key, value) => {
        if (value instanceof Function) {
          return '[Function]';
        }
        if (value instanceof RegExp) {
          return value.toString();
        }
        return value;
      }));
    } catch (error) {
      // 직렬화 실패 시 문자열로 변환
      return String(arg);
    }
  }
  
  /**
   * 버퍼에 있는 로그 메시지 전송
   * @private
   */
  _flushBuffer() {
    if (!this.isConnected() || this.buffer.length === 0) {
      return;
    }
    
    // 버퍼의 메시지들을 하나씩
    for (const logEntry of this.buffer) {
      this._sendLog(logEntry.method, logEntry.args);
    }
    
    // 버퍼 비우기
    this.buffer = [];
  }
  
  /**
   * 세션 ID 생성
   * @private
   * @returns {string} 생성된 세션 ID
   */
  _generateSessionId() {
    return 'console-' + Math.random().toString(36).substring(2, 15);
  }
  
  /**
   * 요청 ID 생성
   * @private
   * @returns {string} 생성된 요청 ID
   */
  _generateRequestId() {
    return Math.random().toString(36).substring(2, 15);
  }
  
  /**
   * 재연결 일정 예약
   * @private
   */
  _scheduleReconnect() {
    // 최대 시도 횟수 초과 시 중단
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.originalConsole.error('[MCP] 재연결 시도 횟수 초과');
      return;
    }
    
    // 기존 타이머 취소
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    // 백오프 계산 (초기 1초, 이후 지수적으로 증가)
    const backoff = Math.min(30000, Math.pow(2, this.reconnectAttempts) * 1000);
    this.reconnectAttempts++;
    
    this.originalConsole.log(`[MCP] ${backoff/1000}초 후 재연결 시도 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    // 재연결 타이머 설정
    this.reconnectTimeout = setTimeout(() => {
      if (!this.connected && !this.connecting) {
        this.connect(this.sessionId).catch(error => {
          this.originalConsole.error('[MCP] 재연결 실패:', error);
        });
      }
    }, backoff);
  }
}

// 브라우저 환경인 경우 전역 객체에 노출
let BrowserConsoleHookInstance = null;

if (typeof window !== 'undefined') {
  // 기본 URL을 사용하여 인스턴스 생성
  const defaultWsUrl = window.location.origin.replace(/^http/, 'ws') + '/mcp/ws/console/';
  BrowserConsoleHookInstance = new BrowserConsoleHook(defaultWsUrl);
  window.BrowserConsoleHook = BrowserConsoleHookInstance;
}

// 모듈 내보내기
export default BrowserConsoleHookInstance || BrowserConsoleHook;
