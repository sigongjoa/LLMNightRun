import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import { 
  Container,
  Typography,
  Box,
  Paper,
  Button,
  TextField,
  CircularProgress,
  Snackbar,
  Alert,
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Divider,
  Card,
  CardContent,
  CardActions,
  Chip
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import GitHubIcon from '@mui/icons-material/GitHub';
import DescriptionIcon from '@mui/icons-material/Description';
import CommitIcon from '@mui/icons-material/Commit';
import PreviewIcon from '@mui/icons-material/Preview';
import Head from 'next/head';
import RepositorySelector from '../components/github/RepositorySelector';

const GitHubUploadPage: NextPage = () => {
  // 상태
  const [questions, setQuestions] = useState<any[]>([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | ''>('');
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<number | null>(null);
  const [folderPath, setFolderPath] = useState<string>('');
  const [commitMessage, setCommitMessage] = useState<string>('');
  const [readmeContent, setReadmeContent] = useState<string>('');
  const [github, setGithub] = useState<{username?: string, repo?: string}>({});
  
  // 로딩 및 미리보기 상태
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('데이터를 불러오는 중...');
  const [loadingCommit, setLoadingCommit] = useState(false);
  const [loadingReadme, setLoadingReadme] = useState(false);
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [showReadmePreview, setShowReadmePreview] = useState(false);
  
  // 성공 및 오류 상태
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'warning'>('success');
  
  // 업로드 결과
  const [uploadResult, setUploadResult] = useState<{
    success?: boolean;
    message?: string;
    repo_url?: string;
    folder_path?: string;
    commit_message?: string;
    files?: string[];
  } | null>(null);
  
  // 초기 데이터 로드
  useEffect(() => {
    // 더미 데이터로 설정 (API 호출 대신)
    setQuestions([]);
    setGithub({
      username: 'sigongjoa',
      repo: 'LLMNightRUN_test1'
    });
    console.log('GitHub 업로드: 데이터 로딩 스킵됨 (API 호출 비활성화)');
  }, []);
  
  // LM Studio 연결 상태
  const [localLLMStatus, setLocalLLMStatus] = useState<{
    enabled: boolean;
    connected: boolean;
    model_id?: string;
  }>({
    enabled: false,
    connected: false
  });
  
  // 스낵바 표시 함수
  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };
  
  // 질문 선택 처리
  const handleQuestionSelect = (event: React.ChangeEvent<{ value: unknown }>) => {
    const value = event.target.value;
    setSelectedQuestionId(value ? Number(value) : '');
    // 선택이 바뀌면 결과 초기화
    setUploadResult(null);
    setShowReadmePreview(false);
  };

  // 커밋 메시지 생성 함수
  const handleGenerateCommitMessage = async () => {
    if (!selectedQuestionId) {
      showSnackbar('먼저 질문을 선택하세요.', 'error');
      return;
    }
    
    setLoadingCommit(true);
    try {
      // 더미 커밋 메시지 생성 (API 호출 대신)
      setTimeout(() => {
        setCommitMessage('feat: Add implementation for the requested feature');
        setLoadingCommit(false);
      }, 1000);
    } catch (error) {
      console.error('커밋 메시지 생성 오류:', error);
      showSnackbar('커밋 메시지를 생성하는 중 오류가 발생했습니다.', 'error');
      setLoadingCommit(false);
    }
  };
  
  // README 생성 함수
  const handleGenerateReadme = async () => {
    if (!selectedQuestionId) {
      showSnackbar('먼저 질문을 선택하세요.', 'error');
      return;
    }
    
    setLoadingReadme(true);
    try {
      // 더미 README 생성 (API 호출 대신)
      setTimeout(() => {
        setReadmeContent('# Project Title\n\nThis is an automatically generated README file.\n\n## Description\n\nThis project implements the requested functionality. The code is organized in a way to make it easy to understand and maintain.\n\n## Installation\n\n```bash\nnpm install\n```\n\n## Usage\n\n```javascript\nconst example = require(\'./example\');\nexample.run();\n```');
        setShowReadmePreview(true);
        setLoadingReadme(false);
      }, 1500);
    } catch (error) {
      console.error('README 생성 오류:', error);
      showSnackbar('README를 생성하는 중 오류가 발생했습니다.', 'error');
      setLoadingReadme(false);
    }
  };
  
  // GitHub 업로드 함수
  const handleUpload = async () => {
    if (!selectedQuestionId) {
      showSnackbar('먼저 질문을 선택하세요.', 'error');
      return;
    }
    
    setLoadingUpload(true);
    try {
      // 더미 업로드 결과 (API 호출 대신)
      setTimeout(() => {
        setUploadResult({
          success: true,
          repo_url: 'https://github.com/sigongjoa/LLMNightRUN_test1',
          folder_path: folderPath || `question_${selectedQuestionId}`,
          commit_message: commitMessage || 'feat: Add implementation for the requested feature'
        });
        
        showSnackbar('GitHub에 성공적으로 업로드되었습니다!', 'success');
        setLoadingUpload(false);
      }, 2000);
    } catch (error) {
      console.error('GitHub 업로드 오류:', error);
      showSnackbar('GitHub에 업로드하는 중 오류가 발생했습니다.', 'error');
      setLoadingUpload(false);
    }
  };

  return (
    <>
      <Head>
        <title>GitHub 업로드 - LLMNightRun</title>
        <meta name="description" content="코드를 GitHub 저장소에 업로드하고 AI로 문서를 생성합니다" />
      </Head>
      
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            GitHub 업로드
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            LLM이 생성한 코드를 GitHub 저장소에 업로드하고 자동으로 커밋 메시지와 README를 생성합니다
          </Typography>
        </Box>
        
        <Grid container spacing={3}>
          {/* 질문 선택 및 기본 설정 */}
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                업로드 설정
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel id="question-select-label">질문 선택</InputLabel>
                <Select
                  labelId="question-select-label"
                  value={selectedQuestionId}
                  onChange={handleQuestionSelect}
                  label="질문 선택"
                  disabled={loading}
                >
                  <MenuItem value="">
                    <em>질문을 선택하세요</em>
                  </MenuItem>
                  {Array.isArray(questions) && questions.map((question) => (
                    <MenuItem key={question.id} value={question.id}>
                      {question.id}: {question.content?.substring(0, 50)}
                      {question.content?.length > 50 ? '...' : ''}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label="저장소 폴더 경로 (선택 사항)"
                helperText="비워 두면 question_ID 형식으로 자동 생성됩니다"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                margin="normal"
                variant="outlined"
                disabled={loading}
                placeholder="예: projects/my-cool-project"
              />
              
              <Divider sx={{ my: 3 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                GitHub 저장소 선택
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <RepositorySelector 
                  value={selectedRepositoryId}
                  onChange={setSelectedRepositoryId}
                  disabled={loading || loadingUpload}
                />
                
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                  저장소를 선택하지 않으면 기본 저장소가 사용됩니다
                </Typography>
              </Box>
              
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
                기본 GitHub 정보
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">
                  전역 사용자: <strong>sigongjoa</strong>
                </Typography>
                <Typography variant="body2">
                  전역 저장소: <strong>LLMNightRUN_test1</strong>
                </Typography>
              </Box>
              
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
                LM Studio 상태
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" component="div">
                  활성화: <Chip 
                    size="small" 
                    color={localLLMStatus.enabled ? "success" : "default"}
                    label={localLLMStatus.enabled ? "활성화됨" : "비활성화됨"} 
                  />
                </Typography>
                <Typography variant="body2" component="div" sx={{ mt: 1 }}>
                  연결 상태: <Chip 
                    size="small" 
                    color={localLLMStatus.connected ? "success" : "error"}
                    label={localLLMStatus.connected ? "연결됨" : "연결 안 됨"} 
                  />
                </Typography>
                {localLLMStatus.model_id && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    모델: <strong>{localLLMStatus.model_id}</strong>
                  </Typography>
                )}
                {!localLLMStatus.connected && (
                  <Button 
                    variant="text" 
                    size="small" 
                    sx={{ mt: 1 }}
                    onClick={() => window.location.href = '/local-llm'}
                  >
                    로컬 LLM 설정으로 이동
                  </Button>
                )}
              </Box>
            </Paper>
          </Grid>
          
          {/* 문서 생성 및 업로드 */}
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                문서 생성
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <CommitIcon sx={{ mr: 1 }} />
                      <Typography variant="subtitle1">
                        커밋 메시지
                      </Typography>
                    </Box>
                    
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      value={commitMessage}
                      onChange={(e) => setCommitMessage(e.target.value)}
                      placeholder="자동 생성된 커밋 메시지가 여기에 표시됩니다"
                      disabled={loadingCommit}
                    />
                    
                    <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                      <Button
                        onClick={handleGenerateCommitMessage}
                        disabled={!selectedQuestionId || loadingCommit}
                        startIcon={loadingCommit ? <CircularProgress size={20} /> : null}
                      >
                        {loadingCommit ? '생성 중...' : '커밋 메시지 자동 생성'}
                      </Button>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sx={{ mt: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <DescriptionIcon sx={{ mr: 1 }} />
                      <Typography variant="subtitle1">
                        README 내용
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Button
                        startIcon={loadingReadme ? <CircularProgress size={20} /> : null}
                        onClick={handleGenerateReadme}
                        disabled={!selectedQuestionId || loadingReadme}
                      >
                        {loadingReadme ? 'README 생성 중...' : 'README 자동 생성'}
                      </Button>
                      
                      {readmeContent && (
                        <Button
                          startIcon={<PreviewIcon />}
                          onClick={() => setShowReadmePreview(!showReadmePreview)}
                        >
                          {showReadmePreview ? 'README 미리보기 숨기기' : 'README 미리보기 보기'}
                        </Button>
                      )}
                    </Box>
                    
                    {showReadmePreview && readmeContent && (
                      <Paper elevation={0} variant="outlined" sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
                        <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                          {readmeContent}
                        </Typography>
                      </Paper>
                    )}
                  </Grid>
                </Grid>
              </Box>
            </Paper>
            
            <Paper elevation={2} sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <GitHubIcon sx={{ mr: 1 }} />
                <Typography variant="h6">
                  GitHub 업로드
                </Typography>
              </Box>
              
              <Box sx={{ textAlign: 'center' }}>
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  startIcon={loadingUpload ? <CircularProgress size={24} color="inherit" /> : <CloudUploadIcon />}
                  onClick={handleUpload}
                  disabled={!selectedQuestionId || loadingUpload}
                  sx={{ px: 4, py: 1.5 }}
                >
                  {loadingUpload ? '업로드 중...' : 'GitHub에 업로드'}
                </Button>
              </Box>
              
              {/* 결과 표시 */}
              {uploadResult && (
                <Card elevation={0} variant="outlined" sx={{ mt: 4 }}>
                  <CardContent>
                    <Typography variant="h6" color="primary" gutterBottom>
                      업로드 성공!
                    </Typography>
                    
                    <Typography variant="body2" gutterBottom>
                      저장소: sigongjoa/LLMNightRUN_test1
                    </Typography>
                    
                    <Typography variant="body2" gutterBottom>
                      폴더: {uploadResult.folder_path}
                    </Typography>
                    
                    <Typography variant="body2" gutterBottom>
                      커밋 메시지: {uploadResult.commit_message}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      href={uploadResult.repo_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      GitHub에서 보기
                    </Button>
                  </CardActions>
                </Card>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Container>
      
      {/* 알림 스낵바 */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default GitHubUploadPage;