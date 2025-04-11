import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Button,
  TextField,
  Card,
  CardContent,
  CardActions,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
  Alert,
  Snackbar,
  Chip
} from '@mui/material';
import CodeIcon from '@mui/icons-material/Code';
import SettingsIcon from '@mui/icons-material/Settings';
import GitHubIcon from '@mui/icons-material/GitHub';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import IntegrationInstructionsIcon from '@mui/icons-material/IntegrationInstructions';
import Layout from '../components/Layout';
import { useApi } from '../src/hooks/useApi';

// GitHub AI 환경 설정 페이지
const GitHubAISetupPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [repoAnalysis, setRepoAnalysis] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [setupComplete, setSetupComplete] = useState(false);
  const [installationLog, setInstallationLog] = useState([]);
  const api = useApi();

  // 단계 정의
  const steps = ['저장소 입력', '저장소 분석', '환경 설정', '설치 및 완료'];

  // 저장소 URL 입력 핸들러
  const handleRepoUrlChange = (event) => {
    setRepoUrl(event.target.value);
  };

  // 저장소 분석 실행
  const analyzeRepository = async () => {
    console.log("분석 버튼 클릭됨, repoUrl:", repoUrl);
    
    if (!repoUrl) {
      setSnackbar({
        open: true,
        message: 'GitHub 저장소 URL을 입력해주세요.',
        severity: 'warning'
      });
      return;
    }

    setIsLoading(true);
    try {
      console.log("API 요청 시작: /model-installer/analyze", { url: repoUrl });
      const response = await api.post('/model-installer/analyze', { url: repoUrl });
      console.log("API 응답:", response);
      
      if (response) {
        setRepoAnalysis(response);
        setActiveStep(1); // 다음 단계로 이동
        setSnackbar({
          open: true,
          message: '저장소 분석이 완료되었습니다.',
          severity: 'success'
        });
      }
    } catch (error) {
      console.error('저장소 분석 오류:', error);
      setSnackbar({
        open: true,
        message: '저장소 분석 중 오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'),
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 폼 제출 핸들러 (Enter 키 지원)
  const handleSubmit = (e) => {
    e.preventDefault();
    analyzeRepository();
  };

  // 다음 단계로 이동
  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  // 이전 단계로 이동
  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  // 환경 설정 적용
  const applyEnvironmentSetup = async () => {
    setIsLoading(true);
    try {
      const response = await api.post('/model-installer/setup', { 
        url: repoUrl,
        analysis: repoAnalysis 
      });
      
      if (response) {
        handleNext(); // 다음 단계로 이동
        setSnackbar({
          open: true,
          message: '환경 설정이 완료되었습니다.',
          severity: 'success'
        });
      }
    } catch (error) {
      console.error('환경 설정 오류:', error);
      setSnackbar({
        open: true,
        message: '환경 설정 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 모델 설치 실행
  const installModel = async () => {
    setIsLoading(true);
    setInstallationLog([]);
    try {
      // 비동기 설치 요청
      const response = await api.post('/model-installer/install', { 
        url: repoUrl
      });
      
      if (response) {
        // 설치 ID 받기
        const installationId = response.installation_id || "inst-12345";
        
        // 로그 폴링 시작
        pollInstallationStatus(installationId);
      }
    } catch (error) {
      console.error('모델 설치 오류:', error);
      setSnackbar({
        open: true,
        message: '모델 설치 중 오류가 발생했습니다.',
        severity: 'error'
      });
      setIsLoading(false);
    }
  };
  
  // 설치 상태 폴링
  const pollInstallationStatus = async (installationId) => {
    try {
      const checkStatus = async () => {
        const statusResponse = await api.get(`/model-installer/status/${installationId}`);
        
        // 로그 업데이트
        if (statusResponse.logs) {
          setInstallationLog(statusResponse.logs);
        }
        
        if (statusResponse.status === 'completed') {
          setIsLoading(false);
          setSetupComplete(true);
          setSnackbar({
            open: true,
            message: '모델 설치가 완료되었습니다.',
            severity: 'success'
          });
          return;
        } else if (statusResponse.status === 'failed') {
          setIsLoading(false);
          setSnackbar({
            open: true,
            message: '모델 설치에 실패했습니다.',
            severity: 'error'
          });
          return;
        }
        
        // 계속 폴링
        setTimeout(checkStatus, 3000);
      };
      
      // 첫 번째 폴링 시작
      checkStatus();
    } catch (error) {
      console.error('설치 상태 확인 오류:', error);
      setIsLoading(false);
      setSnackbar({
        open: true,
        message: '설치 상태 확인 중 오류가 발생했습니다.',
        severity: 'error'
      });
    }
  };

  // 스낵바 닫기
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // 분석 결과 표시 컴포넌트
  const AnalysisResult = ({ analysis }) => {
    if (!analysis) return null;
    
    return (
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            분석 결과
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1">
              식별된 모델 유형:
            </Typography>
            {analysis.model_type && (
              <Chip 
                label={analysis.model_type.primary} 
                color="primary" 
                icon={<CodeIcon />} 
                sx={{ mt: 1 }}
              />
            )}
          </Box>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            발견된 실행 스크립트:
          </Typography>
          <List dense>
            {analysis.launch_scripts && analysis.launch_scripts.map((script, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <IntegrationInstructionsIcon />
                </ListItemIcon>
                <ListItemText primary={script} />
              </ListItem>
            ))}
            {(!analysis.launch_scripts || analysis.launch_scripts.length === 0) && (
              <ListItem>
                <ListItemText primary="실행 스크립트를 찾을 수 없습니다." />
              </ListItem>
            )}
          </List>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            요구사항 파일:
          </Typography>
          <List dense>
            {analysis.requirements && Object.keys(analysis.requirements).map((reqFile, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText primary={reqFile} />
              </ListItem>
            ))}
            {(!analysis.requirements || Object.keys(analysis.requirements).length === 0) && (
              <ListItem>
                <ListItemText primary="요구사항 파일을 찾을 수 없습니다." />
              </ListItem>
            )}
          </List>
        </CardContent>
      </Card>
    );
  };

  // 스텝별 컨텐츠 렌더링
  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box component="form" onSubmit={handleSubmit} noValidate>
            <Typography variant="body1" paragraph>
              분석하고 설정할 GitHub 저장소 URL을 입력하세요.
            </Typography>
            <TextField
              label="GitHub 저장소 URL"
              variant="outlined"
              fullWidth
              value={repoUrl}
              onChange={handleRepoUrlChange}
              placeholder="https://github.com/username/repository"
              sx={{ mb: 3 }}
            />
            <Button
              variant="contained"
              onClick={analyzeRepository}
              disabled={isLoading}
              startIcon={<GitHubIcon />}
              type="submit"
            >
              저장소 분석
              {isLoading && <CircularProgress size={24} sx={{ ml: 1 }} />}
            </Button>
          </Box>
        );
      case 1:
        return (
          <Box>
            <Typography variant="body1" paragraph>
              저장소 분석이 완료되었습니다. 분석 결과를 확인하세요.
            </Typography>
            
            <AnalysisResult analysis={repoAnalysis} />
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button onClick={handleBack}>
                이전
              </Button>
              <Button
                variant="contained"
                onClick={handleNext}
              >
                다음
              </Button>
            </Box>
          </Box>
        );
      case 2:
        return (
          <Box>
            <Typography variant="body1" paragraph>
              분석된 결과를 바탕으로 AI 환경을 자동으로 설정합니다.
            </Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              필요한 패키지와 종속성이 자동으로 설치됩니다. 환경 설정 파일이 생성됩니다.
            </Alert>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button onClick={handleBack}>
                이전
              </Button>
              <Button
                variant="contained"
                onClick={applyEnvironmentSetup}
                disabled={isLoading}
                startIcon={<SettingsIcon />}
              >
                환경 설정 적용
                {isLoading && <CircularProgress size={24} sx={{ ml: 1 }} />}
              </Button>
            </Box>
          </Box>
        );
      case 3:
        return (
          <Box>
            <Typography variant="body1" paragraph>
              환경 설정이 완료되었습니다. 모델을 설치합니다.
            </Typography>
            
            {!setupComplete ? (
              <>
                <Alert severity="info" sx={{ mb: 3 }}>
                  모델 설치는 시간이 소요될 수 있습니다. 설치가 완료될 때까지 기다려주세요.
                </Alert>
                
                {installationLog.length > 0 && (
                  <Paper 
                    variant="outlined" 
                    sx={{ 
                      p: 2, 
                      mb: 3, 
                      maxHeight: '200px', 
                      overflow: 'auto',
                      bgcolor: 'black',
                      color: 'white',
                      fontFamily: 'monospace'
                    }}
                  >
                    {installationLog.map((log, index) => (
                      <Box key={index} component="div" sx={{ pb: 0.5 }}>
                        {log}
                      </Box>
                    ))}
                  </Paper>
                )}
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Button onClick={handleBack} disabled={isLoading}>
                    이전
                  </Button>
                  <Button
                    variant="contained"
                    onClick={installModel}
                    disabled={isLoading}
                    startIcon={isLoading ? <CircularProgress size={24} /> : <AnalyticsIcon />}
                  >
                    {isLoading ? '설치 중...' : '모델 설치'}
                  </Button>
                </Box>
              </>
            ) : (
              <>
                <Alert severity="success" sx={{ mb: 3 }}>
                  모델 설치가 완료되었습니다. 이제 모델을 사용할 수 있습니다.
                </Alert>
                
                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                  <Button
                    variant="contained"
                    color="success"
                    href="/models"
                  >
                    모델 관리로 이동
                  </Button>
                </Box>
              </>
            )}
          </Box>
        );
      default:
        return '알 수 없는 단계';
    }
  };

  return (
    <Layout>
      <Container maxWidth="md">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" gutterBottom component="h1">
            GitHub AI 환경 자동 설정
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            GitHub 저장소를 분석하여 모델 유형을 식별하고 필요한 환경을 자동으로 설정합니다.
          </Typography>

          <Paper sx={{ p: 3, mb: 4 }}>
            <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
            
            {getStepContent(activeStep)}
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

export default GitHubAISetupPage;
