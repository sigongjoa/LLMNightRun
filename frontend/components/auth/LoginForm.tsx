import React, { useState } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress,
  Alert,
  Link as MuiLink
} from '@mui/material';
import Link from 'next/link';
import { useAuth } from './AuthProvider';

const LoginForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formErrors, setFormErrors] = useState<{username?: string; password?: string}>({});
  const { login, isLoading, error } = useAuth();

  const validateForm = (): boolean => {
    const errors: {username?: string; password?: string} = {};
    let isValid = true;

    if (!username.trim()) {
      errors.username = '사용자 이름을 입력하세요';
      isValid = false;
    }

    if (!password) {
      errors.password = '비밀번호를 입력하세요';
      isValid = false;
    }

    setFormErrors(errors);
    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      try {
        await login(username, password);
      } catch (error) {
        // login 함수 내에서 오류 처리
      }
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 400, width: '100%' }}>
      <Typography variant="h5" component="h1" gutterBottom align="center">
        로그인
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {/* 404 오류를 식별하고 사용자 치는 안내 메시지 표시 */}
      {error && error.includes('로그인 서비스에 연결할 수 없습니다') && (
        <Alert severity="info" sx={{ mb: 2 }}>
          서버가 시작되지 않았거나 연결이 안 될 수 있습니다. 터미널에서 <strong>python run_backend_fix.py</strong> 명령어를 실행해보세요.
        </Alert>
      )}
      
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <TextField
          margin="normal"
          required
          fullWidth
          id="username"
          label="사용자 이름"
          name="username"
          autoComplete="username"
          autoFocus
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          error={!!formErrors.username}
          helperText={formErrors.username}
          disabled={isLoading}
        />
        <TextField
          margin="normal"
          required
          fullWidth
          name="password"
          label="비밀번호"
          type="password"
          id="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={!!formErrors.password}
          helperText={formErrors.password}
          disabled={isLoading}
        />
        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
          disabled={isLoading}
        >
          {isLoading ? <CircularProgress size={24} /> : '로그인'}
        </Button>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Link href="/register" legacyBehavior passHref>
            <MuiLink variant="body2">
              계정이 없으신가요? 회원가입
            </MuiLink>
          </Link>
          <Link href="/reset-password" legacyBehavior passHref>
            <MuiLink variant="body2">
              비밀번호 찾기
            </MuiLink>
          </Link>
        </Box>
      </Box>
    </Paper>
  );
};

export default LoginForm;
