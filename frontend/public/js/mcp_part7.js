    /**
     * 작업 디렉터리 조회 또는 설정
     * @param {string} sessionId - 세션 ID
     * @param {string} workingDir - 설정할 작업 디렉터리
     * @returns {Promise<string>} 작업 디렉터리
     */
    async workingDirectory(sessionId, workingDir) {
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
     * @param {string} sessionId - 세션 ID
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
