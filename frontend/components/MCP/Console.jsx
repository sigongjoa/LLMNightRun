import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, Button, Typography, Paper, IconButton, Divider, Select, MenuItem, Grid, FormControl, InputLabel } from '@mui/material';
import { Code as CodeIcon, Refresh as RefreshIcon, Clear as ClearIcon, PlayArrow as ExecuteIcon } from '@mui/icons-material';

/**
 * MCP 브라우저 콘솔 컴포넌트
 * 
 * 자바스크립트 코드를 실행하고 콘솔 로그를 표시하는 UI 컴포넌트입니다.
 * 
 * @param {Object} props - 컴포넌트 속성
 * @param {boolean} props.autoConnect - 자동 연결 여부
 * @param {Function} props.onExecute - 코드 실행 시 호출되는 콜백
 * @param {Function} props.onSessionChange - 세션 ID 변경 시 호출되는 콜백
 */
const MCPConsole = ({ 
  autoConnect = true,
  onExecute,
  onSessionChange
}) => {
  const [sessionId, setSessionId] = useState(null);
  const [code, setCode] = useState('');
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [executeResult, setExecuteResult] = useState(null);
  
  const consoleRef = useRef(null);
  const codeHistory = useRef([]);
  
  // 컴포넌트 마운트 시 웹소켓 연결
  useEffect(() => {
    if (autoConnect && typeof window !== 'undefined' && window.MCP && window.MCP.console) {
      connectConsole();
    }
    
    // 컴포넌트 언마운트 시 정리
    return () => {
      if (connected && typeof window !== 'undefined' && window.MCP && window.MCP.console && typeof window.MCP.console.disconnect === 'function') {
        window.MCP.console.disconnect();
      }
    };
  }, [autoConnect]);
  
  // 5초마다 로그 갱신
  useEffect(() => {
    if (!connected) return;
    
    const fetchLogs = async () => {
      try {
        await updateLogs();
      } catch (error) {
        console.error('로그 갱신 실패:', error);
      }
    };
    
    const intervalId = setInterval(fetchLogs, 5000);
    
    return () => clearInterval(intervalId);
  }, [connected, sessionId]);
  
  // 콘솔 연결
  const connectConsole = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (!window.MCP || !window.MCP.console) {
        throw new Error('콘솔 모듈을 로드할 수 없습니다.');
      }
      
      // 콘솔 연결
      const sid = await window.MCP.console.connect();
      setSessionId(sid);
      setConnected(true);
      
      // 초기 로그 조회
      await updateLogs();
      
      // 세션 변경 콜백 호출
      if (onSessionChange) {
        onSessionChange(sid);
      }
    } catch (error) {
      console.error('콘솔 연결 실패:', error);
      setError(`콘솔 연결 실패: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // 콘솔 로그 갱신
  const updateLogs = async () => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(`/api/mcp/logs?session_id=${sessionId}`);
      if (!response.ok) {
        throw new Error(`로그 조회 실패: ${response.status}`);
      }
      
      const data = await response.json();
      setLogs(data.logs || []);
    } catch (error) {
      console.error('로그 조회 실패:', error);
      // 오류를 UI에 표시하지는 않음 (실패해도 계속 재시도)
    }
  };
  
  // 코드 실행
  const executeCode = async () => {
    if (!code.trim() || !sessionId || loading) return;
    
    // 코드 기록에 추가
    codeHistory.current.push(code);
    
    setLoading(true);
    setExecuteResult(null);
    
    try {
      if (!window.MCP || !window.MCP.console) {
        throw new Error('콘솔 모듈을 로드할 수 없습니다.');
      }
      
      const result = await window.MCP.console.execute(code);
      
      // 콜백 호출
      if (onExecute) {
        onExecute(code, result);
      }
      
      // 결과 표시
      setExecuteResult({
        code,
        result,
        timestamp: new Date().toISOString()
      });
      
      // 로그 갱신
      await updateLogs();
    } catch (error) {
      console.error('코드 실행 실패:', error);
      
      // 오류 표시
      setExecuteResult({
        code,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    } finally {
      setLoading(false);
      
      // 스크롤 아래로 이동
      if (consoleRef.current) {
        consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
      }
    }
  };
  
  // 화면 지우기
  const clearScreen = async () => {
    if (sessionId) {
      try {
        await fetch(`/api/mcp/clear_logs?session_id=${sessionId}`, { method: 'POST' });
        setLogs([]);
        setExecuteResult(null);
      } catch (error) {
        console.error('로그 초기화 실패:', error);
      }
    } else {
      setLogs([]);
      setExecuteResult(null);
    }
  };
  
  // 세션 재연결
  const reconnect = () => {
    if (window.MCP && window.MCP.console && typeof window.MCP.console.disconnect === 'function') {
      window.MCP.console.disconnect();
    }
    setConnected(false);
    setSessionId(null);
    setLogs([]);
    setExecuteResult(null);
    connectConsole();
  };
  
  // 로그 항목 스타일 매핑
  const logLevelStyle = {
    info: { color: '#f0f0f0' },
    warn: { color: '#ffc107' },
    error: { color: '#f44336' },
    debug: { color: '#8bc34a' }
  };
  
  // 필터링된 로그
  const filteredLogs = logs.filter(log => 
    filter === 'all' || log.level === filter
  );
  
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
      {/* 콘솔 헤더 */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        mb: 1,
        pb: 1,
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <CodeIcon sx={{ mr: 1 }} />
          <Typography variant="subtitle1">브라우저 콘솔</Typography>
        </Box>
        
        <Box>
          <IconButton 
            size="small" 
            onClick={clearScreen} 
            title="로그 지우기"
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
      
      {/* 코드 입력 영역 */}
      <Box sx={{ mb: 2 }}>
        <TextField
          multiline
          fullWidth
          variant="outlined"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="실행할 JavaScript 코드를 입력하세요..."
          disabled={!connected || loading}
          InputProps={{
            sx: {
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              backgroundColor: '#1e1e1e',
              color: '#f0f0f0',
              '& textarea': {
                p: 1
              }
            }
          }}
          minRows={3}
          maxRows={8}
          sx={{ mb: 1 }}
        />
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={executeCode}
            disabled={!connected || loading || !code.trim()}
            startIcon={<ExecuteIcon />}
            size="small"
          >
            {loading ? '실행 중...' : '실행'}
          </Button>
        </Box>
      </Box>
      
      {/* 실행 결과 */}
      {executeResult && (
        <Box 
          sx={{
            mb: 2,
            p: 1,
            borderRadius: 1,
            backgroundColor: executeResult.error ? 'rgba(244, 67, 54, 0.1)' : 'rgba(76, 175, 80, 0.1)',
            border: executeResult.error ? '1px solid rgba(244, 67, 54, 0.3)' : '1px solid rgba(76, 175, 80, 0.3)'
          }}
        >
          <Typography variant="caption" sx={{ display: 'block', mb: 0.5, color: 'rgba(255,255,255,0.5)' }}>
            실행 결과:
          </Typography>
          
          {executeResult.error ? (
            <Typography variant="body2" color="error" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
              {executeResult.error}
            </Typography>
          ) : (
            <Typography variant="body2" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {typeof executeResult.result === 'object' 
                ? JSON.stringify(executeResult.result, null, 2)
                : String(executeResult.result)
              }
            </Typography>
          )}
        </Box>
      )}
      
      {/* 로그 필터 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
          로그 ({filteredLogs.length})
        </Typography>
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <Select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            variant="standard"
            sx={{ color: 'rgba(255,255,255,0.7)', '& .MuiSelect-icon': { color: 'rgba(255,255,255,0.7)' } }}
          >
            <MenuItem value="all">모든 로그</MenuItem>
            <MenuItem value="info">Info</MenuItem>
            <MenuItem value="warn">Warning</MenuItem>
            <MenuItem value="error">Error</MenuItem>
            <MenuItem value="debug">Debug</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {/* 콘솔 로그 */}
      <Box 
        ref={consoleRef}
        sx={{ 
          flex: 1, 
          overflowY: 'auto', 
          p: 1,
          backgroundColor: '#1e1e1e',
          borderRadius: 1,
          fontFamily: 'monospace',
          fontSize: '0.875rem'
        }}
      >
        {filteredLogs.length === 0 ? (
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)', fontStyle: 'italic' }}>
            로그가 없습니다.
          </Typography>
        ) : (
          filteredLogs.map((log, index) => (
            <Box key={index} sx={{ mb: 0.5, ...logLevelStyle[log.level] }}>
              <Typography 
                component="span" 
                variant="caption" 
                sx={{ color: 'rgba(255,255,255,0.5)', mr: 1 }}
              >
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </Typography>
              <Typography 
                component="span" 
                variant="body2" 
                sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}
              >
                {log.message}
              </Typography>
            </Box>
          ))
        )}
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

export default MCPConsole;
