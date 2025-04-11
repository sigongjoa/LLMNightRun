import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  Checkbox,
  ListItemText,
  FormHelperText,
  Divider,
  Card,
  CardContent,
  IconButton,
  Alert,
  Snackbar,
  CircularProgress
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import Layout from '../../components/Layout';
import { useRouter } from 'next/router';
import { useApi } from '../../src/hooks/useApi';

// DO NOT CHANGE CODE: 이 코드는 AB 테스트 생성 페이지의 기본 구조입니다.
// TEMP: 임시 구현 코드입니다. 현재는 기본 데이터로 작동하지만 추후 백엔드 API 완성 시 리팩토링 예정입니다.
const CreateABTestPage = () => {
  const router = useRouter();
  const api = useApi();
  const [isLoading, setIsLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  
  // 폼 상태 관리
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    models: [],
    prompts: [],
    metrics: [],
    templateId: '',
  });
  
  // 선택 옵션 목록
  const [availableModels, setAvailableModels] = useState([]);
  const [availablePrompts, setAvailablePrompts] = useState([]);
  const [availableMetrics, setAvailableMetrics] = useState([]);
  const [availableTemplates, setAvailableTemplates] = useState([]);
  
  // 유효성 검사 상태
  const [errors, setErrors] = useState({
    name: false,
    models: false,
    prompts: false,
    metrics: false,
  });

  // 데이터 로드
  useEffect(() => {
    loadSelectionOptions();
  }, []);

  // 선택 옵션 데이터 로드
  const loadSelectionOptions = async () => {
    setIsLoading(true);
    try {
      // 기본 데이터 설정 (API 실패 시 사용)
      const defaultModels = [
        { id: 'model-1', name: '모델 1', description: '기본 모델 1 설명' },
        { id: 'model-2', name: '모델 2', description: '기본 모델 2 설명' },
        { id: 'model-3', name: '모델 3', description: '기본 모델 3 설명' },
      ];
      
      const defaultPrompts = [
        { id: 'prompt-1', name: '프롬프트 1', description: '기본 프롬프트 1 설명' },
        { id: 'prompt-2', name: '프롬프트 2', description: '기본 프롬프트 2 설명' },
      ];
      
      const defaultMetrics = [
        { id: 'metric-1', name: '정확도', description: '응답의 정확도를 평가합니다.' },
        { id: 'metric-2', name: '관련성', description: '응답의 질문 관련성을 평가합니다.' },
      ];
      
      try {
        // 모델 목록 가져오기
        const modelsResponse = await api.get('/ab-testing/models');
        if (modelsResponse.status === 200) {
          setAvailableModels(modelsResponse.data);
        } else {
          setAvailableModels(defaultModels);
        }
      } catch (error) {
        console.log('모델 데이터 로딩 실패, 기본값 사용:', error);
        setAvailableModels(defaultModels);
      }

      try {
        // 프롬프트 목록 가져오기
        const promptsResponse = await api.get('/ab-testing/prompts');
        if (promptsResponse.status === 200) {
          setAvailablePrompts(promptsResponse.data);
        } else {
          setAvailablePrompts(defaultPrompts);
        }
      } catch (error) {
        console.log('프롬프트 데이터 로딩 실패, 기본값 사용:', error);
        setAvailablePrompts(defaultPrompts);
      }

      try {
        // 평가 지표 목록 가져오기
        const metricsResponse = await api.get('/ab-testing/metrics');
        if (metricsResponse.status === 200) {
          setAvailableMetrics(metricsResponse.data);
        } else {
          setAvailableMetrics(defaultMetrics);
        }
      } catch (error) {
        console.log('평가 지표 데이터 로딩 실패, 기본값 사용:', error);
        setAvailableMetrics(defaultMetrics);
      }

      try {
        // 템플릿 목록 가져오기
        const templatesResponse = await api.get('/ab-testing/templates');
        if (templatesResponse.status === 200) {
          setAvailableTemplates(templatesResponse.data);
        }
      } catch (error) {
        console.log('템플릿 데이터 로딩 실패:', error);
        // 템플릿은 기본값 없이 빈 배열 유지
      }
    } catch (error) {
      console.error('데이터 로딩 오류:', error);
      setSnackbar({
        open: true,
        message: '데이터를 불러오는 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 입력 필드 변경 핸들러
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
    
    // 에러 상태 업데이트
    if (name === 'name' && errors.name) {
      setErrors({
        ...errors,
        name: value.trim() === '',
      });
    }
  };

  // 멀티 셀렉트 변경 핸들러
  const handleMultiSelectChange = (e) => {
    const { name, value } = e.target;
    // 값이 배열이 아니면 빈 배열로 기본값 설정
    const safeValue = Array.isArray(value) ? value : [];
    
    setFormData({
      ...formData,
      [name]: safeValue,
    });
    
    // 에러 상태 업데이트
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: safeValue.length === 0,
      });
    }
  };

  // 폼 제출 핸들러
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 유효성 검사
    const newErrors = {
      name: formData.name.trim() === '',
      models: formData.models.length === 0,
      prompts: formData.prompts.length === 0,
      metrics: formData.metrics.length === 0,
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
    
    setIsLoading(true);
    
    try {
      // 실험 세트 생성 API 호출
      const response = await api.post('/ab-testing/experiment-sets', formData);
      
      if (response.status === 201) {
        setSnackbar({
          open: true,
          message: '실험 세트가 성공적으로 생성되었습니다.',
          severity: 'success'
        });
        
        // 잠시 후 목록 페이지로 이동
        setTimeout(() => {
          router.push('/ab-testing');
        }, 1500);
      }
    } catch (error) {
      console.error('실험 세트 생성 오류:', error);
      setSnackbar({
        open: true,
        message: '실험 세트 생성 중 오류가 발생했습니다.',
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
              새 A/B 테스트 실험 세트 생성
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
                    label="실험 세트 이름"
                    fullWidth
                    required
                    value={formData.name}
                    onChange={handleInputChange}
                    error={errors.name}
                    helperText={errors.name ? '실험 세트 이름을 입력해주세요.' : ''}
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
                  />
                </Grid>

                {/* 템플릿 선택 */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    템플릿 (선택사항)
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>템플릿 선택</InputLabel>
                    <Select
                      name="templateId"
                      value={formData.templateId}
                      onChange={handleInputChange}
                      label="템플릿 선택"
                    >
                      <MenuItem value="">선택 안함</MenuItem>
                      {availableTemplates.map((template) => (
                        <MenuItem key={template.id} value={template.id}>
                          {template.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      템플릿을 선택하면 사전 구성된 설정을 불러옵니다.
                    </FormHelperText>
                  </FormControl>
                </Grid>

                {/* 모델 선택 */}
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    비교할 모델
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <FormControl fullWidth required error={errors.models}>
                    <InputLabel>모델 선택</InputLabel>
                    <Select
                      name="models"
                      multiple
                      value={formData.models}
                      onChange={handleMultiSelectChange}
                      input={<OutlinedInput label="모델 선택" />}
                      renderValue={(selected) => {
                        // 선택된 값이 배열이 아니면 빈 배열로 처리
                        const selectedArray = Array.isArray(selected) ? selected : [];
                        return (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {selectedArray.map((value) => (
                              <Chip key={value} label={availableModels.find(model => model.id === value)?.name || value} />
                            ))}
                          </Box>
                        );
                      }}
                    >
                      {availableModels.map((model) => (
                        <MenuItem key={model.id} value={model.id}>
                          <Checkbox checked={formData.models.indexOf(model.id) > -1} />
                          <ListItemText primary={model.name} secondary={model.description} />
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.models && (
                      <FormHelperText>최소 하나의 모델을 선택해주세요.</FormHelperText>
                    )}
                  </FormControl>
                </Grid>

                {/* 프롬프트 선택 */}
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    비교할 프롬프트
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <FormControl fullWidth required error={errors.prompts}>
                    <InputLabel>프롬프트 선택</InputLabel>
                    <Select
                      name="prompts"
                      multiple
                      value={formData.prompts}
                      onChange={handleMultiSelectChange}
                      input={<OutlinedInput label="프롬프트 선택" />}
                      renderValue={(selected) => {
                        // 선택된 값이 배열이 아니면 빈 배열로 처리
                        const selectedArray = Array.isArray(selected) ? selected : [];
                        return (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {selectedArray.map((value) => (
                              <Chip key={value} label={availablePrompts.find(prompt => prompt.id === value)?.name || value} />
                            ))}
                          </Box>
                        );
                      }}
                    >
                      {availablePrompts.map((prompt) => (
                        <MenuItem key={prompt.id} value={prompt.id}>
                          <Checkbox checked={formData.prompts.indexOf(prompt.id) > -1} />
                          <ListItemText primary={prompt.name} />
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.prompts && (
                      <FormHelperText>최소 하나의 프롬프트를 선택해주세요.</FormHelperText>
                    )}
                  </FormControl>
                </Grid>

                {/* 평가 지표 */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    평가 지표
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <FormControl fullWidth required error={errors.metrics}>
                    <InputLabel>평가 지표 선택</InputLabel>
                    <Select
                      name="metrics"
                      multiple
                      value={formData.metrics}
                      onChange={handleMultiSelectChange}
                      input={<OutlinedInput label="평가 지표 선택" />}
                      renderValue={(selected) => {
                        // 선택된 값이 배열이 아니면 빈 배열로 처리
                        const selectedArray = Array.isArray(selected) ? selected : [];
                        return (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {selectedArray.map((value) => (
                              <Chip key={value} label={availableMetrics.find(metric => metric.id === value)?.name || value} />
                            ))}
                          </Box>
                        );
                      }}
                    >
                      {availableMetrics.map((metric) => (
                        <MenuItem key={metric.id} value={metric.id}>
                          <Checkbox checked={formData.metrics.indexOf(metric.id) > -1} />
                          <ListItemText 
                            primary={metric.name} 
                            secondary={metric.description}
                          />
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.metrics && (
                      <FormHelperText>최소 하나의 평가 지표를 선택해주세요.</FormHelperText>
                    )}
                  </FormControl>
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
                    {isLoading ? <CircularProgress size={24} /> : '실험 세트 생성'}
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

export default CreateABTestPage;
