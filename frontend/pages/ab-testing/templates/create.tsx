import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Button,
  TextField,
  FormControl,
  FormHelperText,
  Divider,
  IconButton,
  Alert,
  Snackbar,
  CircularProgress
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import Layout from '../../../components/Layout';
import { useRouter } from 'next/router';
import { useApi } from '../../../src/hooks/useApi';

// DO NOT CHANGE CODE: 이 코드는 AB 테스트 템플릿 생성 페이지의 기본 구조입니다.
// TEMP: 임시 구현 코드입니다. 백엔드 API 연동 후 추가 검증 및 리팩토링 예정입니다.
const CreateTemplateABTestPage = () => {
  const router = useRouter();
  const api = useApi();
  const [isLoading, setIsLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  
  // 폼 상태 관리
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    defaultConfig: `{
  "models": ["model-id-1", "model-id-2"],
  "prompts": ["prompt-id-1", "prompt-id-2"],
  "metrics": ["metric-id-1", "metric-id-2"],
  "additionalSettings": {
    "maxTokens": 1000,
    "temperature": 0.7
  }
}`,
  });
  
  // 유효성 검사 상태
  const [errors, setErrors] = useState({
    name: false,
    defaultConfig: false,
  });

  // 입력 필드 변경 핸들러
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
    
    // 에러 상태 업데이트
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: value.trim() === '',
      });
    }
  };

  // 폼 제출 핸들러
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 유효성 검사
    const newErrors = {
      name: formData.name.trim() === '',
      defaultConfig: formData.defaultConfig.trim() === '',
    };
    
    setErrors(newErrors);
    
    // 에러가 있으면 제출 중단
    if (Object.values(newErrors).some(error => error)) {
      setSnackbar({
        open: true,
        message: '필수 입력 항목을 모두 채워주세요.',
        severity: 'error'
      });
      return;
    }
    
    // JSON 형식 검증
    try {
      JSON.parse(formData.defaultConfig);
    } catch (error) {
      setSnackbar({
        open: true,
        message: '기본 구성이 유효한 JSON 형식이 아닙니다.',
        severity: 'error'
      });
      setErrors({
        ...errors,
        defaultConfig: true,
      });
      return;
    }
    
    setIsLoading(true);
    
    try {
      // 템플릿 생성 API 호출
      const response = await api.post('/ab-testing/templates', formData);
      
      if (response.status === 201) {
        setSnackbar({
          open: true,
          message: '템플릿이 성공적으로 생성되었습니다.',
          severity: 'success'
        });
        
        // 잠시 후 목록 페이지로 이동
        setTimeout(() => {
          router.push('/ab-testing');
        }, 1500);
      }
    } catch (error) {
      console.error('템플릿 생성 오류:', error);
      setSnackbar({
        open: true,
        message: '템플릿 생성 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 뒤로가기 핸들러
  const handleGoBack = () => {
    router.push('/ab-testing');
  };

  // 스낵바 닫기 핸들러
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // 로딩 중일 때 표시
  if (isLoading) {
    return (
      <Layout>
        <Container>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <CircularProgress />
          </Box>
        </Container>
      </Layout>
    );
  }

  return (
    <Layout>
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <IconButton onClick={handleGoBack} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" component="h1">
              새 A/B 테스트 템플릿 생성
            </Typography>
          </Box>

          <Paper sx={{ p: 3 }}>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                {/* 기본 정보 */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    기본 정보
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <TextField
                    name="name"
                    label="템플릿 이름"
                    fullWidth
                    required
                    value={formData.name}
                    onChange={handleInputChange}
                    error={errors.name}
                    helperText={errors.name ? '템플릿 이름을 입력해주세요.' : ''}
                    sx={{ mb: 2 }}
                  />
                  
                  <TextField
                    name="description"
                    label="설명"
                    fullWidth
                    multiline
                    rows={3}
                    value={formData.description}
                    onChange={handleInputChange}
                    sx={{ mb: 2 }}
                  />
                </Grid>

                {/* 기본 구성 */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    기본 구성 (JSON)
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <TextField
                    name="defaultConfig"
                    label="기본 구성 JSON"
                    fullWidth
                    required
                    multiline
                    rows={10}
                    value={formData.defaultConfig}
                    onChange={handleInputChange}
                    error={errors.defaultConfig}
                    helperText={errors.defaultConfig ? '유효한 JSON 형식으로 입력해주세요.' : '모델, 프롬프트, 평가 지표 등의 기본 구성을 JSON 형식으로 입력하세요.'}
                    placeholder={`{
  "models": ["model-id-1", "model-id-2"],
  "prompts": ["prompt-id-1", "prompt-id-2"],
  "metrics": ["metric-id-1", "metric-id-2"],
  "additionalSettings": {
    "maxTokens": 1000,
    "temperature": 0.7
  }
}`}
                  />
                </Grid>

                <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                  <Button variant="outlined" onClick={handleGoBack}>
                    취소
                  </Button>
                  <Button 
                    type="submit" 
                    variant="contained" 
                    color="primary"
                    disabled={isLoading}
                  >
                    {isLoading ? <CircularProgress size={24} /> : '템플릿 생성'}
                  </Button>
                </Grid>
              </Grid>
            </form>
          </Paper>
        </Box>

        {/* 스낵바 알림 */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Layout>
  );
};
// END-DO-NOT-CHANGE

export default CreateTemplateABTestPage;
