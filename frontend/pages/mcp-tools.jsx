import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Grid, Paper, Tabs, Tab, Button } from '@mui/material';
import { Terminal as TerminalIcon, Code as CodeIcon, Settings as SettingsIcon } from '@mui/icons-material';

import MCPTerminal from '../components/MCP/Terminal';
import MCPConsole from '../components/MCP/Console';
import MCPSettingsPanel from '../components/MCP/Settings/MCPSettingsPanel';

// MCP 유틸리티 스크립트 동적 로드
const loadMCPScript = () => {
  return new Promise((resolve, reject) => {
    // 이미 로드된 경우
    if (typeof window !== 'undefined' && window.MCP) {
      resolve(window.MCP);
      return;
    }

    if (typeof window === 'undefined') {
      reject(new Error('window is not defined'));
      return;
    }

    const script = document.createElement('script');
    script.src = '/js/mcp.js';
    script.async = true;
    script.onload = () => {
      if (window.MCP) {
        resolve(window.MCP);
      } else {
        reject(new Error('MCP object not available after script load'));
      }
    };
    script.onerror = (error) => reject(new Error('MCP 스크립트 로드 실패'));

    document.body.appendChild(script);
  });
};

// 탭 패널 컴포넌트
const TabPanel = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`mcp-tabpanel-${index}`}
      aria-labelledby={`mcp-tab-${index}`}
      style={{ height: '100%' }}
      {...other}
    >
      {value === index && (
        <Box sx={{ height: '100%', pt: 2 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

// MCP 도구 페이지
const MCPToolsPage = () => {
  const [tab, setTab] = useState(2); // 초기 탭을 MCP 설정으로 설정
  const [isPageLoaded, setIsPageLoaded] = useState(false);
  const [mcpLoaded, setMcpLoaded] = useState(false);
  const [terminalSession, setTerminalSession] = useState(null);
  const [consoleSession, setConsoleSession] = useState(null);

  // 페이지 로드 상태 추적
  useEffect(() => {
    // 페이지가 완전히 로드되었을 때
    if (typeof window !== 'undefined') {
      setIsPageLoaded(true);
    }
  }, []);

  // MCP 스크립트 로드
  useEffect(() => {
    let isMounted = true;
    
    const loadScript = async () => {
      try {
        const mcp = await loadMCPScript();
        if (isMounted) {
          setMcpLoaded(true);
          console.log('MCP 스크립트 로드 성공:', mcp);
        }
      } catch (error) {
        console.error('MCP 스크립트 로드 실패:', error);
      }
    };
    
    // 클라이언트 사이드에서만 실행
    if (typeof window !== 'undefined') {
      loadScript();
    }
      
    // 페이지 언로드 시 정리
    return () => {
      isMounted = false;
      if (typeof window !== 'undefined' && window.MCP && typeof window.MCP.cleanup === 'function') {
        window.MCP.cleanup();
      }
    };
  }, []);

  // 탭 변경 핸들러
  const handleTabChange = (event, newValue) => {
    setTab(newValue);
  };

  // 터미널 세션 핸들러
  const handleTerminalSession = (sessionId) => {
    setTerminalSession(sessionId);
  };

  // 콘솔 세션 핸들러
  const handleConsoleSession = (sessionId) => {
    setConsoleSession(sessionId);
  };

  // 명령어 실행 핸들러
  const handleCommand = (command, result) => {
    console.log(`명령어 실행: ${command}`, result);
  };

  // 코드 실행 핸들러
  const handleExecute = (code, result) => {
    console.log(`코드 실행: ${code}`, result);
  };

  return (
    <Container maxWidth="xl">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            MCP 도구
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Model Context Protocol(MCP) 서비스를 통해 브라우저 콘솔 및 시스템 터미널과 상호작용합니다.
          </Typography>
        </Box>

        <Paper sx={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
          {/* 탭 헤더 */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tab} onChange={handleTabChange} aria-label="MCP 도구 탭">
              <Tab 
                icon={<TerminalIcon />} 
                label="터미널" 
                id="mcp-tab-0"
                aria-controls="mcp-tabpanel-0" 
              />
              <Tab 
                icon={<CodeIcon />} 
                label="브라우저 콘솔" 
                id="mcp-tab-1"
                aria-controls="mcp-tabpanel-1" 
              />
              <Tab 
                icon={<SettingsIcon />} 
                label="MCP 설정" 
                id="mcp-tab-2"
                aria-controls="mcp-tabpanel-2" 
              />
            </Tabs>
          </Box>

          {/* 세션 정보 */}
          <Box 
            sx={{ 
              px: 2, 
              py: 1, 
              bgcolor: 'background.paper', 
              borderBottom: '1px solid',
              borderColor: 'divider',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Typography variant="body2" color="text.secondary">
              {tab === 0 ? (
                <>터미널 세션: {terminalSession || '연결 안됨'}</>
              ) : tab === 1 ? (
                <>콘솔 세션: {consoleSession || '연결 안됨'}</>
              ) : (
                <>MCP 설정: 로컬 LLM 구성 및 테스트</>
              )}
            </Typography>
            
            <Box>
              <Button 
                size="small" 
                variant="outlined"
                onClick={() => window.open('/api/docs', '_blank')}
              >
                API 문서
              </Button>
            </Box>
          </Box>

          {/* 탭 컨텐츠 */}
          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            <TabPanel value={tab} index={0}>
              <MCPTerminal 
                initialWorkingDir="D:\\"
                autoConnect={mcpLoaded}
                onCommand={handleCommand}
                onSessionChange={handleTerminalSession}
              />
            </TabPanel>
            
            <TabPanel value={tab} index={1}>
              <MCPConsole 
                autoConnect={mcpLoaded}
                onExecute={handleExecute}
                onSessionChange={handleConsoleSession}
              />
            </TabPanel>
            
            <TabPanel value={tab} index={2}>
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                {isPageLoaded ? <MCPSettingsPanel /> : (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <Typography variant="h6" color="text.secondary">
                      MCP 설정 페이지 로드 중...
                    </Typography>
                  </Box>
                )}
              </Box>
            </TabPanel>
          </Box>
        </Paper>
      </Container>
  );
};

export default MCPToolsPage;
