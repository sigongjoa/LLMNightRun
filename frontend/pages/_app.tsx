import React, { useEffect, ReactElement, ReactNode } from 'react';
import type { AppProps } from 'next/app';
import type { NextComponentType } from 'next';
import { CacheProvider, EmotionCache } from '@emotion/react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import Head from 'next/head';
import theme from '../styles/theme';
import createEmotionCache from '../utils/createEmotionCache';
import Layout from '../components/Layout';
import '../styles/globals.css';

// Client-side cache, shared for the whole session of the user in the browser.
const clientSideEmotionCache = createEmotionCache();

interface MyAppProps extends AppProps {
  emotionCache?: EmotionCache;
  Component: NextComponentType & {
    getLayout?: (page: ReactElement) => ReactNode;
  };
}

export default function MyApp({
  Component,
  emotionCache = clientSideEmotionCache,
  pageProps,
}: MyAppProps) {
  // 중복 레이아웃 문제를 방지하기 위한 cleanup
  useEffect(() => {
    // 클라이언트 측에서만 실행
    if (typeof window !== 'undefined') {
      // 기존 중복 요소를 정리하기 위한 코드
      const cleanup = () => {
        // 중복된 요소 제거
        const headers = document.querySelectorAll('header');
        if (headers.length > 1) {
          // 첫 번째를 제외한 중복된 헤더 제거
          for (let i = 1; i < headers.length; i++) {
            headers[i].classList.add('dup-hidden');
          }
        }
        
        // 네비게이션 메뉴 캐시 새로 고침
        const navButtons = document.querySelectorAll('.MuiToolbar-root .MuiButton-root');
        navButtons.forEach(button => {
          const href = button.getAttribute('data-href');
          if (href && window.location.pathname === href) {
            button.classList.add('Mui-active');
          }
        });
      };
      
      // 페이지 로드 후 cleanup 실행
      cleanup();
      
      // DOM 변경 반영을 위해 짧은 지연 후 다시 실행
      const timeoutId = setTimeout(cleanup, 100);
      
      return () => clearTimeout(timeoutId);
    }
  }, []);
  
  return (
    <CacheProvider value={emotionCache}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Head>
          {/* 모든 페이지에 공통으로 필요한 폰트 추가 */}
          <link
            href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap"
            rel="stylesheet"
          />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        </Head>
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </ThemeProvider>
    </CacheProvider>
  );
}
