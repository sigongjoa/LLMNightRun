import React from 'react';
import { 
  Container, 
  Typography, 
  Box,
  Breadcrumbs,
  Link as MuiLink
} from '@mui/material';
import Head from 'next/head';
import { useRouter } from 'next/router';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { McpServerManager } from '../../components/mcp/McpServerManager';
import Layout from '../../components/Layout';

export default function McpPage() {
  const router = useRouter();
  
  return (
    <Layout>
      <Head>
        <title>MCP 서버 관리 - LLMNightRun</title>
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
}
