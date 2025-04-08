import React from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Grid,
  Divider
} from '@mui/material';
import AgentConsole from '../components/Agent';

const AgentPage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
        MCP 에이전트
        </Typography>
        
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="body1" paragraph>
        MCP(Model Context Protocol) 에이전트는 다양한 도구와 리소스를 활용하여 복잡한 작업을 수행할 수 있는 AI 에이전트입니다.
        코드 작성, 파일 편집, 데이터베이스 조회, GitHub 저장소 관리 등의 작업을 수행할 수 있습니다.
        </Typography>
          
          <Typography variant="h6" gutterBottom>
            주요 기능
          </Typography>
          
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={3}>
              <Box>
                <Typography variant="subtitle1">🔍 파일 시스템 탐색</Typography>
                <Typography variant="body2" color="text.secondary">
                  파일 시스템을 탐색하고 파일을 관리합니다.
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box>
                <Typography variant="subtitle1">💻 Python 코드 실행</Typography>
                <Typography variant="body2" color="text.secondary">
                  샌드박스에서 안전하게 Python 코드를 실행합니다.
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box>
                <Typography variant="subtitle1">📝 파일 편집</Typography>
                <Typography variant="body2" color="text.secondary">
                  텍스트 파일을 생성하고 편집할 수 있습니다.
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box>
                <Typography variant="subtitle1">🌐 GitHub 연동</Typography>
                <Typography variant="body2" color="text.secondary">
                  GitHub 저장소에 파일을 업로드하고 PR을 생성할 수 있습니다.
                </Typography>
              </Box>
            </Grid>
          </Grid>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle2" color="text.secondary">
            에이전트에게 간단한 질문이나 복잡한 코드 작업을 요청해보세요.
          </Typography>
        </Paper>
        
        <Box sx={{ height: '70vh' }}>
          <AgentConsole />
        </Box>
      </Box>
    </Container>
  );
};

export default AgentPage;