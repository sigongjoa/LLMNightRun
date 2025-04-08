import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  CardActions, 
  Button,
  IconButton,
  Chip,
  Divider,
  Alert,
  CircularProgress,
  Breadcrumbs,
  Link as MuiLink,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  GitHub as GitHubIcon
} from '@mui/icons-material';
import Head from 'next/head';
import { useRouter } from 'next/router';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import Layout from '../../components/Layout';
import { useMcp } from '../../contexts/McpContext';
import { McpProvider } from '../../contexts/McpContext';
import { ServerInfo } from '../../utils/mcp/api';

interface ToolInfo {
  name: string;
  description: string;
  server: string;
  schema?: any;
}

const McpTools: React.FC = () => {
  const router = useRouter();
  const { servers, isLoading, error, refreshServers, startServer } = useMcp();
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loadingTools, setLoadingTools] = useState<boolean>(false);
  const [toolError, setToolError] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<ToolInfo | null>(null);
  const [toolDialogOpen, setToolDialogOpen] = useState<boolean>(false);

  // 서버 시작 핸들러
  const handleStartServer = async (serverId: string) => {
    try {
      await startServer(serverId);
    } catch (err) {
      console.error('Error starting server:', err);
    }
  };

  // 도구 목록 새로고침
  const fetchTools = async () => {
    setLoadingTools(true);
    setToolError(null);
    
    try {
      // 여기서는 가상 데이터를 사용합니다. 실제로는 API를 호출하여 데이터를 가져와야 합니다.
      // 이 부분은 실제 MCP 도구 API가 구현된 후에 대체해야 합니다.
      const mockTools: ToolInfo[] = [
        // 파일 시스템 도구
        {
          name: 'read_file',
          description: '파일 내용 읽기',
          server: 'filesystem',
          schema: {
            type: 'object',
            properties: {
              path: { type: 'string', description: '파일 경로' }
            },
            required: ['path']
          }
        },
        {
          name: 'write_file',
          description: '파일에 내용 쓰기',
          server: 'filesystem',
          schema: {
            type: 'object',
            properties: {
              path: { type: 'string', description: '파일 경로' },
              content: { type: 'string', description: '파일 내용' }
            },
            required: ['path', 'content']
          }
        },
        {
          name: 'list_directory',
          description: '디렉토리 내용 나열',
          server: 'filesystem',
          schema: {
            type: 'object',
            properties: {
              path: { type: 'string', description: '디렉토리 경로' }
            },
            required: ['path']
          }
        },
        
        // GitHub 도구
        {
          name: 'github_search_repository',
          description: 'GitHub 저장소 검색',
          server: 'github-api',
          schema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: '검색어' },
              language: { type: 'string', description: '프로그래밍 언어 필터' }
            },
            required: ['query']
          }
        },
        {
          name: 'github_create_issue',
          description: 'GitHub 이슈 생성',
          server: 'github-api',
          schema: {
            type: 'object',
            properties: {
              owner: { type: 'string', description: '저장소 소유자' },
              repo: { type: 'string', description: '저장소 이름' },
              title: { type: 'string', description: '이슈 제목' },
              body: { type: 'string', description: '이슈 내용' }
            },
            required: ['owner', 'repo', 'title']
          }
        },
        
        // 메모리 도구
        {
          name: 'memory_store',
          description: '메모리에 정보 저장',
          server: 'memory',
          schema: {
            type: 'object',
            properties: {
              key: { type: 'string', description: '키' },
              value: { type: 'string', description: '값' }
            },
            required: ['key', 'value']
          }
        },
        {
          name: 'memory_retrieve',
          description: '메모리에서 정보 검색',
          server: 'memory',
          schema: {
            type: 'object',
            properties: {
              key: { type: 'string', description: '키' }
            },
            required: ['key']
          }
        },
        {
          name: 'memory_search',
          description: '메모리에서 패턴으로 검색',
          server: 'memory',
          schema: {
            type: 'object',
            properties: {
              pattern: { type: 'string', description: '검색 패턴' }
            },
            required: ['pattern']
          }
        }
      ];
      
      // 일반적으로 실행 중인 서버에서만 도구를 가져옵니다
      const runningServers = servers.filter(s => s.running).map(s => s.id);
      const availableTools = mockTools.filter(tool => runningServers.includes(tool.server));
      
      setTools(availableTools);
    } catch (err) {
      console.error('Error fetching tools:', err);
      setToolError('도구 목록을 가져오는 중 오류가 발생했습니다.');
    } finally {
      setLoadingTools(false);
    }
  };

  // 서버 상태가 변경될 때마다 도구 목록을 업데이트
  useEffect(() => {
    if (!isLoading) {
      fetchTools();
    }
  }, [isLoading, servers]);

  // 도구 선택 핸들러
  const handleSelectTool = (tool: ToolInfo) => {
    setSelectedTool(tool);
    setToolDialogOpen(true);
  };

  // 도구 상세 Dialog 닫기
  const handleCloseToolDialog = () => {
    setToolDialogOpen(false);
    setSelectedTool(null);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          MCP 도구
        </Typography>
        
        <Button 
          startIcon={<RefreshIcon />}
          variant="outlined"
          onClick={fetchTools}
          disabled={loadingTools}
        >
          {loadingTools ? <CircularProgress size={24} /> : '도구 새로고침'}
        </Button>
      </Box>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        MCP 서버에서 제공하는 도구를 통해 LLM과 다양한 외부 시스템을 연동할 수 있습니다.
        아래에서 실행 중인 서버의 도구를 확인하고 사용해보세요.
      </Alert>

      {/* 서버 상태 섹션 */}
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          MCP 서버 상태
        </Typography>
        
        {isLoading ? (
          <Box display="flex" justifyContent="center" my={3}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={2}>
            {servers.length === 0 ? (
              <Grid item xs={12}>
                <Alert severity="warning">
                  등록된 MCP 서버가 없습니다. 
                  <Box component="span" ml={1}>
                    <MuiLink 
                      sx={{ cursor: 'pointer' }}
                      onClick={() => router.push('/mcp')}
                    >
                      MCP 서버 관리 페이지
                    </MuiLink>
                  </Box>
                  에서 서버를 추가하세요.
                </Alert>
              </Grid>
            ) : (
              servers.map((server: ServerInfo) => (
                <Grid item xs={12} sm={6} md={4} key={server.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {server.id}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {server.command} {server.args.join(' ')}
                      </Typography>
                      <Box mt={1}>
                        <Chip
                          label={server.running ? '실행 중' : '중지됨'}
                          color={server.running ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </CardContent>
                    <CardActions>
                      {!server.running && (
                        <Button 
                          size="small" 
                          startIcon={<StartIcon />}
                          onClick={() => handleStartServer(server.id)}
                        >
                          시작
                        </Button>
                      )}
                      <Button 
                        size="small"
                        onClick={() => router.push('/mcp')}
                      >
                        관리
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        )}
      </Paper>

      {/* 도구 목록 섹션 */}
      <Paper elevation={2} sx={{ p: 2 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          사용 가능한 도구
        </Typography>
        
        {loadingTools ? (
          <Box display="flex" justifyContent="center" my={3}>
            <CircularProgress />
          </Box>
        ) : toolError ? (
          <Alert severity="error">{toolError}</Alert>
        ) : tools.length === 0 ? (
          <Alert severity="info">
            사용 가능한 도구가 없습니다. MCP 서버를 시작하거나 새로고침 버튼을 클릭하세요.
          </Alert>
        ) : (
          <Grid container spacing={2}>
            {tools.map((tool) => (
              <Grid item xs={12} sm={6} md={4} key={tool.name}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom noWrap>
                      {tool.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {tool.description}
                    </Typography>
                    <Box mt={1}>
                      <Chip
                        label={`서버: ${tool.server}`}
                        size="small"
                        color="primary"
                      />
                    </Box>
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      startIcon={<InfoIcon />}
                      onClick={() => handleSelectTool(tool)}
                    >
                      상세 정보
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* 도구 상세 다이얼로그 */}
      <Dialog open={toolDialogOpen} onClose={handleCloseToolDialog} maxWidth="md" fullWidth>
        {selectedTool && (
          <>
            <DialogTitle>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">{selectedTool.name}</Typography>
                <Chip label={`서버: ${selectedTool.server}`} size="small" color="primary" />
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              <Typography variant="subtitle1" gutterBottom>
                설명
              </Typography>
              <Typography variant="body2" paragraph>
                {selectedTool.description}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                입력 스키마
              </Typography>
              {selectedTool.schema ? (
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                  <pre style={{ margin: 0, overflowX: 'auto' }}>
                    {JSON.stringify(selectedTool.schema, null, 2)}
                  </pre>
                </Paper>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  스키마 정보가 없습니다.
                </Typography>
              )}
              
              <Box mt={3}>
                <Typography variant="subtitle1" gutterBottom>
                  도구 테스트
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  이 기능은 추후 업데이트에서 제공될 예정입니다.
                </Alert>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseToolDialog}>닫기</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default function McpToolsPage() {
  const router = useRouter();
  
  return (
    <Layout>
      <Head>
        <title>MCP 도구 - LLMNightRun</title>
      </Head>
      
      <Box sx={{ py: 2, px: 3 }}>
        <Breadcrumbs 
          separator={<NavigateNextIcon fontSize="small" />}
          aria-label="breadcrumb"
          sx={{ mb: 2 }}
        >
          <MuiLink 
            color="inherit" 
            underline="hover"
            component="button"
            onClick={() => router.push('/')}
            sx={{ 
              textAlign: 'left',
              background: 'none',
              border: 'none',
              padding: 0,
              cursor: 'pointer'
            }}
          >
            홈
          </MuiLink>
          <Typography color="text.primary">MCP 도구</Typography>
        </Breadcrumbs>
        
        <McpProvider>
          <McpTools />
        </McpProvider>
      </Box>
    </Layout>
  );
}
