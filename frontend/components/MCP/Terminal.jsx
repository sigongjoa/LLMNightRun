import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, Button, Typography, Paper, CircularProgress, IconButton, Divider } from '@mui/material';
import { Terminal as TerminalIcon, Refresh as RefreshIcon, Clear as ClearIcon } from '@mui/icons-material';
import MCP from '../../utils/mcp';

/**
 * MCP 터미널 컴포넌트
 * 
 * 명령어를 입력하고 결과를 표시하는 터미널 UI 컴포넌트입니다.
 * 
 * @param {Object} props - 컴포넌트 속성
 * @param {string} props.initialWorkingDir - 초기 작업 디렉터리
 * @param {boolean} props.autoConnect - 자동 연결 여부
 * @param {Function} props.onCommand - 명령어 실행 시 호출되는 콜백
 * @param {Function} props.onSessionChange - 세션 ID 변경 시 호출되는 콜백
 */
const MCPTerminal = ({ 
  initialWorkingDir,
  autoConnect = true,
  onCommand,
  onSessionChange
}) => {
  const [sessionId, setSessionId] = useState(null);
  const [command, setCommand] = useState('');
  const [history, setHistory] = useState([]);
  const [workingDir, setWorkingDir] = useState(initialWorkingDir || 'D:\\');
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  
  const terminalRef = useRef(null);
  const commandHistoryRef = useRef([]);
  const historyIndexRef = useRef(-1);
  
  // 컴포넌트 마운트 시 터미널 세션 생성
  useEffect(() => {
    if (autoConnect) {
      initTerminal();
    }
    
    // 컴포넌트 언마운트 시 정리
    return () => {
      if (sessionId) {
        MCP.terminal.disconnectWebSocket();
      }
    };
  }, [autoConnect]);
  
  // 터미널 초기화
  const initTerminal = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 세션 생성
      const newSessionId = await MCP.terminal.createSession(initialWorkingDir);
      setSessionId(newSessionId);
      
      // 작업 디렉터리 조회
      const dir = await MCP.terminal.workingDirectory(newSessionId);
      setWorkingDir(dir);
      
      // WebSocket 연결
      await MCP.terminal.connectWebSocket(newSessionId);
      
      // 기본 정보 표시
      setHistory([{
        command: 'session-info',
        result: {
          stdout: `터미널 세션이 생성되었습니다 (ID: ${newSessionId})`,
          stderr: '',
          exit_code: 0
        }
      }]);
      
      setConnected(true);
      
      // 세션 변경 콜백 호출
      if (onSessionChange) {
        onSessionChange(newSessionId);
      }
    } catch (error) {
      console.error('터미널 초기화 실패:', error);
      setError(`터미널 초기화 실패: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // 명령어 실행
  const executeCommand = async () => {
    if (!command.trim() || !sessionId || loading) return;
    
    // 명령어 입력 기록
    commandHistoryRef.current.push(command);
    historyIndexRef.current = commandHistoryRef.current.length;
    
    setLoading(true);
    
    // 명령어 UI에 표시
    setHistory(prev => [...prev, {
      command,
      result: { stdout: 'Executing...', stderr: '', exit_code: null }
    }]);
    
    try {
      // 명령어 실행
      const result = await MCP.terminal.executeCommand(command, sessionId);
      
      // 콜백 호출
      if (onCommand) {
        onCommand(command, result);
      }
      
      // 작업 디렉터리 갱신 (cd 명령어인 경우)
      if (command.trim().startsWith('cd ') && result.exit_code === 0) {
        const dir = await MCP.terminal.workingDirectory(sessionId);
        setWorkingDir(dir);
      }
      
      // 결과 업데이트
      setHistory(prev => prev.map((item, index) => 
        index === prev.length - 1
          ? { ...item, result }
          : item
      ));
    } catch (error) {
      console.error('명령어 실행 실패:', error);
      
      // 오류 표시
      setHistory(prev => prev.map((item, index) => 
        index === prev.length - 1
          ? { ...item, result: { stdout: '', stderr: `Error: ${error.message}`, exit_code: 1 } }
          : item
      ));
    } finally {
      setLoading(false);
      setCommand('');
      
      // 스크롤 아래로 이동
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
    }
  };
  
  // 명령어 기록 탐색 (위/아래 화살표)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      executeCommand();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyIndexRef.current > 0) {
        historyIndexRef.current--;
        setCommand(commandHistoryRef.current[historyIndexRef.current]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndexRef.current < commandHistoryRef.current.length - 1) {
        historyIndexRef.current++;
        setCommand(commandHistoryRef.current[historyIndexRef.current]);
      } else {
        historyIndexRef.current = commandHistoryRef.current.length;
        setCommand('');
      }
    }
  };
  
  // 화면 지우기
  const clearScreen = () => {
    setHistory([]);
  };
  
  // 세션 재연결
  const reconnect = () => {
    // 세션 삭제
    if (sessionId) {
      MCP.terminal.disconnectWebSocket();
      MCP.terminal.deleteSession(sessionId)
        .finally(() => {
          setSessionId(null);
          setConnected(false);
          // 새 세션 생성
          initTerminal();
        });
    } else {
      initTerminal();
    }
  };
  
  // 명령어 결과 렌더링
  const renderCommandResult = (item, index) => {
    const { command, result } = item;
    
    return (
      <Box key={index} sx={{ mb: 1 }}>
        {/* 명령어 입력 */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
          <Typography component="span" variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>
            {workingDir}&gt;
          </Typography>
          <Typography component="span" variant="body2" sx={{ ml: 1, fontFamily: 'monospace' }}>
            {command}
          </Typography>
        </Box>
        
        {/* 명령어 출력 */}
        {result && (
          <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem', whiteSpace: 'pre-wrap', ml: 2 }}>
            {result.stdout && (
              <Typography variant="body2" component="div" sx={{ whiteSpace: 'pre-wrap' }}>
                {result.stdout}
              </Typography>
            )}
            {result.stderr && (
              <Typography variant="body2" component="div" color="error" sx={{ whiteSpace: 'pre-wrap' }}>
                {result.stderr}
              </Typography>
            )}
          </Box>
        )}
      </Box>
    );
  };
  
  return (
    <Paper 
      elevation={3}
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        bgcolor: '#252525',
        color: '#f0f0f0',
        p: 1,
        borderRadius: 1
      }}
    >
      {/* 터미널 헤더 */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        mb: 1,
        pb: 1,
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TerminalIcon sx={{ mr: 1 }} />
          <Typography variant="subtitle1">터미널</Typography>
          {loading && <CircularProgress size={16} sx={{ ml: 1 }} />}
        </Box>
        
        <Box>
          <IconButton 
            size="small" 
            onClick={clearScreen} 
            title="화면 지우기"
            sx={{ color: 'rgba(255,255,255,0.7)' }}
          >
            <ClearIcon fontSize="small" />
          </IconButton>
          <IconButton 
            size="small" 
            onClick={reconnect} 
            title="세션 재연결"
            sx={{ color: 'rgba(255,255,255,0.7)', ml: 1 }}
          >
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>
      
      {/* 오류 메시지 */}
      {error && (
        <Typography variant="body2" color="error" sx={{ mb: 1 }}>
          {error}
        </Typography>
      )}
      
      {/* 터미널 본문 */}
      <Box 
        ref={terminalRef}
        sx={{ 
          flex: 1, 
          overflowY: 'auto', 
          p: 1,
          backgroundColor: '#1e1e1e',
          borderRadius: 1,
          mb: 1
        }}
      >
        {history.map(renderCommandResult)}
      </Box>
      
      {/* 명령어 입력 */}
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Typography component="span" variant="body2" color="primary" sx={{ fontWeight: 'bold', whiteSpace: 'nowrap' }}>
          {workingDir}&gt;
        </Typography>
        <TextField
          fullWidth
          variant="standard"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!connected || loading}
          autoFocus
          InputProps={{
            disableUnderline: true,
            sx: {
              ml: 1,
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              color: '#f0f0f0',
              '& input': {
                p: 0.5
              }
            }
          }}
          sx={{ backgroundColor: 'transparent' }}
        />
      </Box>
      
      {/* 연결 상태 */}
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          mt: 1,
          pt: 1,
          borderTop: '1px solid rgba(255,255,255,0.1)',
          fontSize: '0.75rem',
          color: 'rgba(255,255,255,0.5)'
        }}
      >
        <Box>
          세션: {sessionId ? (
            <Typography component="span" variant="caption" color="primary">
              {sessionId.substring(0, 8)}...
            </Typography>
          ) : '연결 안됨'}
        </Box>
        <Box>
          상태: {connected ? (
            <Typography component="span" variant="caption" color="success.main">
              연결됨
            </Typography>
          ) : (
            <Typography component="span" variant="caption" color="error">
              연결 안됨
            </Typography>
          )}
        </Box>
      </Box>
    </Paper>
  );
};

export default MCPTerminal;
