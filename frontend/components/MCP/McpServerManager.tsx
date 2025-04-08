import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Button, 
  Grid,
  Alert,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  ButtonGroup,
  CircularProgress
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  Edit as EditIcon,
  Add as AddIcon,
  Code as CodeIcon,
  Launch as LaunchIcon
} from '@mui/icons-material';
import { ServerList } from './ServerList';
import { ServerEditor } from './ServerEditor';
import { JsonConfigEditor } from './JsonConfigEditor';
import { ExternalServerAdder } from './ExternalServerAdder';
import { McpProvider } from '../../contexts/McpContext';

export const McpServerManager: React.FC = () => {
  const [serverEditorOpen, setServerEditorOpen] = useState<boolean>(false);
  const [jsonEditorOpen, setJsonEditorOpen] = useState<boolean>(false);
  const [externalServerAdderOpen, setExternalServerAdderOpen] = useState<boolean>(false);
  const [editingServerId, setEditingServerId] = useState<string | undefined>(undefined);

  const handleAddServer = () => {
    setEditingServerId(undefined);
    setServerEditorOpen(true);
  };

  const handleEditServer = (serverId: string) => {
    setEditingServerId(serverId);
    setServerEditorOpen(true);
  };

  const handleOpenJsonEditor = () => {
    setJsonEditorOpen(true);
  };

  const handleOpenExternalServerAdder = () => {
    setExternalServerAdderOpen(true);
  };

  const handleCloseDialogs = () => {
    setServerEditorOpen(false);
    setJsonEditorOpen(false);
    setExternalServerAdderOpen(false);
    setEditingServerId(undefined);
  };
  
  const openExternalLink = (url: string) => {
    if (typeof window !== 'undefined') {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  const [initialized, setInitialized] = useState<boolean>(false);
  const [connectionError, setConnectionError] = useState<boolean>(false);

  // 컴포넌트 마운트 시 백엔드 API와의 연결 확인
  useEffect(() => {
    const checkConnection = async () => {
      try {
        await fetch(`${window.location.protocol}//${window.location.hostname}:8000/health`);
        setInitialized(true);
        setConnectionError(false);
      } catch (err) {
        console.error('Backend connection error:', err);
        setConnectionError(true);
        setInitialized(true);
      }
    };
    
    checkConnection();
  }, []);

  if (!initialized) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (connectionError) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          백엔드 서버에 연결할 수 없습니다!
        </Typography>
        <Typography variant="body1">
          LLMNightRun 백엔드 서버가 실행 중인지 확인하세요.<br />
          다음 명령으로 서버를 시작할 수 있습니다:<br />
          <code>uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload</code>
        </Typography>
      </Alert>
    );
  }

  return (
    <McpProvider>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            MCP 서버 관리
          </Typography>
          
          <ButtonGroup variant="outlined">
            <Button 
              startIcon={<AddIcon />}
              onClick={handleAddServer}
            >
              서버 추가
            </Button>
            <Button 
              startIcon={<EditIcon />}
              onClick={handleOpenJsonEditor}
              color="secondary"
            >
              JSON 직접 편집
            </Button>
            <Button 
              startIcon={<CodeIcon />}
              onClick={handleOpenExternalServerAdder}
              color="primary"
            >
              외부 서버 추가
            </Button>
          </ButtonGroup>
        </Box>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          MCP(Model Context Protocol) 서버를 관리할 수 있는 페이지입니다. 
          MCP를 통해 LLMNightRun에서 외부 데이터 소스, 도구 및 기능에 접근할 수 있습니다.
        </Alert>
        
        <ServerList onEdit={handleEditServer} onAdd={handleAddServer} />
        
        <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" component="h2" gutterBottom>
            MCP란 무엇인가요?
          </Typography>
          <Typography variant="body1" paragraph>
            Model Context Protocol(MCP)은 LLM 애플리케이션에 컨텍스트를 제공하는 방법을 표준화하는 오픈 프로토콜입니다.
            MCP는 LLM이 파일 시스템, 데이터베이스, API 및 다양한 도구와 상호 작용할 수 있게 해주는 통합 레이어를 제공합니다.
          </Typography>
          
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">MCP 서버 유형 및 예시</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    일반적인 MCP 서버 유형:
                  </Typography>
                  <ul>
                    <li>파일 시스템 접근 서버</li>
                    <li>데이터베이스 접근 서버</li>
                    <li>API 통합 서버 (GitHub, Slack 등)</li>
                    <li>검색 및 웹 스크래핑 서버</li>
                    <li>메모리 및 지식 그래프 서버</li>
                    <li>도구 및 유틸리티 서버</li>
                  </ul>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    인기 있는 MCP 서버 예시:
                  </Typography>
                  <ul>
                    <li>@modelcontextprotocol/server-memory</li>
                    <li>@modelcontextprotocol/server-filesystem</li>
                    <li>@modelcontextprotocol/server-github</li>
                    <li>@modelcontextprotocol/server-fetch</li>
                    <li>@modelcontextprotocol/server-postgres</li>
                    <li>@modelcontextprotocol/server-git</li>
                  </ul>
                </Grid>
              </Grid>
              <Box mt={2}>
                <Typography variant="body2">
                  더 많은 MCP 서버는{' '}
                  <Button
                    variant="text"
                    size="small"
                    endIcon={<LaunchIcon fontSize="small" />}
                    onClick={() => openExternalLink('https://modelcontextprotocol.io/examples')}
                    sx={{ p: 0, minWidth: 0, verticalAlign: 'baseline', textTransform: 'none' }}
                  >
                    Model Context Protocol 웹사이트
                  </Button>
                  에서 확인할 수 있습니다.
                </Typography>
              </Box>
            </AccordionDetails>
          </Accordion>
        </Paper>
        
        {/* 다이얼로그 컴포넌트들 */}
        <ServerEditor
          open={serverEditorOpen}
          serverId={editingServerId}
          onClose={handleCloseDialogs}
        />
        
        <JsonConfigEditor 
          open={jsonEditorOpen}
          onClose={handleCloseDialogs}
        />
        
        <ExternalServerAdder
          open={externalServerAdderOpen}
          onClose={handleCloseDialogs}
        />
      </Container>
    </McpProvider>
  );
};
