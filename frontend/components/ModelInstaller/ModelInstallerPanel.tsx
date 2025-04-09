import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Paper, 
  Grid, 
  List, 
  ListItem, 
  ListItemText, 
  CircularProgress,
  Divider,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Card,
  CardContent,
  CardActions,
  Alert
} from '@mui/material';
import { 
  GitHub as GitHubIcon, 
  PlayArrow as PlayIcon, 
  Refresh as RefreshIcon,
  CloudUpload as CloudUploadIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import axios from 'axios';

// API 경로 설정
const API_BASE_URL = '/api/model-installer';

// 모델 인터페이스
interface Model {
  name: string;
  path: string;
  metadata: any;
  created?: number;
}

// 설치 단계 인터페이스
interface InstallStep {
  name: string;
  status: string;
  error?: string;
}

// 설치 결과 인터페이스
interface InstallResult {
  status: string;
  model_name: string;
  model_dir?: string;
  error?: string;
  steps?: InstallStep[];
  elapsed_time?: number;
}

const ModelInstallerPanel: React.FC = () => {
  // 상태 관리
  const [repoUrl, setRepoUrl] = useState<string>('');
  const [modelName, setModelName] = useState<string>('');
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [installing, setInstalling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [installResult, setInstallResult] = useState<InstallResult | null>(null);
  const [openDetailDialog, setOpenDetailDialog] = useState<boolean>(false);
  const [openInstallDialog, setOpenInstallDialog] = useState<boolean>(false);

  // 모델 목록 로드
  const loadModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/models`);
      setModels(response.data);
    } catch (err) {
      setError('모델 목록을 불러오는 중 오류가 발생했습니다.');
      console.error('Error loading models:', err);
    } finally {
      setLoading(false);
    }
  };

  // 초기 로드
  useEffect(() => {
    loadModels();
  }, []);

  // 모델 설치
  const installModel = async () => {
    if (!repoUrl) {
      setError('GitHub 저장소 URL을 입력해주세요.');
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setInstalling(true);
    setInstallResult(null);
    setOpenInstallDialog(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/install`, {
        repo_url: repoUrl,
        model_name: modelName || undefined
      });

      setInstallResult(response.data);

      if (response.data.status === 'success') {
        setSuccessMessage(`모델 ${response.data.model_name}이(가) 성공적으로 설치되었습니다.`);
        loadModels(); // 목록 새로고침
        setRepoUrl(''); // 입력 필드 초기화
        setModelName('');
      } else {
        setError(response.data.error || '알 수 없는 오류가 발생했습니다.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '모델 설치 중 오류가 발생했습니다.');
      console.error('Error installing model:', err);
    } finally {
      setInstalling(false);
    }
  };

  // 모델 실행
  const runModel = async (model: Model) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post(`${API_BASE_URL}/run`, {
        model_name: model.name
      });

      if (response.data.status === 'success') {
        setSuccessMessage(`모델 ${model.name}이(가) 실행되었습니다. (프로세스 ID: ${response.data.process_id})`);
      } else {
        setError(response.data.error || '알 수 없는 오류가 발생했습니다.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '모델 실행 중 오류가 발생했습니다.');
      console.error('Error running model:', err);
    } finally {
      setLoading(false);
    }
  };

  // MCP 서버로 모델 푸시
  const pushToMcp = async (model: Model) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post(`${API_BASE_URL}/push-to-mcp`, {
        model_name: model.name
      });

      if (response.data.status === 'success') {
        setSuccessMessage(`모델 ${model.name}이(가) MCP 서버에 업로드되었습니다.`);
      } else {
        setError(response.data.error || '알 수 없는 오류가 발생했습니다.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'MCP 서버 업로드 중 오류가 발생했습니다.');
      console.error('Error pushing to MCP:', err);
    } finally {
      setLoading(false);
    }
  };

  // 모델 상세 정보 조회
  const viewModelDetails = (model: Model) => {
    setSelectedModel(model);
    setOpenDetailDialog(true);
  };

  // 날짜 포맷팅 함수
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        GitHub 모델 자동 설치 시스템
      </Typography>
      
      {/* 알림 메시지 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* 모델 설치 양식 */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          새 모델 설치
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="GitHub 저장소 URL"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/username/repository"
              variant="outlined"
              required
              disabled={installing}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="모델 이름 (선택 사항)"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="지정하지 않으면 저장소 이름으로 자동 설정됩니다."
              variant="outlined"
              disabled={installing}
            />
          </Grid>
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<GitHubIcon />}
              onClick={installModel}
              disabled={installing || !repoUrl}
            >
              {installing ? (
                <>
                  <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
                  설치 중...
                </>
              ) : (
                '모델 설치'
              )}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* 설치된 모델 목록 */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            설치된 모델 목록
          </Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadModels}
            disabled={loading}
          >
            새로고침
          </Button>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : models.length === 0 ? (
          <Typography variant="body2" color="textSecondary" sx={{ p: 2, textAlign: 'center' }}>
            설치된 모델이 없습니다.
          </Typography>
        ) : (
          <Grid container spacing={2}>
            {models.map((model) => (
              <Grid item xs={12} md={6} lg={4} key={model.name}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {model.name}
                    </Typography>
                    
                    {model.metadata?.repo_url && (
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        저장소: {model.metadata.repo_url}
                      </Typography>
                    )}
                    
                    {model.created && (
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        설치일: {formatDate(model.created)}
                      </Typography>
                    )}
                    
                    {model.metadata?.repo_analysis?.model_type?.primary && (
                      <Chip
                        label={model.metadata.repo_analysis.model_type.primary}
                        size="small"
                        color="primary"
                        sx={{ mr: 1, mt: 1 }}
                      />
                    )}
                  </CardContent>
                  
                  <CardActions>
                    <Tooltip title="모델 실행">
                      <IconButton color="primary" onClick={() => runModel(model)}>
                        <PlayIcon />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="MCP 서버에 업로드">
                      <IconButton color="secondary" onClick={() => pushToMcp(model)}>
                        <CloudUploadIcon />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="상세 정보">
                      <IconButton onClick={() => viewModelDetails(model)}>
                        <InfoIcon />
                      </IconButton>
                    </Tooltip>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* 모델 상세 정보 다이얼로그 */}
      <Dialog
        open={openDetailDialog}
        onClose={() => setOpenDetailDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedModel?.name} 상세 정보
        </DialogTitle>
        
        <DialogContent dividers>
          {selectedModel && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="subtitle1">기본 정보</Typography>
                <Typography variant="body2">
                  <strong>모델 경로:</strong> {selectedModel.path}
                </Typography>
                {selectedModel.metadata?.created_at && (
                  <Typography variant="body2">
                    <strong>설치일:</strong> {formatDate(selectedModel.metadata.created_at)}
                  </Typography>
                )}
                {selectedModel.metadata?.repo_url && (
                  <Typography variant="body2">
                    <strong>저장소:</strong> {selectedModel.metadata.repo_url}
                  </Typography>
                )}
              </Grid>
              
              {selectedModel.metadata?.repo_analysis?.model_type && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1">모델 유형</Typography>
                  <Typography variant="body2">
                    <strong>주요 유형:</strong> {selectedModel.metadata.repo_analysis.model_type.primary}
                  </Typography>
                  {selectedModel.metadata.repo_analysis.model_type.all_detected && (
                    <Typography variant="body2">
                      <strong>감지된 모든 유형:</strong> {Object.keys(selectedModel.metadata.repo_analysis.model_type.all_detected).join(', ')}
                    </Typography>
                  )}
                </Grid>
              )}
              
              {selectedModel.metadata?.install_info?.dependencies && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1">의존성 패키지</Typography>
                  <Box component="pre" sx={{ p: 1, bgcolor: 'background.paper', borderRadius: 1, overflow: 'auto' }}>
                    {selectedModel.metadata.install_info.dependencies.join(', ')}
                  </Box>
                </Grid>
              )}
              
              {selectedModel.metadata?.install_info?.launch_command && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1">실행 명령어</Typography>
                  <Box component="pre" sx={{ p: 1, bgcolor: 'background.paper', borderRadius: 1, overflow: 'auto' }}>
                    {selectedModel.metadata.install_info.launch_command}
                  </Box>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setOpenDetailDialog(false)}>닫기</Button>
          {selectedModel && (
            <Button 
              variant="contained" 
              color="primary" 
              onClick={() => {
                runModel(selectedModel);
                setOpenDetailDialog(false);
              }}
              startIcon={<PlayIcon />}
            >
              모델 실행
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* 설치 진행 상황 다이얼로그 */}
      <Dialog
        open={openInstallDialog}
        onClose={() => !installing && setOpenInstallDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          모델 설치 진행 상황
        </DialogTitle>
        
        <DialogContent dividers>
          {installing ? (
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <CircularProgress size={40} sx={{ mb: 2 }} />
              <Typography>
                GitHub 저장소를 분석하고 모델을 설치하는 중입니다...
              </Typography>
            </Box>
          ) : installResult ? (
            <Box>
              <Typography variant="h6" gutterBottom color={installResult.status === 'success' ? 'success.main' : 'error.main'}>
                {installResult.status === 'success' ? '설치 완료' : '설치 실패'}
              </Typography>
              
              {installResult.status === 'success' && (
                <Typography gutterBottom>
                  모델 '{installResult.model_name}'이(가) 성공적으로 설치되었습니다.
                  <br />
                  설치 경로: {installResult.model_dir}
                  <br />
                  소요 시간: {installResult.elapsed_time?.toFixed(2)}초
                </Typography>
              )}
              
              {installResult.error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {installResult.error}
                </Alert>
              )}
              
              {installResult.steps && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    설치 단계
                  </Typography>
                  
                  <List>
                    {installResult.steps.map((step, index) => (
                      <ListItem key={index}>
                        <ListItemText
                          primary={`${index + 1}. ${step.name}`}
                          secondary={
                            step.error ? `오류: ${step.error}` : ''
                          }
                          primaryTypographyProps={{
                            color: step.status === 'completed' ? 'success.main' : 
                                   step.status === 'failed' ? 'error.main' : 'inherit'
                          }}
                        />
                        <Chip 
                          label={step.status} 
                          color={
                            step.status === 'completed' ? 'success' : 
                            step.status === 'failed' ? 'error' : 'default'
                          }
                          size="small"
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Box>
          ) : (
            <Typography>
              설치가 시작되지 않았습니다.
            </Typography>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button 
            onClick={() => setOpenInstallDialog(false)} 
            disabled={installing}
          >
            닫기
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ModelInstallerPanel;
