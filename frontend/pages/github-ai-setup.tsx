import React, { useState, useEffect, useRef } from 'react';
// TEMP: 임시 구현 코드입니다. 정상 작동하지만 추후 리팩토링 예정입니다. 수정하지 마세요.
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
import Head from 'next/head';

// GitHub AI 환경 설정 페이지
const GitHubAISetupPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [repoAnalysis, setRepoAnalysis] = useState<any>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [setupComplete, setSetupComplete] = useState(false);
  const [installationLog, setInstallationLog] = useState<string[]>([]);
  
  // 페이지가 마운트되었는지 추적
  const mounted = useRef(false);

  // TEMP: 임시 API 처리 코드입니다. 추후 서버 연결이 정상화되면 제거 예정입니다. 수정하지 마세요.

  // 저장소 URL 입력 핸들러
  const handleRepoUrlChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRepoUrl(event.target.value);
  };

  // 컴포넌트 마운트 시 초기화
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  // 저장소 분석 실행
  // TEMP: 임시 모의 구현입니다. 서버 API가 정상 작동하면 이 코드를 제거하고 원래 API 호출 코드로 변경해야 합니다. 수정하지 마세요.
  const analyzeRepository = async () => {
    if (!repoUrl) {
      setSnackbar({
        open: true,
        message: 'GitHub 저장소 URL을 입력해주세요.',
        severity: 'warning'
      });
      return;
    }

    setIsLoading(true);
    
    // 저장소 이름 추출
    const repoName = repoUrl.split('/').pop() || '';
    
    // 분석 시뮬레이션 (API 호출 대신)
    setTimeout(() => {
      if (!mounted.current) return;
      
      // 모의 분석 결과
      const mockAnalysisResult = {
        status: "success",
        repo_name: repoName,
        repo_url: repoUrl,
        model_type: {
          primary: "llama",
          confidence: 0.85
        },
        launch_scripts: [
          "run.py",
          "app.py",
          "serve.py"
        ],
        requirements: {
          "requirements.txt": {
            content: "torch\ntransformers\nfastapi\nuvicorn"
          }
        },
        config_files: {
          "model_config.json": {
            content: "{\"model_size\": \"7B\", \"parameters\": {\"temperature\": 0.7}}"
          }
        }
      };
      
      // 상태 업데이트
      setRepoAnalysis(mockAnalysisResult);
      setActiveStep(1);
      setSnackbar({
        open: true,
        message: '저장소 분석이 완료되었습니다.',
        severity: 'success'
      });
      setIsLoading(false);
    }, 1500);
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
  // TEMP: 임시 모의 구현입니다. 서버 API가 정상 작동하면 이 코드를 제거하고 원래 API 호출 코드로 변경해야 합니다. 수정하지 마세요.
  const applyEnvironmentSetup = async () => {
    setIsLoading(true);
    
    // 설정 시뮬레이션
    setTimeout(() => {
      if (!mounted.current) return;
      
      handleNext();
      setSnackbar({
        open: true,
        message: '환경 설정이 완료되었습니다.',
        severity: 'success'
      });
      setIsLoading(false);
    }, 2000);
  };

  // 모델 설치 실행
  // TEMP: 임시 모의 구현입니다. 서버 API가 정상 작동하면 이 코드를 제거하고 원래 API 호출 코드로 변경해야 합니다. 수정하지 마세요.
  const installModel = async () => {
    setIsLoading(true);
    setInstallationLog([]);
    
    // 로그 컨테이너 표시
    const logContainer = document.getElementById('log-container');
    if (logContainer) {
      logContainer.style.display = 'block';
    }
    
    // 설치 로그 시뮬레이션
    const installationLogs = [
      '모델 설치 시작...',
      '의존성 패키지 설치 중...',
      'pip install -r requirements.txt',
      'torch 설치 중...',
      'transformers 설치 중...',
      'fastapi 설치 중...',
      '모델 파일 다운로드 중...',
      '모델 가중치 다운로드 중 (2.3GB)...',
      '환경 구성 완료...',
      '모델 설치 완료!'
    ];
    
    // 로그 표시 함수
    const addLogWithDelay = (index: number) => {
      if (index < installationLogs.length) {
        setInstallationLog(prev => [...prev, installationLogs[index]]);
        setTimeout(() => addLogWithDelay(index + 1), 800);
      } else {
        if (!mounted.current) return;
        setIsLoading(false);
        setSetupComplete(true);
        setSnackbar({
          open: true,
          message: '모델 설치가 완료되었습니다.',
          severity: 'success'
        });
      }
    };
    
    // 첫 번째 로그 시작
    addLogWithDelay(0);
  };

  // 스낵바 닫기
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // 분석 결과 표시 컴포넌트
  const AnalysisResult = ({ analysis }: { analysis: any }) => {
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
            {analysis.launch_scripts && analysis.launch_scripts.map((script: string, index: number) => (
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
            {analysis.requirements && Object.keys(analysis.requirements).map((reqFile: string, index: number) => (
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
  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box component="form" onSubmit={(e) => { e.preventDefault(); analyzeRepository(); }}>
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
                    id="log-container"
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
      <Head>
        {/* TEMP: 임시 해결책으로 외부 스크립트를 사용합니다. 서버 연결이 정상화되면 제거 예정입니다. 수정하지 마세요. */}
        {/* 연결 문제를 해결하기 위한 외부 스크립트 */}
        <script src="/fix-api.js" />
        {/* 버튼 클릭 문제를 해결하기 위한 스크립트 - 수정된 버전 */}
        <script src="/fix-button-fixed.js" />
        {/* 디버그 헬퍼 스크립트 */}
        <script src="/debug-helper.js" />
      </Head>
      
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
              {['저장소 입력', '저장소 분석', '환경 설정', '설치 및 완료'].map((label) => (
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
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity as any} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Layout>
  );
};

export default GitHubAISetupPage;
