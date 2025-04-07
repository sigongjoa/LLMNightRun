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
