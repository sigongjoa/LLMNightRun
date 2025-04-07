import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Layout from '@/components/Layout'
import { useEffect } from 'react'

// 테마 정의
const theme = createTheme({
  palette: {
    primary: {
      main: '#3f51b5',
    },
    secondary: {
      main: '#f50057',
    },
  },
})

// 전역 타입 선언 추가
declare global {
  interface Window {
    MCP: any;
  }
}

export default function App({ Component, pageProps }: AppProps) {
  // MCP 유틸리티 로드
  useEffect(() => {
    // 클라이언트 사이드에서만 실행
    if (typeof window !== 'undefined') {
      // 전역 MCP 객체 초기화
      window.MCP = window.MCP || {};
      
      // 터미널 모듈 임포트
      import('@/utils/mcp/terminal').then((module) => {
        window.MCP.terminal = module.default;
        console.log('[MCP] 터미널 모듈 로드됨');
      }).catch(err => {
        console.error('[MCP] 터미널 모듈 로드 오류:', err);
      });
    }
  }, []);
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </ThemeProvider>
  )
}