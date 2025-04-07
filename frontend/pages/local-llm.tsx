import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Switch, 
  FormControlLabel, 
  TextField, 
  Button, 
  Paper,
  Card,
  CardContent,
  CardActions,
  Grid,
  Divider,
  Chip,
  Alert,
  CircularProgress,
  Slider,
  Tooltip
} from '@mui/material';
import { 
  getLocalLLMStatus, 
  updateLocalLLMConfig, 
  askLocalLLM 
} from '../utils/local-llm-api';
import { LocalLLMStatus, LocalLLMConfigUpdate } from '../types/local-llm';

/**
 * 로컬 LLM 설정 및 테스트 페이지
 */
const LocalLLMPage: React.FC = () => {
  // 상태
  const [status, setStatus] = useState<LocalLLMStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [testing, setTesting] = useState<boolean>(false);
  const [baseUrl, setBaseUrl] = useState<string>('http://127.0.0.1:1234');
  const [modelId, setModelId] = useState<string>('');
  const [enabled, setEnabled] = useState<boolean>(false);
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(1000);
  const [testQuestion, setTestQuestion] = useState<string>('');
  const [testResponse, setTestResponse] = useState<string>('');
  const [error, setError] = useState<string>('');

  // 초기 데이터 로드
  useEffect(() => {
    loadStatus();
  }, []);

  // 상태 로드
  const loadStatus = async () => {
    setLoading(true);
    setError('');
    
    try {
      console.log('로컬 LLM 상태 요청 중...');
      const data = await getLocalLLMStatus();
      console.log('로컬 LLM 상태 응답 받음:', data);
      setStatus(data);
      setEnabled(data.enabled);
      setBaseUrl(data.base_url);
      if (data.model_id) {
        setModelId(data.model_id);
      }
    } catch (err: any) {
      console.error('LLM 상태 가져오기 오류:', err);
      setError(typeof err.detail === 'string' ? err.detail : '로컬 LLM 상태를 가져오는 데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 설정 저장
  const saveConfig = async () => {
    setSaving(true);
    setError('');
    
    try {
      const config: LocalLLMConfigUpdate = {
        enabled,
        base_url: baseUrl,
        model_id: modelId,
        temperature,
        max_tokens: maxTokens
      };
      
      await updateLocalLLMConfig(config);
      await loadStatus(); // 상태 다시 로드
    } catch (err: any) {
      console.error('설정 저장 오류:', err);
      setError(typeof err.detail === 'string' ? err.detail : '설정을 저장하는 데 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  // 테스트 질문 전송
  const sendTestQuestion = async () => {
    if (!testQuestion.trim()) {
      setError('질문을 입력해주세요.');
      return;
    }
    
    setTesting(true);
    setError('');
    setTestResponse('');
    
    try {
      console.log('로컬 LLM에 질문 전송 중...', testQuestion);
      const response = await askLocalLLM(testQuestion);
      console.log('로컬 LLM 응답 받음:', response);
      setTestResponse(response.content);
    } catch (err: any) {
      console.error('로컬 LLM 질문 오류:', err);
      setError(typeof err.detail === 'string' ? err.detail : '로컬 LLM에 질문하는 데 실패했습니다.');
    } finally {
      setTesting(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box my={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          로컬 LLM 설정
        </Typography>
        
        {loading ? (
          <Box display="flex" justifyContent="center" my={4}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {error && (
              <Alert severity="error" sx={{ my: 2 }}>
                {error}
              </Alert>
            )}
            
            <Grid container spacing={3}>
              {/* 설정 카드 */}
              <Grid item xs={12} md={6}>
                <Paper elevation={2} sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    로컬 LLM 구성
                  </Typography>
                  
                  <Box my={2}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={enabled}
                          onChange={(e) => setEnabled(e.target.checked)}
                          color="primary"
                        />
                      }
                      label="로컬 LLM 활성화"
                    />
                  </Box>
                  
                  <TextField
                    fullWidth
                    label="LLM API URL"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    margin="normal"
                    variant="outlined"
                    helperText="LM Studio API 주소 (기본값: http://127.0.0.1:1234)"
                  />
                  
                  <TextField
                    fullWidth
                    label="모델 ID"
                    value={modelId}
                    onChange={(e) => setModelId(e.target.value)}
                    margin="normal"
                    variant="outlined"
                    helperText="현재 사용 중인 모델 ID (예: deepseek-r1-distill-qwen-7b)"
                  />
                  
                  <Box mt={3}>
                    <Typography gutterBottom>Temperature: {temperature}</Typography>
                    <Slider
                      value={temperature}
                      onChange={(_, value) => setTemperature(value as number)}
                      step={0.1}
                      marks
                      min={0}
                      max={1}
                      valueLabelDisplay="auto"
                    />
                  </Box>
                  
                  <Box mt={3}>
                    <Typography gutterBottom>Max Tokens: {maxTokens}</Typography>
                    <Slider
                      value={maxTokens}
                      onChange={(_, value) => setMaxTokens(value as number)}
                      step={100}
                      marks
                      min={100}
                      max={2000}
                      valueLabelDisplay="auto"
                    />
                  </Box>
                  
                  <Box mt={3} display="flex" justifyContent="space-between">
                    <Button 
                      variant="outlined" 
                      onClick={loadStatus}
                      disabled={loading}
                    >
                      새로고침
                    </Button>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={saveConfig}
                      disabled={saving}
                    >
                      {saving ? <CircularProgress size={24} /> : '저장'}
                    </Button>
                  </Box>
                </Paper>
                
                {/* 상태 정보 */}
                {status && (
                  <Card sx={{ mt: 3 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        상태 정보
                      </Typography>
                      
                      <Box display="flex" alignItems="center" mb={1}>
                        <Typography variant="body1" sx={{ mr: 1 }}>
                          활성화:
                        </Typography>
                        <Chip 
                          label={status.enabled ? '활성화됨' : '비활성화됨'} 
                          color={status.enabled ? 'success' : 'default'} 
                          size="small" 
                        />
                      </Box>
                      
                      <Box display="flex" alignItems="center" mb={1}>
                        <Typography variant="body1" sx={{ mr: 1 }}>
                          연결 상태:
                        </Typography>
                        <Chip 
                          label={status.connected ? '연결됨' : '연결 안 됨'} 
                          color={status.connected ? 'success' : 'error'} 
                          size="small" 
                        />
                      </Box>
                      
                      {status.error && (
                        <Alert severity="error" sx={{ mt: 2 }}>
                          {typeof status.error === 'string' ? status.error : '연결 오류가 발생했습니다.'}
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                )}
              </Grid>
              
              {/* 테스트 카드 */}
              <Grid item xs={12} md={6}>
                <Paper elevation={2} sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    로컬 LLM 테스트
                  </Typography>
                  
                  <TextField
                    fullWidth
                    label="테스트 질문"
                    value={testQuestion}
                    onChange={(e) => setTestQuestion(e.target.value)}
                    margin="normal"
                    variant="outlined"
                    multiline
                    rows={4}
                    placeholder="여기에 질문을 입력하세요..."
                  />
                  
                  <Box mt={2} display="flex" justifyContent="flex-end">
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={sendTestQuestion}
                      disabled={testing || !enabled || (status && !status.connected)}
                    >
                      {testing ? <CircularProgress size={24} /> : '질문하기'}
                    </Button>
                  </Box>
                  
                  {testResponse && (
                    <Box mt={3}>
                      <Typography variant="subtitle1" gutterBottom>
                        응답:
                      </Typography>
                      <Paper
                        variant="outlined"
                        sx={{
                          p: 2,
                          bgcolor: 'grey.50',
                          maxHeight: '300px',
                          overflow: 'auto'
                        }}
                      >
                        <Typography variant="body1" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                          {testResponse}
                        </Typography>
                      </Paper>
                    </Box>
                  )}
                </Paper>
              </Grid>
            </Grid>
          </>
        )}
      </Box>
    </Container>
  );
};

export default LocalLLMPage;