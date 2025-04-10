import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Grid, 
  TextField, 
  Button, 
  Alert, 
  CircularProgress,
  Tabs,
  Tab,
  Divider,
  IconButton,
  InputAdornment,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Card,
  CardContent,
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Save as SaveIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Star as StarIcon
} from '@mui/icons-material';
import { Settings, GitHubRepository } from '../types';
import { fetchSettings, updateSettings } from '../utils/api';
import axios from 'axios';

// API 기본 URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// 저장소 목록 컴포넌트
const GitHubRepositoriesList: React.FC = () => {
  const [repositories, setRepositories] = useState<GitHubRepository[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRepo, setEditingRepo] = useState<GitHubRepository | null>(null);
  const [showTokens, setShowTokens] = useState<{[key: number]: boolean}>({});
  
  // 새 저장소 정보
  const [newRepo, setNewRepo] = useState({
    name: '',
    owner: '',
    token: '',
    description: '',
    is_default: false,
    is_private: true,
    branch: 'main'
  });
  
  // 저장소 목록 로드
  const loadRepositories = async () => {
    setLoading(true);
    setError(null);
    
    try {
      try {
        const response = await axios.get(`${API_BASE_URL}/github/repositories`);
        setRepositories(response.data.repositories || []);
      } catch (err) {
        console.error('저장소 목록 로드 오류:', err);
        // 백엔드에 엔드포인트가 없는 경우 빈 배열로 초기화
        setRepositories([]);
        
        // 개발 환경에서만 에러 메시지 표시
        if (process.env.NODE_ENV === 'development') {
          setError('백엔드 API가 준비되지 않았습니다: /github/repositories');
        } else {
          setError(null);
        }
      }
    } catch (innerErr) {
      console.error('예상치 못한 오류:', innerErr);
      setError('저장소 목록을 불러오는 중 예상치 못한 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  // 컴포넌트 마운트 시 저장소 목록 로드
  useEffect(() => {
    loadRepositories();
  }, []);
  
  // 토큰 표시 토글
  const toggleShowToken = (repoId: number) => {
    setShowTokens(prev => ({
      ...prev,
      [repoId]: !prev[repoId]
    }));
  };
  
  // 저장소 추가 다이얼로그 열기
  const handleOpenAddDialog = () => {
    setEditingRepo(null);
    setNewRepo({
      name: '',
      owner: '',
      token: '',
      description: '',
      is_default: false,
      is_private: true,
      branch: 'main'
    });
    setDialogOpen(true);
  };
  
  // 저장소 편집 다이얼로그 열기
  const handleOpenEditDialog = (repo: GitHubRepository) => {
    setEditingRepo(repo);
    setNewRepo({
      name: repo.name,
      owner: repo.owner,
      token: '',  // 보안상 비워둠
      description: repo.description || '',
      is_default: repo.is_default,
      is_private: repo.is_private,
      branch: repo.branch || 'main'
    });
    setDialogOpen(true);
  };
  
  // 입력 변경 핸들러
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = e.target;
    setNewRepo({
      ...newRepo,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  // 저장소 추가 또는 업데이트
  const handleSaveRepository = async () => {
    try {
      if (!newRepo.name || !newRepo.owner || (!editingRepo && !newRepo.token)) {
        alert('이름, 소유자, 토큰은 필수 입력 필드입니다.');
        return;
      }
      
      try {
        if (editingRepo) {
          // 기존 저장소 업데이트
          const updateData = { ...newRepo };
          if (!updateData.token) {
            delete updateData.token; // 토큰이 비어있으면 업데이트하지 않음
          }
          
          await axios.put(`${API_BASE_URL}/github/repositories/${editingRepo.id}`, updateData);
        } else {
          // 새 저장소 추가
          await axios.post(`${API_BASE_URL}/github/repositories`, newRepo);
        }
        
        // API 호출이 성공하면 저장소 목록 새로고침
        await loadRepositories();
        setDialogOpen(false);
        
        // 로컬 저장소 정보를 임시로 업데이트 (APIs가 준비되지 않은 경우)
        if (repositories.length === 0) {
          const newRepoItem = {
            id: Date.now(), // 임시 ID
            name: newRepo.name,
            owner: newRepo.owner,
            description: newRepo.description,
            is_default: newRepo.is_default,
            is_private: newRepo.is_private,
            branch: newRepo.branch
          };
          
          setRepositories([newRepoItem]);
        }
      } catch (apiErr) {
        console.error('저장소 API 오류:', apiErr);
        
        if (process.env.NODE_ENV === 'development') {
          alert('백엔드 API가 준비되지 않았습니다. 개발 모드에서는 변경 사항이 저장되지 않습니다.');
        } else {
          alert('저장소를 저장하는 중 오류가 발생했습니다.');
        }
      }
    } catch (err) {
      console.error('저장소 저장 오류:', err);
      alert('저장소를 저장하는 중 오류가 발생했습니다.');
    }
  };
  
  // 저장소 삭제
  const handleDeleteRepository = async (repoId: number) => {
    if (!confirm('정말로 이 저장소를 삭제하시겠습니까?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE_URL}/github/repositories/${repoId}`);
      await loadRepositories();
    } catch (err) {
      console.error('저장소 삭제 오류:', err);
      alert('저장소를 삭제하는 중 오류가 발생했습니다.');
    }
  };
  
  // 기본 저장소로 설정
  const handleSetDefault = async (repoId: number) => {
    try {
      await axios.put(`${API_BASE_URL}/github/repositories/${repoId}`, {
        is_default: true
      });
      await loadRepositories();
    } catch (err) {
      console.error('기본 저장소 설정 오류:', err);
      alert('기본 저장소를 설정하는 중 오류가 발생했습니다.');
    }
  };
  
  return (
    <>
      {loading ? (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
          <CircularProgress size={24} sx={{ mr: 1 }} />
          <Typography>저장소 목록을 불러오는 중...</Typography>
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : repositories.length === 0 ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          연결된 GitHub 저장소가 없습니다. 저장소를 추가해 주세요.
        </Alert>
      ) : (
        <List>
          {repositories.map((repo) => (
            <Card key={repo.id} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6" sx={{ flexGrow: 1 }}>
                    {repo.owner}/{repo.name}
                  </Typography>
                  {repo.is_default && (
                    <Chip 
                      size="small" 
                      color="primary" 
                      icon={<StarIcon />} 
                      label="기본" 
                      sx={{ ml: 1 }}
                    />
                  )}
                </Box>
                
                {repo.description && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {repo.description}
                  </Typography>
                )}
                
                <Grid container spacing={1} sx={{ mt: 1 }}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" component="div">
                      <strong>브랜치:</strong> {repo.branch || 'main'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" component="div">
                      <strong>가시성:</strong> {repo.is_private ? '비공개' : '공개'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" component="div" sx={{ display: 'flex', alignItems: 'center' }}>
                      <strong>토큰:</strong> 
                      <span style={{ marginLeft: '8px', flexGrow: 1 }}>
                        {showTokens[repo.id] ? '••••••••' : '•••••••••••••••••••'}
                      </span>
                      <IconButton 
                        size="small" 
                        onClick={() => toggleShowToken(repo.id)}
                      >
                        {showTokens[repo.id] ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                      </IconButton>
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
              <CardActions>
                <Button 
                  size="small" 
                  startIcon={<EditIcon />} 
                  onClick={() => handleOpenEditDialog(repo)}
                >
                  편집
                </Button>
                {!repo.is_default && (
                  <Button 
                    size="small" 
                    startIcon={<StarIcon />} 
                    onClick={() => handleSetDefault(repo.id)}
                  >
                    기본으로 설정
                  </Button>
                )}
                <Button 
                  size="small" 
                  color="error" 
                  startIcon={<DeleteIcon />} 
                  onClick={() => handleDeleteRepository(repo.id)}
                >
                  삭제
                </Button>
              </CardActions>
            </Card>
          ))}
        </List>
      )}
      
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Button 
          variant="contained" 
          color="primary" 
          startIcon={<AddIcon />} 
          onClick={handleOpenAddDialog}
        >
          GitHub 저장소 추가
        </Button>
      </Box>
      
      {/* 저장소 추가/편집 다이얼로그 */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingRepo ? '저장소 편집' : '새 GitHub 저장소 추가'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="소유자"
                name="owner"
                value={newRepo.owner}
                onChange={handleInputChange}
                placeholder="사용자명 또는 조직명"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="저장소 이름"
                name="name"
                value={newRepo.name}
                onChange={handleInputChange}
                placeholder="repository-name"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                required={!editingRepo}
                label="GitHub 토큰"
                name="token"
                type="password"
                value={newRepo.token}
                onChange={handleInputChange}
                placeholder={editingRepo ? '변경하지 않으려면 비워두세요' : 'ghp_...'}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="설명 (선택사항)"
                name="description"
                value={newRepo.description}
                onChange={handleInputChange}
                placeholder="저장소에 대한 간단한 설명"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="기본 브랜치"
                name="branch"
                value={newRepo.branch}
                onChange={handleInputChange}
                placeholder="main"
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    name="is_private"
                    checked={newRepo.is_private}
                    onChange={handleInputChange}
                  />
                }
                label="비공개 저장소"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    name="is_default"
                    checked={newRepo.is_default}
                    onChange={handleInputChange}
                  />
                }
                label="기본 저장소로 설정"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            취소
          </Button>
          <Button 
            onClick={handleSaveRepository} 
            variant="contained" 
            color="primary"
          >
            {editingRepo ? '저장소 업데이트' : '저장소 추가'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

const SettingsPage: React.FC = () => {
  // 상태 관리
  const [settings, setSettings] = useState<Settings>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<number>(0);
  
  // 비밀번호 표시 상태
  const [showOpenAIKey, setShowOpenAIKey] = useState<boolean>(false);
  const [showClaudeKey, setShowClaudeKey] = useState<boolean>(false);
  const [showGitHubToken, setShowGitHubToken] = useState<boolean>(false);
  
  // 웹 크롤링 설정
  const [enableWebCrawling, setEnableWebCrawling] = useState<boolean>(false);
  const [openaiUsername, setOpenaiUsername] = useState<string>('');
  const [openaiPassword, setOpenaiPassword] = useState<string>('');
  const [claudeUsername, setClaudeUsername] = useState<string>('');
  const [claudePassword, setClaudePassword] = useState<string>('');
  
  // 데이터 로드
  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        setError(null);
        
        try {
          const settingsData = await fetchSettings();
          setSettings(settingsData);
        } catch (apiErr: any) {
          console.error('설정 로딩 오류:', apiErr);
          // API가 준비되지 않은 경우 빈 설정 객체로 초기화
          setSettings({});
          
          if (process.env.NODE_ENV === 'development') {
            setError('백엔드 API가 준비되지 않았습니다: /settings');
          }
        }
        
        // 환경 변수에서 웹 크롤링 설정 로드 (실제로는 API를 통해 가져와야 함)
        setEnableWebCrawling(localStorage.getItem('enable_web_crawling') === 'true');
        setOpenaiUsername(localStorage.getItem('openai_username') || '');
        setOpenaiPassword(localStorage.getItem('openai_password') || '');
        setClaudeUsername(localStorage.getItem('claude_username') || '');
        setClaudePassword(localStorage.getItem('claude_password') || '');
      } catch (err: any) {
        console.error('설정 로딩 오류:', err);
        setError(err.detail || '설정을 불러오는 중에 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    loadSettings();
  }, []);
  
  // 탭 변경 핸들러
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  // 설정 저장 핸들러
  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);
      
      try {
        // API 설정 저장
        await updateSettings(settings);
      } catch (apiErr: any) {
        console.error('API 설정 저장 오류:', apiErr);
        
        if (process.env.NODE_ENV === 'development') {
          // 개발 환경에서는 경고만 표시하고 계속 진행
          console.warn('백엔드 API가 준비되지 않았습니다. 로컬 스토리지에만 저장합니다.');
        } else {
          throw apiErr; // 프로덕션 환경에서는 에러 발생
        }
      }
      
      // 웹 크롤링 설정 저장 (로컬 스토리지에 임시 저장)
      localStorage.setItem('enable_web_crawling', enableWebCrawling.toString());
      localStorage.setItem('openai_username', openaiUsername);
      localStorage.setItem('openai_password', openaiPassword);
      localStorage.setItem('claude_username', claudeUsername);
      localStorage.setItem('claude_password', claudePassword);
      
      // GitHub 설정도 로컬 스토리지에 백업 (API 실패 대비)
      if (settings.github_token) {
        localStorage.setItem('github_token', settings.github_token);
      }
      if (settings.github_username) {
        localStorage.setItem('github_username', settings.github_username);
      }
      if (settings.github_repo) {
        localStorage.setItem('github_repo', settings.github_repo);
      }
      
      setSuccess(true);
      
      // 3초 후 성공 메시지 숨기기
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (err: any) {
      console.error('설정 저장 오류:', err);
      setError(err.detail || '설정을 저장하는 중에 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  };
  
  // 테스트 연결 핸들러
  const handleTestConnection = (service: string) => {
    // 실제로는 API를 통해 연결 테스트
    alert(`${service} 연결 테스트를 수행합니다.`);
  };
  
  // 로딩 화면
  if (loading) {
    return (
      <Container maxWidth="md">
        <Box sx={{ my: 4, textAlign: 'center' }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>설정을 불러오는 중...</Typography>
        </Box>
      </Container>
    );
  }
  
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          설정
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert 
            severity="success" 
            sx={{ mb: 3 }}
            icon={<CheckCircleIcon fontSize="inherit" />}
          >
            설정이 성공적으로 저장되었습니다.
          </Alert>
        )}
        
        <Paper elevation={3}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange}
              variant="fullWidth"
            >
              <Tab label="API 키" />
              <Tab label="GitHub 설정" />
              <Tab label="웹 크롤링" />
            </Tabs>
          </Box>
          
          {/* API 키 설정 */}
          <TabPanel value={activeTab} index={0}>
            <Typography variant="h6" gutterBottom>
              LLM API 키 설정
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              OpenAI와 Anthropic API 키를 설정하여 API를 통해 LLM에 액세스합니다.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  label="OpenAI API 키"
                  fullWidth
                  value={settings.openai_api_key || ''}
                  onChange={(e) => setSettings({...settings, openai_api_key: e.target.value})}
                  type={showOpenAIKey ? 'text' : 'password'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowOpenAIKey(!showOpenAIKey)}
                          edge="end"
                        >
                          {showOpenAIKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  label="Claude API 키"
                  fullWidth
                  value={settings.claude_api_key || ''}
                  onChange={(e) => setSettings({...settings, claude_api_key: e.target.value})}
                  type={showClaudeKey ? 'text' : 'password'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowClaudeKey(!showClaudeKey)}
                          edge="end"
                        >
                          {showClaudeKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="outlined" 
                  onClick={() => handleTestConnection('OpenAI')}
                  fullWidth
                >
                  OpenAI 연결 테스트
                </Button>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="outlined" 
                  onClick={() => handleTestConnection('Claude')}
                  fullWidth
                >
                  Claude 연결 테스트
                </Button>
              </Grid>
            </Grid>
          </TabPanel>
          
          {/* GitHub 설정 */}
          <TabPanel value={activeTab} index={1}>
            <Typography variant="h6" gutterBottom>
              GitHub 연동 설정
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              응답과 코드를 GitHub 저장소에 저장하기 위한 설정을 구성합니다.
              여러 개의 저장소를 추가하고 관리할 수 있습니다.
            </Typography>
            
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 3, fontWeight: 'bold' }}>
                연결된 GitHub 저장소
              </Typography>
              
              <GitHubRepositoriesList />
            </Box>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
              기본 GitHub 설정
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              전역 기본 설정으로 사용됩니다. 특정 저장소가 선택되지 않은 경우 이 설정이 적용됩니다.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  label="GitHub 토큰"
                  fullWidth
                  value={settings.github_token || ''}
                  onChange={(e) => setSettings({...settings, github_token: e.target.value})}
                  type={showGitHubToken ? 'text' : 'password'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowGitHubToken(!showGitHubToken)}
                          edge="end"
                        >
                          {showGitHubToken ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  label="GitHub 사용자명"
                  fullWidth
                  value={settings.github_username || ''}
                  onChange={(e) => setSettings({...settings, github_username: e.target.value})}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  label="저장소 이름"
                  fullWidth
                  value={settings.github_repo || ''}
                  onChange={(e) => setSettings({...settings, github_repo: e.target.value})}
                />
              </Grid>
              
              <Grid item xs={12}>
                <Button 
                  variant="outlined" 
                  onClick={() => handleTestConnection('GitHub')}
                  fullWidth
                >
                  GitHub 연결 테스트
                </Button>
              </Grid>
            </Grid>
          </TabPanel>
          
          {/* 웹 크롤링 설정 */}
          <TabPanel value={activeTab} index={2}>
            <Typography variant="h6" gutterBottom>
              웹 크롤링 설정
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              ChatGPT와 Claude 웹 인터페이스를 자동화하기 위한 설정을 구성합니다.
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={enableWebCrawling}
                  onChange={(e) => setEnableWebCrawling(e.target.checked)}
                />
              }
              label="웹 크롤링 활성화"
              sx={{ mb: 2 }}
            />
            
            {enableWebCrawling && (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }}>
                    <Typography variant="subtitle2">OpenAI 웹 계정</Typography>
                  </Divider>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="OpenAI 사용자명"
                    fullWidth
                    value={openaiUsername}
                    onChange={(e) => setOpenaiUsername(e.target.value)}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="OpenAI 비밀번호"
                    fullWidth
                    type="password"
                    value={openaiPassword}
                    onChange={(e) => setOpenaiPassword(e.target.value)}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }}>
                    <Typography variant="subtitle2">Claude 웹 계정</Typography>
                  </Divider>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Claude 사용자명"
                    fullWidth
                    value={claudeUsername}
                    onChange={(e) => setClaudeUsername(e.target.value)}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Claude 비밀번호"
                    fullWidth
                    type="password"
                    value={claudePassword}
                    onChange={(e) => setClaudePassword(e.target.value)}
                  />
                </Grid>
              </Grid>
            )}
          </TabPanel>
          
          <Box sx={{ p: 3, textAlign: 'right' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
              onClick={handleSaveSettings}
              disabled={saving}
            >
              {saving ? '저장 중...' : '설정 저장'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default SettingsPage;