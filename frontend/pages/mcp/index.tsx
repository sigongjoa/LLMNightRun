import React from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { Box, Breadcrumbs, Typography, Link as MuiLink } from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { useRouter } from 'next/router';
import { McpServerManager } from '../../components/MCP/McpServerManager';
import Layout from '../../components/Layout';

const MCPPage: NextPage = () => {
  const router = useRouter();
  
  return (
    <Layout>
      <Head>
        <title>MCP 서버 관리 | LLMNightRun</title>
        <meta name="description" content="LLMNightRun의 Model Context Protocol 서버 관리 페이지" />
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
          <Typography color="text.primary">MCP 서버 관리</Typography>
        </Breadcrumbs>
        
        <McpServerManager />
      </Box>
    </Layout>
  );
};

export default MCPPage;