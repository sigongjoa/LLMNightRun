import React, { useState } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Button, 
  Grid,
  Alert,
  Divider,
  Link,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { ServerList } from './ServerList';
import { ServerEditor } from './ServerEditor';
import { McpProvider } from '../../contexts/McpContext';

export const McpServerManager: React.FC = () => {
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [editingServerId, setEditingServerId] = useState<string | undefined>(undefined);

  const handleAddServer = () => {
    setEditingServerId(undefined);
    setDialogOpen(true);
  };

  const handleEditServer = (serverId: string) => {
    setEditingServerId(serverId);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingServerId(undefined);
  };

  return (
    <McpProvider>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          MCP 서버 관리
        </Typography>
        
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
                  <Link href="https://modelcontextprotocol.io/examples" target="_blank" rel="noopener">
                    Model Context Protocol 웹사이트
                  </Link>
                  에서 확인할 수 있습니다.
                </Typography>
              </Box>
            </AccordionDetails>
          </Accordion>
        </Paper>
        
        <ServerEditor
          open={dialogOpen}
          serverId={editingServerId}
          onClose={handleCloseDialog}
        />
      </Container>
    </McpProvider>
  );
};
