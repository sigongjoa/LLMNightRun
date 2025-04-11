import React, { useEffect, useState } from 'react';
import type { AppProps } from 'next/app';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useRouter } from 'next/router';
import { AuthProvider } from '../components/auth/AuthProvider';
import '../styles/globals.css';

// 테마 설정
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#f50057',
    },
  },
  typography: {
    fontFamily: [
      'Noto Sans KR',
      'Roboto',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

// 간단한 래퍼 컴포넌트 
const SimpleLayout = ({ children }) => <>{children}</>;

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  
  // 클라이언트 사이드에서 컴포넌트가 마운트된 후 상태 업데이트
  useEffect(() => {
    setMounted(true);
  }, []);

  // 서버 사이드 렌더링 동안에는 SimpleLayout 사용
  // 클라이언트 사이드에서만 실제 Layout 로드
  if (!mounted) {
    // 첫 번째 렌더링에서는 간단한 레이아웃만 사용
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <SimpleLayout>
            <Component {...pageProps} />
          </SimpleLayout>
        </AuthProvider>
      </ThemeProvider>
    );
  }

  // 클라이언트 사이드에서만 실행
  let Layout = SimpleLayout;
  
  // 로그인, 회원가입 등 인증 페이지에서는 Layout을 적용하지 않습니다
  const authPages = ['/login', '/register', '/reset-password'];
  const withoutLayout = authPages.includes(router.pathname);
  
  try {
    // 마운트된 후에만 Layout 로드 시도
    const LayoutComponent = require('../components/Layout').default;
    
    // Layout 할당 (인증 페이지가 아닐 경우에만)
    if (!withoutLayout) {
      Layout = LayoutComponent;
    }
  } catch (e) {
    console.error('Layout 컴포넌트 로딩 오류:', e);
    // 오류 발생 시 기본 래퍼 사용
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </AuthProvider>
    </ThemeProvider>
  );
}