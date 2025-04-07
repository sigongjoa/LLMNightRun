  /**
   * MCP 클라이언트 초기화
   * @param {object} options - 초기화 옵션
   * @returns {Promise<object>} MCP 클라이언트 객체
   */
  async function initMCP(options = {}) {
    const result = {
      consoleSessionId: null,
      terminalSessionId: null,
      consoleConnected: false,
      terminalSessionCreated: false
    };

    const consoleTool = new BrowserConsoleHook(options.consoleUrl);
    const terminalTool = new MCPTerminalClient(options.terminalUrl, options.terminalWsUrl);

    // 브라우저 콘솔 초기화
    if (options.autoConnectConsole) {
      try {
        result.consoleSessionId = await consoleTool.connect();
        result.consoleConnected = true;
        console.log(`[MCP] 브라우저 콘솔이 연결되었습니다 (세션 ID: ${result.consoleSessionId})`);
      } catch (error) {
        console.error('[MCP] 브라우저 콘솔 연결 실패:', error);
      }
    }

    // 터미널 세션 초기화
    if (options.autoCreateTerminal) {
      try {
        result.terminalSessionId = await terminalTool.createSession(options.workingDir);
        result.terminalSessionCreated = true;
        console.log(`[MCP] 터미널 세션이 생성되었습니다 (세션 ID: ${result.terminalSessionId})`);

        // WebSocket 연결
        if (options.autoConnectTerminal !== false) {
          await terminalTool.connectWebSocket(result.terminalSessionId);
        }
      } catch (error) {
        console.error('[MCP] 터미널 세션 생성 실패:', error);
      }
    }

    return {
      console: consoleTool,
      terminal: terminalTool,
      sessions: result
    };
  }

  /**
   * MCP 연결 정리
   * @param {object} mcp - MCP 클라이언트 객체
   * @param {boolean} deleteTerminalSession - 터미널 세션 삭제 여부
   */
  async function cleanupMCP(mcp, deleteTerminalSession = true) {
    if (!mcp) return;

    try {
      // 브라우저 콘솔 연결 해제
      if (mcp.console) {
        mcp.console.disconnect();
      }

      // 터미널 세션 정리
      if (mcp.terminal) {
        // WebSocket 연결 해제
        mcp.terminal.disconnectWebSocket();

        // 세션 삭제
        if (deleteTerminalSession && mcp.terminal.activeSession) {
          try {
            await mcp.terminal.deleteSession();
            console.log('[MCP] 터미널 세션이 삭제되었습니다');
          } catch (error) {
            console.error('[MCP] 터미널 세션 삭제 실패:', error);
          }
        }
      }
    } catch (error) {
      console.error('[MCP] 정리 중 오류:', error);
    }
  }

  // 전역 객체로 노출
  global.MCP = {
    BrowserConsoleHook,
    MCPTerminalClient,
    init: initMCP,
    cleanup: cleanupMCP
  };

})(typeof window !== 'undefined' ? window : global);
