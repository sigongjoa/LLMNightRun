import React from 'react';
import Layout from '../components/Layout';
import dynamic from 'next/dynamic';

// 클라이언트 사이드에서만 로드하도록 설정
const MCPChatInterface = dynamic(
  () => import('../components/Chat/MCPChatInterface'),
  { ssr: false }
);
import { Box, Typography, Paper } from '@mui/material';

const MCPChatPage = () => {
  return (
    <Layout>
      <Box sx={{ height: 'calc(100vh - 120px)', p: 2 }}>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            MCP 통합 대화
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Model Context Protocol을 통해 LM Studio와 연결된 채팅 인터페이스입니다. 
            파일 조작, 코드 분석 등 다양한 도구를 사용해보세요.
          </Typography>
        </Box>
        
        <Paper 
          elevation={0} 
          variant="outlined" 
          sx={{ 
            height: 'calc(100% - 80px)', 
            borderRadius: 3,
            overflow: 'hidden'
          }}
        >
          <MCPChatInterface />
        </Paper>
      </Box>
    </Layout>
  );
};

export default MCPChatPage;