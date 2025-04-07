import React from 'react';
import { 
  Container, 
  Typography, 
  Box,
  Breadcrumbs,
  Link as MuiLink
} from '@mui/material';
import Head from 'next/head';
import Link from 'next/link';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { McpServerManager } from '../../components/mcp/McpServerManager';
import Layout from '../../components/Layout';

export default function McpPage() {
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
          <Link href="/" passHref>
            <MuiLink color="inherit" underline="hover">
              홈
            </MuiLink>
          </Link>
          <Typography color="text.primary">MCP 서버 관리</Typography>
        </Breadcrumbs>
        
        <McpServerManager />
      </Box>
    </Layout>
  );
}
