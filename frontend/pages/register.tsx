import React, { useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Container, Box, Typography } from '@mui/material';
import RegisterForm from '../components/auth/RegisterForm';
import { useAuth } from '../components/auth/AuthProvider';

const RegisterPage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // 이미 로그인한 사용자는 대시보드로 리디렉션
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/');
    }
  }, [isLoading, isAuthenticated, router]);

  // 로딩 중이거나 이미 인증된 상태면 내용을 숨김
  if (isLoading || isAuthenticated) {
    return null;
  }

  return (
    <>
      <Head>
        <title>회원가입 - LLMNightRun</title>
        <meta name="description" content="LLMNightRun 회원가입 페이지" />
      </Head>
      
      <Container maxWidth="sm" sx={{ pt: { xs: 4, sm: 8 } }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            LLMNightRun
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            멀티 LLM 통합 자동화 플랫폼
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <RegisterForm />
        </Box>
      </Container>
    </>
  );
};

export default RegisterPage;
