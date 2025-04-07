    /**
     * 터미널 명령어 실행
     * @param {string} command - 실행할 명령어
     * @param {string} sessionId - 세션 ID
     * @param {number} timeout - 제한 시간
     * @param {string} workingDir - 작업 디렉터리
     * @returns {Promise<object>} 실행 결과
     */
    async executeCommand(command, sessionId, timeout, workingDir) {
      const sid = sessionId || this.activeSession;
      if (!sid) {
        throw new Error('활성 터미널 세션이 없습니다');
      }

      try {
        const args = {
          session_id: sid,
          command
        };

        if (timeout !== null && timeout !== undefined) {
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
     * @param {string} sessionId - 세션 ID
     * @param {number} count - 기록 수
     * @returns {Promise<Array>} 실행 기록
     */
    async getHistory(sessionId, count = 10) {
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
