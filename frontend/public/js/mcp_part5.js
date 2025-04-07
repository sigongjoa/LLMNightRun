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
     * @param {string} workingDir - 초기 작업 디렉터리
     * @returns {Promise<string>} 세션 ID
     */
    async createSession(workingDir) {
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
     * @param {string} sessionId - 세션 ID
     * @returns {Promise<boolean>} 성공 여부
     */
    async deleteSession(sessionId) {
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
