import React, { useState } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress,
  Alert,
  Link as MuiLink,
  Grid
} from '@mui/material';
import Link from 'next/link';
import { useAuth } from './AuthProvider';

const RegisterForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [formErrors, setFormErrors] = useState<{
    username?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});
  
  const { register, isLoading, error } = useAuth();

  const validateForm = (): boolean => {
    const errors: {
      username?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};
    let isValid = true;

    // 사용자명 검증
    if (!username.trim()) {
      errors.username = '사용자 이름을 입력하세요';
      isValid = false;
    } else if (!/^[a-zA-Z0-9\-_.]+$/.test(username)) {
      errors.username = '영문, 숫자, 특수문자(-, _, .)만 사용할 수 있습니다';
      isValid = false;
    }

    // 이메일 검증
    if (!email.trim()) {
      errors.email = '이메일을 입력하세요';
      isValid = false;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = '올바른 이메일 형식이 아닙니다';
      isValid = false;
    }

    // 비밀번호 검증
    if (!password) {
      errors.password = '비밀번호를 입력하세요';
      isValid = false;
    } else if (password.length < 8) {
      errors.password = '비밀번호는 8자 이상이어야 합니다';
      isValid = false;
    } else {
      // 비밀번호 강도 검증 (대문자, 소문자, 숫자, 특수문자 중 3가지 이상)
      const hasUpper = /[A-Z]/.test(password);
      const hasLower = /[a-z]/.test(password);
      const hasNumber = /[0-9]/.test(password);
      const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
      
      const categories = [hasUpper, hasLower, hasNumber, hasSpecial];
      const categoriesCount = categories.filter(Boolean).length;
      
      if (categoriesCount < 3) {
        errors.password = '비밀번호는 대문자, 소문자, 숫자, 특수문자 중 3가지 이상을 포함해야 합니다';
        isValid = false;
      }
    }

    // 비밀번호 확인 검증
    if (!confirmPassword) {
      errors.confirmPassword = '비밀번호 확인을 입력하세요';
      isValid = false;
    } else if (password !== confirmPassword) {
      errors.confirmPassword = '비밀번호가 일치하지 않습니다';
      isValid = false;
    }

    setFormErrors(errors);
    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      try {
        await register(username, email, password, firstName, lastName);
        setSuccessMessage('회원가입이 성공적으로 완료되었습니다. 잠시 후 로그인 페이지로 이동합니다.');
        
        // 3초 후 로그인 페이지로 자동 이동
        setTimeout(() => {
          window.location.href = '/login?registered=true';
        }, 3000);
      } catch (error) {
        // register 함수 내에서 오류 처리
      }
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 600, width: '100%' }}>
      <Typography variant="h5" component="h1" gutterBottom align="center">
        회원가입
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}
      
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              id="username"
              label="사용자 이름"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              error={!!formErrors.username}
              helperText={formErrors.username}
              disabled={isLoading || !!successMessage}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              id="email"
              label="이메일"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={!!formErrors.email}
              helperText={formErrors.email}
              disabled={isLoading || !!successMessage}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              id="firstName"
              label="이름 (선택)"
              name="firstName"
              autoComplete="given-name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              disabled={isLoading || !!successMessage}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              id="lastName"
              label="성 (선택)"
              name="lastName"
              autoComplete="family-name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              disabled={isLoading || !!successMessage}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              name="password"
              label="비밀번호"
              type="password"
              id="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={!!formErrors.password}
              helperText={formErrors.password || '비밀번호는 8자 이상이며, 대문자, 소문자, 숫자, 특수문자 중 3가지 이상을 포함해야 합니다'}
              disabled={isLoading || !!successMessage}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              name="confirmPassword"
              label="비밀번호 확인"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              error={!!formErrors.confirmPassword}
              helperText={formErrors.confirmPassword}
              disabled={isLoading || !!successMessage}
            />
          </Grid>
        </Grid>
        
        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
          disabled={isLoading || !!successMessage}
        >
          {isLoading ? <CircularProgress size={24} /> : '회원가입'}
        </Button>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Link href="/login" legacyBehavior passHref>
            <MuiLink variant="body2">
              이미 계정이 있으신가요? 로그인
            </MuiLink>
          </Link>
        </Box>
      </Box>
    </Paper>
  );
};

export default RegisterForm;