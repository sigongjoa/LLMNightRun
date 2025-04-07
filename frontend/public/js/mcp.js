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
      this.pendingExecutions = new Map();
      this.buffer = [];
      this.connecting = false;
      this.maxBufferSize = 1000;
      this.reconnectTimeout = null;
      this.reconnectAttempts = 0;
      this.maxReconnectAttempts = 5;
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