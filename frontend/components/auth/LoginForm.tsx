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
      
      {/* 서버 연결 오류 식별 및 안내 메시지 표시 */}
      {error && error.includes('로그인 서비스에 연결할 수 없습니다') && (
        <Alert severity="info" sx={{ mb: 2 }}>
          서버가 시작되지 않았거나 연결이 안 될 수 있습니다. 터미널에서 <strong>uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload</strong> 명령어를 실행해보세요.
        </Alert>
      )}
      
      {/* 인증 오류 정보 양식 안내 */}
      {error && error.includes('아이디 또는 비밀번호가 일치하지 않습니다') && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          입력하신 사용자 이름과 비밀번호를 확인해주세요. 
          <br /><br />
          <Button 
            variant="outlined" 
            color="primary" 
            size="small"
            onClick={async () => {
              try {
                const response = await fetch('http://localhost:8000/initialize-db', {
                  method: 'POST',
                });
                const responseData = await response.json();
                alert(responseData.message);
              } catch (err) {
                alert('데이터베이스 초기화 중 오류가 발생했습니다.');
                console.error(err);
              }
            }}
          >
            데이터베이스 초기화
          </Button>
          <Typography variant="caption" display="block" mt={1}>
            위 버튼을 클릭하면 데이터베이스가 초기화되고 테스트 계정(admin/admin123)이 생성됩니다.
          </Typography>
        </Alert>
      )}
      
      {/* 사용자 안내 메시지 - 테스트 계정 정보 */}
      <Alert severity="info" sx={{ mb: 2 }}>
        테스트 계정: <strong>user / user123</strong> 또는 <strong>admin / admin123</strong>
        <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center' }}>
          <Button 
            variant="contained" 
            color="primary"
            size="small"
            onClick={async () => {
              try {
                // JSON 데이터로 보내기
                const data = {
                  username: 'admin',
                  password: 'admin123'
                };
                
                // 단순 로그인 API 호출
                const response = await fetch('http://localhost:8000/simple-login', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify(data)
                });
                
                const responseData = await response.json();
                
                if (responseData.access_token) {
                  // 토큰 저장
                  localStorage.setItem('token', responseData.access_token);
                  
                  // 성공 메시지 표시
                  alert(`관리자 계정으로 로그인 성공!`);
                  
                  // 페이지 새로고침
                  window.location.href = '/';
                } else {
                  alert(`로그인 실패: ${data.detail || '알 수 없는 오류'}`);
                }
              } catch (err) {
                alert('로그인 중 오류가 발생했습니다.');
                console.error(err);
              }
            }}
          >
            관리자로 로그인
          </Button>
          <Button 
            variant="outlined" 
            color="primary"
            size="small"
            sx={{ ml: 2 }}
            onClick={async () => {
              try {
                // JSON 데이터로 보내기
                const data = {
                  username: 'user',
                  password: 'user123'
                };
                
                // 단순 로그인 API 호출
                const response = await fetch('http://localhost:8000/simple-login', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify(data)
                });
                
                const responseData = await response.json();
                
                if (responseData.access_token) {
                  // 토큰 저장
                  localStorage.setItem('token', responseData.access_token);
                  
                  // 성공 메시지 표시
                  alert(`일반 사용자 계정으로 로그인 성공!`);
                  
                  // 페이지 새로고침
                  window.location.href = '/';
                } else {
                  alert(`로그인 실패: ${data.detail || '알 수 없는 오류'}`);
                }
              } catch (err) {
                alert('로그인 중 오류가 발생했습니다.');
                console.error(err);
              }
            }}
          >
            일반 사용자로 로그인
          </Button>
        </Box>
      </Alert>

      {/* 대체 로그인 방법 */}
      <Alert severity="warning" sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          기존 로그인이 작동하지 않을 경우 아래 방법을 시도해 보세요:
        </Typography>
        <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center' }}>
          <Button 
            variant="contained" 
            color="warning"
            size="small"
            onClick={() => {
              try {
                // 백엔드 의존 없이 세션 스토리지에 직접 저장
                sessionStorage.setItem('user', JSON.stringify({
                  username: 'admin',
                  is_admin: true
                }));
                
                // 비상 로그인 플래그 설정
                sessionStorage.setItem('emergency_login', 'true');
                
                alert('비상 로그인 성공! 관리자로 로그인되었습니다. (오프라인 모드)');
                window.location.href = '/';
              } catch (err) {
                console.error('비상 로그인 오류:', err);
                alert('비상 로그인 처리 중 오류가 발생했습니다.');
              }
            }}
          >
            비상 로그인 (관리자)
          </Button>
        </Box>
      </Alert>
      
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