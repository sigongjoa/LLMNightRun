import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Button, Container, Typography, Paper } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // 다음 렌더링에서 폴백 UI가 보이도록 상태를 업데이트합니다.
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 에러 리포팅 서비스에 에러를 기록할 수도 있습니다.
    console.error('ErrorBoundary caught an error', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleResetError = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      // 사용자 정의 폴백 UI를 반환하거나 기본 폴백 UI를 표시합니다.
      if (fallback) {
        return fallback;
      }

      return (
        <Container maxWidth="md" sx={{ my: 4 }}>
          <Paper 
            elevation={3} 
            sx={{ 
              p: 4, 
              textAlign: 'center',
              border: '1px solid',
              borderColor: 'error.main',
              borderRadius: 2,
            }}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
              <ErrorOutlineIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
              <Typography variant="h5" component="h2" color="error" gutterBottom>
                문제가 발생했습니다
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                애플리케이션에서 오류가 발생했습니다. 이 페이지를 다시 로드하거나 홈으로 돌아가보세요.
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
              <Button variant="contained" color="primary" onClick={this.handleResetError}>
                다시 시도
              </Button>
              <Button variant="outlined" color="primary" href="/">
                홈으로
              </Button>
            </Box>

            {process.env.NODE_ENV !== 'production' && (
              <Box sx={{ mt: 4, textAlign: 'left' }}>
                <Typography variant="h6" color="error" gutterBottom>
                  오류 세부 정보:
                </Typography>
                <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.100', overflowX: 'auto' }}>
                  <Typography variant="body2" component="pre">
                    {error?.toString()}
                    {errorInfo?.componentStack}
                  </Typography>
                </Paper>
              </Box>
            )}
          </Paper>
        </Container>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
