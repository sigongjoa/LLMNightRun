/**
 * MCP(Model Context Protocol) 클라이언트 라이브러리
 * 
 * 브라우저와 터미널에서 MCP 서버와 통신하는 기능을 제공합니다.
 * 
 * @version 1.0.0
 */
(function(global) {
  'use strict';

  /**
   * 브라우저 개발자 콘솔 후킹 클래스
   */
  class BrowserConsoleHook {
    /**
     * 브라우저 콘솔 후킹 초기화
     * @param {string} serverUrl - MCP 서버 WebSocket URL
     */
    constructor(serverUrl) {
      this.serverUrl = serverUrl || ((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + 
                      window.location.host + '/mcp/ws/console/');
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
      this.maxReconnectAttempts = 5;
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
          this.originalConsole.error('[MCP] 웹소켓 연결 해제 중 오류:', e);
        }
        this.connected = false;
        this.connecting = false;
        this._unhookConsole();
      }
    }

    /**
     * MCP 서버에 연결
     * @param {string} sessionId - 세션 ID (없으면 생성됨)
     * @returns {Promise<string>} 세션 ID
     */
    async connect(sessionId) {
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
          this.originalConsole.log(`[MCP] 브라우저 콘솔 후킹이 활성화되었습니다 (세션 ID: ${this.sessionId})`);
        };

        this.socket.onclose = () => {
          this.connected = false;
          this._unhookConsole();
          this.originalConsole.log('[MCP] 브라우저 콘솔 후킹이 비활성화되었습니다');
          this._scheduleReconnect();
        };

        this.socket.onerror = (error) => {
          this.originalConsole.error('[MCP] 웹소켓 오류:', error);
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
        this.originalConsole.error('[MCP] 브라우저 콘솔 WebSocket 연결 실패:', error);
        this._scheduleReconnect();
        throw error;
      }
    }

    /**
     * 자바스크립트 코드 실행
     * @param {string} code - 실행할 자바스크립트 코드
     * @param {number} timeout - 제한 시간 (밀리초)
     * @returns {Promise<any>} 실행 결과
     */
    async execute(code, timeout = 30000) {
      if (!this.connected) {
        try {
          await this.connect();
        } catch (error) {
          throw new Error('MCP 서버에 연결되어 있지 않습니다');
        }
      }

      const executionId = this._generateExecutionId();

      // 실행 요청 메시지 전송
      this.socket.send(JSON.stringify({
        type: 'execute',
        execution_id: executionId,
        code
      }));

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
            this.originalConsole.log('[MCP] 알 수 없는 메시지 유형:', message.type);
        }
      } catch (error) {
        this.originalConsole.error('[MCP] 메시지 처리 중 오류:', error);
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
        this.originalConsole.error('[MCP] 오류:', message.message);
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
      if (!this.connected) {
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
      if (!this.connected || this.buffer.length === 0) {
        return;
      }
      
      // 버퍼의 메시지들을 하나씩 전송
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
     * 실행 ID 생성
     * @private
     * @returns {string} 생성된 실행 ID
     */
    _generateExecutionId() {
      return 'exec-' + Date.now() + '-' + Math.random().toString(36).substring(2, 10);
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

  /**
   * 터미널 클라이언트 클래스
   */
  class TerminalClient {
    /**
     * 터미널 클라이언트 초기화
     * @param {string} baseUrl - API 기본 URL
     */
    constructor(baseUrl) {
      this.baseUrl = baseUrl || ((window.location.protocol === 'https:' ? 'https://' : 'http://') + 
                    window.location.host + '/mcp');
      this.wsBaseUrl = this.baseUrl.replace(/^http/, 'ws') + '/ws';
      this.activeSession = null;
      this.socket = null;
      this.connected = false;
      this.messageHandlers = new Map();
    }

    /**
     * 터미널 세션 생성
     * @param {string} workingDir - 초기 작업 디렉터리
     * @returns {Promise<string>} 세션 ID
     */
    async createSession(workingDir) {
      try {
        const response = await fetch(`${this.baseUrl}/v1/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            type: 'function_call',
            content: {
              name: 'terminal_create',
              arguments: workingDir ? { working_dir: workingDir } : {},
              call_id: this._generateCallId()
            }
          })
        });

        if (!response.ok) {
          throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.type !== 'function_response' || !data.content.result.session_id) {
          throw new Error('터미널 세션 생성 실패: ' + (data.error || '알 수 없는 오류'));
        }

        this.activeSession = data.content.result.session_id;
        return this.activeSession;
      } catch (error) {
        console.error('터미널 세션 생성 오류:', error);
        throw error;
      }
    }

    /**
     * 터미널 세션 삭제
     * @param {string} sessionId - 세션 ID (없으면 활성 세션 사용)
     * @returns {Promise<boolean>} 성공 여부
     */
    async deleteSession(sessionId) {
      const sid = sessionId || this.activeSession;
      if (!sid) {
        throw new Error('활성 터미널 세션이 없습니다');
      }

      try {
        const response = await fetch(`${this.baseUrl}/v1/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            type: 'function_call',
            content: {
              name: 'terminal_delete',
              arguments: {
                session_id: sid
              },
              call_id: this._generateCallId()
            }
          })
        });

        if (!response.ok) {
          throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.type !== 'function_response' || !data.content.result.success) {
          return false;
        }

        if (sid === this.activeSession) {
          this.activeSession = null;
        }
        
        return true;
      } catch (error) {
        console.error('터미널 세션 삭제 오류:', error);
        throw error;
      }
    }

    /**
     * 명령어 실행
     * @param {string} command - 실행할 명령어
     * @param {string} sessionId - 세션 ID (없으면 활성 세션 사용)
     * @returns {Promise<object>} 실행 결과
     */
    async executeCommand(command, sessionId) {
      const sid = sessionId || this.activeSession;
      if (!sid) {
        throw new Error('활성 터미널 세션이 없습니다');
      }

      try {
        const response = await fetch(`${this.baseUrl}/v1/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            type: 'function_call',
            content: {
              name: 'terminal_execute',
              arguments: {
                session_id: sid,
                command
              },
              call_id: this._generateCallId()
            }
          })
        });

        if (!response.ok) {
          throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.type !== 'function_response') {
          throw new Error('명령어 실행 실패: ' + (data.error || '알 수 없는 오류'));
        }

        return data.content.result;
      } catch (error) {
        console.error('명령어 실행 오류:', error);
        throw error;
      }
    }

    /**
     * 작업 디렉터리 조회/설정
     * @param {string} sessionId - 세션 ID (없으면 활성 세션 사용)
     * @param {string} workingDir - 설정할 작업 디렉터리 (없으면 조회만)
     * @returns {Promise<string>} 작업 디렉터리
     */
    async workingDirectory(sessionId, workingDir) {
      const sid = sessionId || this.activeSession;
      if (!sid) {
        throw new Error('활성 터미널 세션이 없습니다');
      }

      const args = {
        session_id: sid
      };

      if (workingDir) {
        args.working_dir = workingDir;
      }

      try {
        const response = await fetch(`${this.baseUrl}/v1/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            type: 'function_call',
            content: {
              name: 'terminal_workdir',
              arguments: args,
              call_id: this._generateCallId()
            }
          })
        });

        if (!response.ok) {
          throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.type !== 'function_response' || data.content.result.status !== 'success') {
          throw new Error('작업 디렉터리 조회/설정 실패: ' + (data.error || '알 수 없는 오류'));
        }

        return data.content.result.working_dir;
      } catch (error) {
        console.error('작업 디렉터리 조회/설정 오류:', error);
        throw error;
      }
    }

    /**
     * WebSocket 연결
     * @param {string} sessionId - 세션 ID (없으면 활성 세션 사용)
     * @returns {Promise<void>}
     */
    async connectWebSocket(sessionId) {
      const sid = sessionId || this.activeSession;
      if (!sid) {
        throw new Error('활성 터미널 세션이 없습니다');
      }

      if (this.socket) {
        // 이미 연결되어 있는 경우
        if (this.socket.sessionId === sid) {
          return;
        }
        // 다른 세션에 연결되어 있는 경우 연결 해제
        this.disconnectWebSocket();
      }

      try {
        const wsUrl = `${this.wsBaseUrl}/terminal/${sid}`;
        this.socket = new WebSocket(wsUrl);
        this.socket.sessionId = sid;

        return new Promise((resolve, reject) => {
          this.socket.onopen = () => {
            console.log(`[MCP] 터미널 WebSocket 연결됨 (세션 ID: ${sid})`);
            this.connected = true;
            resolve();
          };

          this.socket.onclose = () => {
            console.log('[MCP] 터미널 WebSocket 연결 해제됨');
            this.connected = false;
            this.socket = null;
          };

          this.socket.onerror = (error) => {
            console.error('[MCP] 터미널 WebSocket 오류:', error);
            reject(error);
          };

          this.socket.onmessage = (event) => {
            this._handleMessage(event);
          };

          // 연결 시간 초과
          setTimeout(() => {
            if (!this.connected) {
              reject(new Error('WebSocket 연결 시간 초과'));
            }
          }, 5000);
        });
      } catch (error) {
        console.error('[MCP] 터미널 WebSocket 연결 설정 오류:', error);
        throw error;
      }
    }

    /**
     * WebSocket 연결 해제
     */
    disconnectWebSocket() {
      if (this.socket) {
        try {
          // 연결 해제 요청 전송
          if (this.connected) {
            this.socket.send(JSON.stringify({
              type: 'disconnect'
            }));
          }
          this.socket.close();
        } catch (e) {
          console.error('[MCP] 터미널 WebSocket 연결 해제 중 오류:', e);
        } finally {
          this.connected = false;
          this.socket = null;
        }
      }
    }

    /**
     * 메시지 핸들러 등록
     * @param {string} type - 메시지 유형
     * @param {Function} handler - 핸들러 함수
     * @returns {Function} 핸들러 제거 함수
     */
    onMessage(type, handler) {
      if (!this.messageHandlers.has(type)) {
        this.messageHandlers.set(type, []);
      }
      this.messageHandlers.get(type).push(handler);

      return () => {
        const handlers = this.messageHandlers.get(type);
        if (handlers) {
          const index = handlers.indexOf(handler);
          if (index !== -1) {
            handlers.splice(index, 1);
          }
        }
      };
    }

    /**
     * 메시지 처리
     * @private
     * @param {MessageEvent} event - WebSocket 메시지 이벤트
     */
    _handleMessage(event) {
      try {
        const message = JSON.parse(event.data);
        const type = message.type;

        if (this.messageHandlers.has(type)) {
          for (const handler of this.messageHandlers.get(type)) {
            try {
              handler(message);
            } catch (e) {
              console.error(`[MCP] 메시지 핸들러 오류 (${type}):`, e);
            }
          }
        }
      } catch (error) {
        console.error('[MCP] 메시지 처리 오류:', error);
      }
    }

    /**
     * 함수 호출 ID 생성
     * @private
     * @returns {string} 함수 호출 ID
     */
    _generateCallId() {
      return 'call-' + Date.now() + '-' + Math.random().toString(36).substring(2, 10);
    }
  }

  // MCP 클라이언트 생성
  const baseUrl = (window.location.protocol === 'https:' ? 'https://' : 'http://') + 
                  window.location.host + '/mcp';
  
  const MCP = {
    console: new BrowserConsoleHook(),
    terminal: new TerminalClient(baseUrl),
    
    init: async function(options = {}) {
      const result = {
        consoleSessionId: null,
        terminalSessionId: null,
        consoleConnected: false,
        terminalSessionCreated: false
      };
      
      try {
        // 브라우저 콘솔 초기화
        if (options.autoConnectConsole) {
          try {
            result.consoleSessionId = await this.console.connect();
            result.consoleConnected = true;
            console.log(`[MCP] 브라우저 콘솔이 연결되었습니다 (세션 ID: ${result.consoleSessionId})`);
          } catch (error) {
            console.error('[MCP] 브라우저 콘솔 연결 실패:', error);
          }
        }
        
        // 터미널 초기화
        if (options.autoCreateTerminal) {
          try {
            result.terminalSessionId = await this.terminal.createSession(options.workingDir);
            result.terminalSessionCreated = true;
            console.log(`[MCP] 터미널 세션이 생성되었습니다 (세션 ID: ${result.terminalSessionId})`);
          } catch (error) {
            console.error('[MCP] 터미널 세션 생성 실패:', error);
          }
        }
      } catch (error) {
        console.error('[MCP] 초기화 중 오류:', error);
      }
      
      return result;
    },
    
    cleanup: async function() {
      try {
        // 브라우저 콘솔 연결 해제
        if (this.console && typeof this.console.disconnect === 'function') {
          this.console.disconnect();
        }
        
        // 터미널 세션 정리
        if (this.terminal && this.terminal.activeSession) {
          try {
            // WebSocket 연결 해제
            if (typeof this.terminal.disconnectWebSocket === 'function') {
              this.terminal.disconnectWebSocket();
            }
            
            // 세션 삭제
            if (typeof this.terminal.deleteSession === 'function') {
              await this.terminal.deleteSession();
            }
          } catch (error) {
            console.error('[MCP] 터미널 세션 삭제 실패:', error);
          }
        }
      } catch (error) {
        console.error('[MCP] 정리 중 오류:', error);
      }
    }
  };
  
  // 전역 객체에 MCP 할당
  global.MCP = MCP;
  
})(typeof globalThis !== 'undefined' ? globalThis :
   typeof window !== 'undefined' ? window :
   typeof global !== 'undefined' ? global :
   typeof self !== 'undefined' ? self : {});
