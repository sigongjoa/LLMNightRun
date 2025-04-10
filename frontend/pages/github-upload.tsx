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
  Link,
  Chip
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import GitHubIcon from '@mui/icons-material/GitHub';
import DescriptionIcon from '@mui/icons-material/Description';
import CommitIcon from '@mui/icons-material/Commit';
import PreviewIcon from '@mui/icons-material/Preview';
import StorageIcon from '@mui/icons-material/Storage';
import Head from 'next/head';
import { 
  fetchQuestions,
  fetchCodeSnippets,
  fetchSettings,
  generateCommitMessage,
  generateReadme,
  uploadToGitHub
} from '../utils/api';
import { Question, CodeSnippet, GitHubRepository } from '../types';
import RepositorySelector from '../components/github/RepositorySelector';

const GitHubUploadPage: NextPage = () => {
  // 상태
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | ''>('');
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<number | null>(null);
  const [folderPath, setFolderPath] = useState<string>('');
  const [commitMessage, setCommitMessage] = useState<string>('');
  const [readmeContent, setReadmeContent] = useState<string>('');
  const [codeSnippets, setCodeSnippets] = useState<CodeSnippet[]>([]);
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
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  
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
    loadInitialData();
    
    // LM Studio 연결 상태 확인
    checkLocalLLMStatus();
  }, []);
  
  // LM Studio 연결 상태 확인
  const [localLLMStatus, setLocalLLMStatus] = useState<{
    enabled: boolean;
    connected: boolean;
    model_id?: string;
  }>({
    enabled: false,
    connected: false
  });
  
  const checkLocalLLMStatus = async () => {
    try {
      // 로컬 LLM 상태 API 호출
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/local-llm/status`);
      const status = await response.json();
      setLocalLLMStatus(status);
    } catch (error) {
      console.error('LM Studio 상태 확인 오류:', error);
      setLocalLLMStatus({
        enabled: false,
        connected: false
      });
    }
  };
  
  // 선택된 질문이 변경될 때 코드 스니펫 로드
  useEffect(() => {
    if (selectedQuestionId) {
      loadCodeSnippets(Number(selectedQuestionId));
    } else {
      setCodeSnippets([]);
      setCommitMessage('');
      setReadmeContent('');
    }
  }, [selectedQuestionId]);
  
  // 초기 데이터 로드 함수
  const loadInitialData = async () => {
    setLoading(true);
    setLoadingMessage('데이터를 불러오는 중...');
    try {
      try {
        // 질문 목록 로드
        try {
          const questionsData = await fetchQuestions();
          setQuestions(questionsData);
        } catch (questionsErr) {
          console.error('질문 목록 로드 오류:', questionsErr);
          // 개발 모드에서는 샘플 데이터 사용
          if (process.env.NODE_ENV === 'development') {
            setQuestions([
              { id: 1, content: '샘플 질문 1', tags: ['sample'] },
              { id: 2, content: '샘플 질문 2', tags: ['sample'] }
            ]);
          } else {
            setQuestions([]);
          }
        }
        
        // GitHub 설정 로드
        try {
          const settings = await fetchSettings();
          setGithub({
            username: settings.github_username,
            repo: settings.github_repo
          });
          
          if (!settings.github_token || !settings.github_username || !settings.github_repo) {
            showSnackbar('GitHub 연결이 구성되지 않았습니다. 먼저 설정에서 GitHub 정보를 구성하세요.', 'warning');
          }
        } catch (settingsErr) {
          console.error('설정 로드 오류:', settingsErr);
          // localStorage에서 GitHub 정보 가져오기
          const username = localStorage.getItem('github_username');
          const repo = localStorage.getItem('github_repo');
          
          setGithub({
            username: username || undefined,
            repo: repo || undefined
          });
          
          if (!username || !repo) {
            showSnackbar('GitHub 연결이 구성되지 않았습니다. 먼저 설정에서 GitHub 정보를 구성하세요.', 'warning');
          }
        }
      } catch (apiErr) {
        console.error('API 오류:', apiErr);
        showSnackbar('API 서버에 연결할 수 없습니다.', 'error');
      }
    } catch (error) {
      console.error('데이터 로드 오류:', error);
      showSnackbar('데이터를 불러오는 중 오류가 발생했습니다.', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 코드 스니펫 로드 함수
  const loadCodeSnippets = async (questionId: number) => {
    setLoadingMessage('코드 스니펫을 불러오는 중...');
    setLoading(true);
    try {
      try {
        const snippets = await fetchCodeSnippets();
        // 질문 ID로 필터링
        const filteredSnippets = snippets.filter(s => s.question_id === questionId);
        setCodeSnippets(filteredSnippets);
        
        if (filteredSnippets.length === 0) {
          showSnackbar('선택한 질문에 코드 스니펫이 없습니다.', 'error');
        }
      } catch (apiError) {
        console.error('코드 스니펫 API 오류:', apiError);
        
        if (process.env.NODE_ENV === 'development') {
          // 개발 모드에서는 샘플 데이터 사용
          setCodeSnippets([
            {
              id: 1,
              title: '샘플 코드 스니펫',
              content: '// 이것은 샘플 코드입니다.\nconsole.log("백엔드 API가 준비되지 않아 샘플 데이터가 표시됩니다.");',
              language: 'javascript',
              tags: ['sample'],
              question_id: questionId,
              version: 1
            }
          ]);
          
          showSnackbar('백엔드 API가 준비되지 않아 샘플 데이터를 사용합니다.', 'warning');
        } else {
          // 프로덕션 모드에서는 에러 표시
          setCodeSnippets([]);
          showSnackbar('코드 스니펫을 불러오는 중 오류가 발생했습니다.', 'error');
        }
      }
    } catch (error) {
      console.error('코드 스니펫 로드 오류:', error);
      setCodeSnippets([]);
      showSnackbar('코드 스니펫을 불러오는 중 오류가 발생했습니다.', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 커밋 메시지 생성 함수
  const handleGenerateCommitMessage = async () => {
    if (!selectedQuestionId) {
      showSnackbar('먼저 질문을 선택하세요.', 'error');
      return;
    }
    
    setLoadingCommit(true);
    try {
      const result = await generateCommitMessage(
        Number(selectedQuestionId),
        selectedRepositoryId || undefined
      );
      setCommitMessage(result.commit_message);
    } catch (error) {
      console.error('커밋 메시지 생성 오류:', error);
      showSnackbar('커밋 메시지를 생성하는 중 오류가 발생했습니다.', 'error');
    } finally {
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
      const result = await generateReadme(
        Number(selectedQuestionId),
        selectedRepositoryId || undefined
      );
      setReadmeContent(result.readme_content);
      setShowReadmePreview(true);
    } catch (error) {
      console.error('README 생성 오류:', error);
      showSnackbar('README를 생성하는 중 오류가 발생했습니다.', 'error');
    } finally {
      setLoadingReadme(false);
    }
  };
  
  // GitHub 업로드 함수
  const handleUpload = async () => {
    if (!selectedQuestionId) {
      showSnackbar('먼저 질문을 선택하세요.', 'error');
      return;
    }
    
    if (codeSnippets.length === 0) {
      showSnackbar('업로드할 코드 스니펫이 없습니다.', 'error');
      return;
    }
    
    setLoadingUpload(true);
    try {
      // 저장소를 지정하여 업로드
      const result = await uploadToGitHub(
        Number(selectedQuestionId),
        folderPath || undefined,
        selectedRepositoryId || undefined
      );
      
      setUploadResult({
        repo_url: result.repo_url,
        folder_path: result.folder_path,
        commit_message: result.commit_message
      });
      
      showSnackbar('GitHub에 성공적으로 업로드되었습니다!', 'success');
    } catch (error) {
      console.error('GitHub 업로드 오류:', error);
      showSnackbar('GitHub에 업로드하는 중 오류가 발생했습니다.', 'error');
    } finally {
      setLoadingUpload(false);
    }
  };
  
  // 스낵바 표시 함수
  const showSnackbar = (message: string, severity: 'success' | 'error') => {
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

  return (
    <>
      <Head>
        <title>GitHub 업로드 - LLMNightRun</title>
        <meta name="description" content="코드 스니펫을 GitHub 저장소에 업로드하고 AI로 문서를 생성합니다" />
      </Head>
      
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            GitHub 업로드
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            LLM이 생성한 코드 스니펫을 GitHub 저장소에 업로드하고 자동으로 커밋 메시지와 README를 생성합니다
          </Typography>
        </Box>
        
        {/* GitHub 설정 상태 */}
        {(!github.username || !github.repo) && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            GitHub 연결이 구성되지 않았습니다. 
            <Button 
              variant="text" 
              color="inherit" 
              onClick={() => window.location.href = '/settings'}
              sx={{ ml: 1 }}
            >
              설정으로 이동
            </Button>
          </Alert>
        )}
        
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
                  value={selectedQuestionId === '' ? '' : Number(selectedQuestionId)}
                  onChange={handleQuestionSelect}
                  label="질문 선택"
                  disabled={loading}
                >
                  <MenuItem value="">
                    <em>질문을 선택하세요</em>
                  </MenuItem>
                  {questions.map((question) => (
                    <MenuItem key={question.id} value={question.id}>
                      {question.id}: {question.content.substring(0, 50)}
                      {question.content.length > 50 ? '...' : ''}
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
                  전역 사용자: <strong>{github.username || '설정되지 않음'}</strong>
                </Typography>
                <Typography variant="body2">
                  전역 저장소: <strong>{github.repo || '설정되지 않음'}</strong>
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
              
              <Divider sx={{ my: 3 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                포함될 코드 스니펫 ({codeSnippets.length})
              </Typography>
              
              {loading ? (
                <Box sx={{ display: 'flex', my: 2 }}>
                  <CircularProgress size={24} sx={{ mr: 1 }} />
                  <Typography>{loadingMessage}</Typography>
                </Box>
              ) : codeSnippets.length > 0 ? (
                <Box sx={{ mt: 2 }}>
                  {codeSnippets.map((snippet) => (
                    <Box key={snippet.id} sx={{ mb: 1 }}>
                      <Typography variant="body2">
                        {snippet.title} ({snippet.language})
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  선택한 질문에 코드 스니펫이 없습니다
                </Typography>
              )}
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
                      <Paper variant="outlined" sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
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
                  disabled={!selectedQuestionId || loadingUpload || codeSnippets.length === 0}
                  sx={{ px: 4, py: 1.5 }}
                >
                  {loadingUpload ? '업로드 중...' : 'GitHub에 업로드'}
                </Button>
              </Box>
              
              {/* 결과 표시 */}
              {uploadResult && (
                <Card variant="outlined" sx={{ mt: 4 }}>
                  <CardContent>
                    <Typography variant="h6" color="primary" gutterBottom>
                      업로드 성공!
                    </Typography>
                    
                    <Typography variant="body2" gutterBottom>
                      저장소: {github.username}/{github.repo}
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