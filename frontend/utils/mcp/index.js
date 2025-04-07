/**
 * MCP 클라이언트 모듈
 * 
 * MCP(Model Context Protocol) 서버와 통신하기 위한 클라이언트 유틸리티 모음입니다.
 * - 브라우저 개발자 콘솔 후킹 및 로그 전송
 * - 터미널 명령어 실행 및 결과 조회
 */

import BrowserConsoleHook from './console-hook';
import MCPTerminalClient from './terminal';

/**
 * MCP 클라이언트 초기화
 * @param {object} options - 초기화 옵션
 * @param {boolean} options.autoConnectConsole - 콘솔 자동 연결 여부
 * @param {boolean} options.autoCreateTerminal - 터미널 세션 자동 생성 여부
 * @param {string} options.workingDir - 터미널 초기 작업 디렉터리
 * @returns {Promise<object>} MCP 클라이언트 객체 및 세션 정보
 */
export const initMCP = async (options = {}) => {
  const result = {
    consoleSessionId: null,
    terminalSessionId: null,
    consoleConnected: false,
    terminalSessionCreated: false
  };

  try {
    // 브라우저 개발자 콘솔 초기화
    if (options.autoConnectConsole) {
      try {
        result.consoleSessionId = await BrowserConsoleHook.connect();
        result.consoleConnected = true;
        console.log(`[MCP] 브라우저 콘솔이 연결되었습니다 (세션 ID: ${result.consoleSessionId})`);
      } catch (error) {
        console.error('[MCP] 브라우저 콘솔 연결 실패:', error);
      }
    }

    // 터미널 세션 초기화
    if (options.autoCreateTerminal) {
      try {
        result.terminalSessionId = await MCPTerminalClient.createSession(options.workingDir);
        result.terminalSessionCreated = true;
        console.log(`[MCP] 터미널 세션이 생성되었습니다 (세션 ID: ${result.terminalSessionId})`);
      } catch (error) {
        console.error('[MCP] 터미널 세션 생성 실패:', error);
      }
    }
  } catch (error) {
    console.error('[MCP] 초기화 중 오류:', error);
  }

  return {
    console: BrowserConsoleHook,
    terminal: MCPTerminalClient,
    sessions: result
  };
};

/**
 * MCP 연결 정리
 * - 브라우저 콘솔 후킹 해제
 * - 터미널 세션 삭제
 * @param {boolean} deleteTerminalSession - 터미널 세션 삭제 여부
 */
export const cleanupMCP = async (deleteTerminalSession = true) => {
  try {
    // 브라우저 콘솔 연결 해제
    BrowserConsoleHook.disconnect();

    // 터미널 세션 정리
    if (deleteTerminalSession && MCPTerminalClient.activeSession) {
      try {
        // WebSocket 연결 해제
        MCPTerminalClient.disconnectWebSocket();
        
        // 세션 삭제
        await MCPTerminalClient.deleteSession();
        console.log('[MCP] 터미널 세션이 삭제되었습니다');
      } catch (error) {
        console.error('[MCP] 터미널 세션 삭제 실패:', error);
      }
    }
  } catch (error) {
    console.error('[MCP] 정리 중 오류:', error);
  }
};

// 브라우저 종료 시 정리 작업 수행
window.addEventListener('beforeunload', () => {
  BrowserConsoleHook.disconnect();
  MCPTerminalClient.disconnectWebSocket();
});

// 전역 객체로 노출
window.MCP = {
  console: BrowserConsoleHook,
  terminal: MCPTerminalClient,
  init: initMCP,
  cleanup: cleanupMCP
};

export default window.MCP;
