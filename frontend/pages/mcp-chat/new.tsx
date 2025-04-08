import React from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { Box, Typography } from '@mui/material';
import dynamic from 'next/dynamic';

// 클라이언트 사이드에서만 로드하도록 설정
const MCPChatInterface = dynamic(
  () => import('../../components/Chat/MCPChatInterface'),
  { ssr: false }
);

const MCPChatNewPage: NextPage = () => {
  return (
    <>
      <Head>
        <title>MCP 통합 대화 | LLMNightRun</title>
        <meta name="description" content="LLMNightRun의 Model Context Protocol 기반 대화 인터페이스" />
      </Head>
      
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: 'calc(100vh - 120px)', 
        overflow: 'hidden',
        p: 0,
        pt: 1
      }}>
        <Box sx={{ flexGrow: 1, display: 'flex', overflow: 'hidden' }}>
          <MCPChatInterface />
        </Box>
      </Box>
    </>
  );
};

export default MCPChatNewPage;