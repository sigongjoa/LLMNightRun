import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Grid, Paper, Tabs, Tab, Button } from '@mui/material';
import { Terminal as TerminalIcon, Code as CodeIcon } from '@mui/icons-material';

import Layout from '../components/Layout';
import MCPTerminal from '../components/MCP/Terminal';
import MCPConsole from '../components/MCP/Console';

// MCP 유틸리티 스크립트 동적 로드
const loadMCPScript = () => {
  return new Promise((resolve, reject) => {
    // 이미 로드된 경우
    if (window.MCP) {
      resolve(window.MCP);
      return;
    }

    const script = document.createElement('script');
    script.src = '/js/mcp.js';
    script.async = true;
    script.onload = () => resolve(window.MCP);
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
  const [tab, setTab] = useState(0);
  const [mcpLoaded, setMcpLoaded] = useState(false);
  const [terminalSession, setTerminalSession] = useState(null);
  const [consoleSession, setConsoleSession] = useState(null);

  // MCP 스크립트 로드
  useEffect(() => {
    loadMCPScript()
      .then(() => setMcpLoaded(true))
      .catch(error => console.error('MCP 스크립트 로드 실패:', error));
      
    // 페이지 언로드 시 세션 정리
    return () => {
      if (window.MCP) {
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
    <Layout title="MCP 도구">
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
              ) : (
                <>콘솔 세션: {consoleSession || '연결 안됨'}</>
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
          </Box>
        </Paper>
      </Container>
    </Layout>
  );
};

export default MCPToolsPage;
