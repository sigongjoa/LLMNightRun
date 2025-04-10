import React, { useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Container, Box, Alert, Typography } from '@mui/material';
import LoginForm from '../components/auth/LoginForm';
import { useAuth } from '../components/auth/AuthProvider';

const LoginPage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { registered, reset } = router.query;

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
        <title>로그인 - LLMNightRun</title>
        <meta name="description" content="LLMNightRun 로그인 페이지" />
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

        {registered && (
          <Alert severity="success" sx={{ mb: 3 }}>
            회원가입이 완료되었습니다. 이제 로그인하실 수 있습니다.
          </Alert>
        )}
        
        {reset && (
          <Alert severity="success" sx={{ mb: 3 }}>
            비밀번호가 성공적으로 재설정되었습니다. 새로운 비밀번호로 로그인하세요.
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <LoginForm />
        </Box>
      </Container>
    </>
  );
};

export default LoginPage;
