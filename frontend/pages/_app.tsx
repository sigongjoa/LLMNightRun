import { useEffect } from 'react';
import type { AppProps } from 'next/app';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button, Snackbar, Alert } from '@mui/material';
import { useState } from 'react';
import { useRouter } from 'next/router';
import { updateApiBaseURLIfNeeded } from '../utils/api';
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

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [serverError, setServerError] = useState<boolean>(false);
  const [snackbar, setSnackbar] = useState<{open: boolean, message: string, severity: 'info' | 'success' | 'warning' | 'error'}>({
    open: false,
    message: '',
    severity: 'info'
  });

  // 앱 초기화 시 서버 연결 상태 확인
  useEffect(() => {
    const checkServerConnection = async () => {
      try {
        // 서버 상태 확인 및 필요시 URL 업데이트
        await updateApiBaseURLIfNeeded();
        
        // 로컬 스토리지의 인증 토큰이 있는지 확인
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('token');
          
          // 로그인 페이지나 회원가입 페이지가 아니고 토큰이 없으면 로그인 페이지로 리디렉트
          if (!token && router.pathname !== '/login' && router.pathname !== '/register') {
            router.push('/login');
          }
        }
      } catch (error) {
        console.error('서버 연결 오류:', error);
        setServerError(true);
      }
    };

    checkServerConnection();
    
    // 주기적으로 서버 상태 확인 (60초마다)
    const intervalId = setInterval(async () => {
      try {
        await updateApiBaseURLIfNeeded();
        
        // 이전에 서버 오류가 있었다면 해결된 것으로 표시
        if (serverError) {
          setServerError(false);
          setSnackbar({
            open: true,
            message: '서버 연결이 복구되었습니다.',
            severity: 'success'
          });
        }
      } catch (error) {
        console.error('서버 연결 확인 오류:', error);
        
        // 이전에 오류가 없었다면 알림 표시
        if (!serverError) {
          setServerError(true);
        }
      }
    }, 60000); // 60초
    
    return () => clearInterval(intervalId);
  }, [router, serverError]);

  // 스낵바 닫기 핸들러
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // 서버 오류 대화 상자 닫기 핸들러
  const handleCloseErrorDialog = () => {
    setServerError(false);
  };

  // 서버 다시 연결 시도
  const handleRetryConnection = async () => {
    setServerError(false);
    try {
      await updateApiBaseURLIfNeeded();
      setSnackbar({
        open: true,
        message: '서버 연결 시도 중...',
        severity: 'info'
      });
    } catch (error) {
      console.error('서버 재연결 시도 실패:', error);
      setServerError(true);
    }
  };

  // 로그인, 회원가입 등 인증 페이지에서는 Layout을 적용하지 않습니다
  const authPages = ['/login', '/register', '/reset-password'];
  const withoutLayout = authPages.includes(router.pathname);

  // Layout 컴포넌트 동적 임포트
  const Layout = (withoutLayout) ? 
    ({ children }) => <>{children}</> :  // 인증 페이지일 경우 단순 렌더링
    require('../components/Layout').default;  // 그 외의 경우 Layout 적용

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </AuthProvider>
      
      {/* 서버 오류 대화 상자 */}
      <Dialog
        open={serverError}
        onClose={handleCloseErrorDialog}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">
          {"서버 연결 오류"}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.
            <br /><br />
            다음 단계를 시도해 보세요:
            <br />
            1. 백엔드 서버가 실행 중인지 확인
            <br />
            2. 네트워크 연결 확인
            <br />
            3. 브라우저 새로고침
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseErrorDialog}>무시</Button>
          <Button onClick={handleRetryConnection} autoFocus color="primary">
            다시 연결
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 알림 스낵바 */}
      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
}
