import React from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { Box, Container } from '@mui/material';
import Layout from '../components/Layout';
import { MemoryDashboard } from '../components/Memory';

const MemoryManagerPage: NextPage = () => {
  return (
    <>
      <Head>
        <title>메모리 관리 - LLMNightRun</title>
        <meta name="description" content="LLM 메모리 관리 및 Vector DB 연동 시스템" />
      </Head>
      <Layout>
        <Container maxWidth="xl">
          <MemoryDashboard />
        </Container>
      </Layout>
    </>
  );
};

export default MemoryManagerPage;