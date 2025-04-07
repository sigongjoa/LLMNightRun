/**
 * MCP 터미널 클라이언트
 * 
 * MCP 서버의 터미널 서비스와 통신하기 위한 클라이언트 유틸리티입니다.
 * 터미널 세션을 생성하고, 명령어를 실행하고, 결과를 조회하는 기능을 제공합니다.
 */

class MCPTerminalClient {
  /**
   * MCP 터미널 클라이언트 초기화
   * @param {string} baseUrl - MCP 서버 API 기본 URL (e.g., "http://localhost:8000/mcp")
   * @param {string} wsBaseUrl - MCP 서버 WebSocket 기본 URL (e.g., "ws://localhost:8000/mcp/ws")
   */
  constructor(baseUrl, wsBaseUrl = null) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl : baseUrl + '/';
    this.wsBaseUrl = wsBaseUrl || baseUrl.replace(/^http/, 'ws');
    if (!this.wsBaseUrl.endsWith('/')) {
      this.wsBaseUrl += '/';
    }
    this.activeSession = null;
    this.socket = null;
    this.connected = false;
    this.messageHandlers = new Map();
    this.messageId = 0;
  }

  /**
   * API 호출 도우미 함수
   * @private
   * @param {string} endpoint - API 엔드포인트
   * @param {string} method - HTTP 메서드
   * @param {object} data - 요청 데이터
   * @returns {Promise<any>} 응답 데이터
   */
  async _callApi(endpoint, method = 'GET', data = null) {
    const url = this.baseUrl + 'v1/' + endpoint;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`MCP API 호출 오류 (${endpoint}):`, error);
      throw error;
    }
  }

  /**
   * 터미널 세션 생성
   * @param {string} workingDir - 초기 작업 디렉터리 (선택 사항)
   * @returns {Promise<string>} 세션 ID
   */
  async createSession(workingDir = null) {
    try {
      const data = workingDir ? { working_dir: workingDir } : {};
      const response = await this._callApi('process', 'POST', {
        type: 'function_call',
        content: {
          name: 'terminal_create',
          arguments: data,
          call_id: this._generateCallId()
        }
      });

      if (response.type === 'function_response' && response.content.status === 'success') {
        this.activeSession = response.content.result.session_id;
        return this.activeSession;
      } else {
        throw new Error(response.content.error || '터미널 세션 생성 실패');
      }
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
  async deleteSession(sessionId = null) {
    const sid = sessionId || this.activeSession;
    if (!sid) {
      throw new Error('활성 터미널 세션이 없습니다');
    }

    try {
      const response = await this._callApi('process', 'POST', {
        type: 'function_call',
        content: {
          name: 'terminal_delete',
          arguments: {
            session_id: sid
          },
          call_id: this._generateCallId()
        }
      });

      if (response.type === 'function_response' && response.content.result.success) {
        if (sid === this.activeSession) {
          this.activeSession = null;
        }
        return true;
      } else {
        throw new Error(response.content.error || '터미널 세션 삭제 실패');
      }
    } catch (error) {
      console.error('터미널 세션 삭제 오류:', error);
      throw error;
    }
  }

  /**
   * 터미널 명령어 실행
   * @param {string} command - 실행할 명령어
   * @param {string} sessionId - 세션 ID (없으면 활성 세션 사용)
   * @param {number} timeout - 실행 제한 시간 (초)
   * @param {string} workingDir - 작업 디렉터리 (선택 사항)
   * @returns {Promise<object>} 실행 결과
   */
  async executeCommand(command, sessionId = null, timeout = null, workingDir = null) {
    const sid = sessionId || this.activeSession;
    if (!sid) {
      throw new Error('활성 터미널 세션이 없습니다');
    }

    try {
      const args = {
        session_id: sid,
        command
      };

      if (timeout !== null) {
        args.timeout = timeout;
      }

      if (workingDir) {
        args.working_dir = workingDir;
      }

      const response = await this._callApi('process', 'POST', {
        type: 'function_call',
        content: {
          name: 'terminal_execute',
          arguments: args,
          call_id: this._generateCallId()
        }
      });

      if (response.type === 'function_response') {
        return response.content.result;
      } else {
        throw new Error(response.content.error || '명령어 실행 실패');
      }
    } catch (error) {
      console.error('명령어 실행 오류:', error);
      throw error;
    }
  }

  /**
   * 명령어 실행 기록 조회
   * @param {string} sessionId - 세션 ID (없으면 활성 세션 사용)
   * @param {number} count - 조회할 기록 수
   * @returns {Promise<Array>} 명령어 실행 기록
   */
  async getHistory(sessionId = null, count = 10) {
    const sid = sessionId || this.activeSession;
    if (!sid) {
      throw new Error('활성 터미널 세션이 없습니다');
    }

    try {
      const response = await this._callApi('process', 'POST', {
        type: 'function_call',
        content: {
          name: 'terminal_history',
          arguments: {
            session_id: sid,
            count
          },
          call_id: this._generateCallId()
        }
      });

      if (response.type === 'function_response' && response.content.result.status === 'success') {
        return response.content.result.history;
      } else {
        throw new Error(response.content.error || '명령어 실행 기록 조회 실패');
      }
    } catch (error) {
      console.error('명령어 실행 기록 조회 오류:', error);
      throw error;
    }
  }

  /**
   * 활성 세션 목록 조회
   * @returns {Promise<Array>} 세션 목록
   */
  async listSessions() {
    try {
      const response = await this._callApi('process', 'POST', {
        type: 'function_call',
        content: {
          name: 'terminal_sessions',
          arguments: {},
          call_id: this._generateCallId()
        }
      });

      if (response.type === 'function_response' && response.content.result.status === 'success') {
        return response.content.result.sessions;
      } else {
        throw new Error(response.content.error || '세션 목록 조회 실패');
      }
    } catch (error) {
      console.error('세션 목록 조회 오류:', error);
      throw error;
    }
  }

  /**
   * 작업 디렉터리 조회 또는 설정
   * @param {string} sessionId - 세션 ID (없으면 활성 세션 사용)
   * @param {string} workingDir - 설정할 작업 디렉터리 (없으면 조회만 수행)
   * @returns {Promise<string>} 작업 디렉터리
   */
  async workingDirectory(sessionId = null, workingDir = null) {
    const sid = sessionId || this.activeSession;
    if (!sid) {
      throw new Error('활성 터미널 세션이 없습니다');
    }

    try {
      const args = {
        session_id: sid
      };

      if (workingDir) {
        args.working_dir = workingDir;
      }

      const response = await this._callApi('process', 'POST', {
        type: 'function_call',
        content: {
          name: 'terminal_workdir',
          arguments: args,
          call_id: this._generateCallId()
        }
      });

      if (response.type === 'function_response' && response.content.result.status === 'success') {
        return response.content.result.working_dir;
      } else {
        throw new Error(response.content.error || '작업 디렉터리 조회/설정 실패');
      }
    } catch (error) {
      console.error('작업 디렉터리 조회/설정 오류:', error);
      throw error;
    }
  }

  /**
   * WebSocket 연결 설정
   * @param {string} sessionId - 세션 ID (없으면 활성 세션 사용)
   * @returns {Promise<void>}
   */
  async connectWebSocket(sessionId = null) {
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
      const wsUrl = `${this.wsBaseUrl}terminal/${sid}`;
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

    // 핸들러 제거 함수 반환
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
   * WebSocket 메시지 처리
   * @private
   * @param {MessageEvent} event - 웹소켓 메시지 이벤트
   */
  _handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      const type = message.type;

      // 메시지 유형에 대한 핸들러 호출
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
   * 핑 메시지 전송 (연결 유지)
   */
  sendPing() {
    if (this.connected && this.socket && this.socket.readyState === WebSocket.OPEN) {
      try {
        this.socket.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now()
        }));
      } catch (error) {
        console.error('[MCP] 핑 메시지 전송 오류:', error);
      }
    }
  }

  /**
   * 함수 호출 ID 생성
   * @private
   * @returns {string} 함수 호출 ID
   */
  _generateCallId() {
    return 'call-' + Date.now() + '-' + (++this.messageId);
  }
}

// 전역 인스턴스 생성 (기본 MCP 서버 URL 사용)
const defaultMCPServerUrl = window.location.origin + '/mcp/';
window.MCPTerminal = new MCPTerminalClient(defaultMCPServerUrl);

export default window.MCPTerminal;
