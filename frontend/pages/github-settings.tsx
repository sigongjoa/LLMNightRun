import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import { 
  Container, 
  Typography, 
  Box, 
  TextField, 
  Button, 
  Grid, 
  CircularProgress,
  Divider,
  Card,
  CardContent,
  CardHeader,
  Snackbar,
  Alert,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  FormControlLabel,
  Switch
} from '@mui/material';
import Head from 'next/head';
import GitHubIcon from '@mui/icons-material/GitHub';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import LockIcon from '@mui/icons-material/Lock';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import SettingsIcon from '@mui/icons-material/Settings';

import api from '../utils/api';
import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

// GitHub 저장소 타입 정의
interface Repository {
  id: number;
  name: string;
  description?: string;
  owner: string;
  url: string;
  is_default: boolean;
  is_private: boolean;
  token: string;
  branch?: string;
  project_id?: number;
  created_at?: string;
  updated_at?: string;
}

const GitHubSettingsPage: NextPage = () => {
  // 상태 정의
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [confirmAction, setConfirmAction] = useState<() => void>(() => {});
  const [confirmTitle, setConfirmTitle] = useState('');
  const [confirmMessage, setConfirmMessage] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [showTokens, setShowTokens] = useState<{[key: number]: boolean}>({});
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    owner: '',
    token: '',
    is_default: false,
    is_private: true,
    branch: 'main'
  });

  // 저장소 목록 가져오기
  const fetchRepositories = async () => {
    setLoadingRepos(true);
    setError(null);
    
    try {
      // 실제 API 호출로 데이터 가져오기
      const response = await api.get('/github-repos/');
      setRepositories(response.data);
    } catch (err: any) {
      console.error('저장소 목록 로드 오류:', err);
      
      // 오류 메시지 구성
      let errorMessage = 'GitHub 저장소 목록을 불러오는 중 오류가 발생했습니다.';
      
      if (err.response) {
        // 서버에서 응답이 왔지만 에러인 경우
        errorMessage += ` (${err.response.status})`;
        if (err.response.data && err.response.data.detail) {
          errorMessage += `: ${err.response.data.detail}`;
        }
      } else if (err.request) {
        // 요청은 보냈지만 응답이 없는 경우
        errorMessage = '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.';
      } else {
        // 요청 설정 중 오류 발생
        errorMessage += `: ${err.message || '알 수 없는 오류'}`;
      }
      
      setError(errorMessage);
      
      // 오류 발생 시 빈 배열 사용
      setRepositories([]);
    } finally {
      setLoadingRepos(false);
    }
  };

  // 초기 데이터 로드
  useEffect(() => {
    fetchRepositories();
  }, []);

  // 폼 입력 처리
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // 저장소 추가/수정 처리
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // 실제 API 호출
      if (editMode && selectedRepo) {
        // 저장소 수정
        await api.put(`/github-repos/${selectedRepo.id}`, formData);
        setSuccess('저장소 정보가 성공적으로 업데이트되었습니다.');
      } else {
        // 새 저장소 추가
        await api.post('/github-repos/', formData);
        setSuccess('새 GitHub 저장소가 성공적으로 추가되었습니다.');
      }
      
      // 폼 초기화 및 저장소 목록 새로고침
      resetForm();
      fetchRepositories();
    } catch (err: any) {
      console.error('저장소 저장 오류:', err);
      
      // 오류 메시지 구성
      let errorMessage = 'GitHub 저장소 정보를 저장하는 중 오류가 발생했습니다.';
      
      if (err.response) {
        // 서버에서 응답이 왔지만 에러인 경우
        errorMessage += ` (${err.response.status})`;
        if (err.response.data && err.response.data.detail) {
          errorMessage += `: ${err.response.data.detail}`;
        }
      } else if (err.request) {
        // 요청은 보냈지만 응답이 없는 경우
        errorMessage = '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.';
      } else {
        // 요청 설정 중 오류 발생
        errorMessage += `: ${err.message || '알 수 없는 오류'}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 폼 초기화
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      owner: '',
      token: '',
      is_default: false,
      is_private: true,
      branch: 'main'
    });
    setEditMode(false);
    setSelectedRepo(null);
  };

  // 저장소 편집 모드 시작
  const handleEditRepository = (repo: Repository) => {
    setEditMode(true);
    setSelectedRepo(repo);
    setFormData({
      name: repo.name,
      description: repo.description || '',
      owner: repo.owner,
      token: '', // 토큰은 보안상의 이유로 다시 입력해야 함
      is_default: repo.is_default,
      is_private: repo.is_private,
      branch: repo.branch || 'main'
    });
  };

  // 저장소 삭제 확인
  const confirmDeleteRepository = (repo: Repository) => {
    setConfirmTitle('저장소 삭제');
    setConfirmMessage(`저장소 "${repo.name}"을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`);
    setConfirmAction(() => () => handleDeleteRepository(repo.id));
    setOpenDialog(true);
  };

  // 저장소 삭제 처리
  const handleDeleteRepository = async (repoId: number) => {
    setLoading(true);
    setError(null);
    
    try {
      // 실제 API 호출
      await api.delete(`/github-repos/${repoId}`);
      setSuccess('저장소가 성공적으로 삭제되었습니다.');
      fetchRepositories();
    } catch (err: any) {
      console.error('저장소 삭제 오류:', err);
      
      // 오류 메시지 구성
      let errorMessage = '저장소를 삭제하는 중 오류가 발생했습니다.';
      
      if (err.response) {
        // 서버에서 응답이 왔지만 에러인 경우
        errorMessage += ` (${err.response.status})`;
        if (err.response.data && err.response.data.detail) {
          errorMessage += `: ${err.response.data.detail}`;
        }
      } else if (err.request) {
        // 요청은 보냈지만 응답이 없는 경우
        errorMessage = '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.';
      } else {
        // 요청 설정 중 오류 발생
        errorMessage += `: ${err.message || '알 수 없는 오류'}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 기본 저장소 설정
  const handleSetDefaultRepository = (repo: Repository) => {
    if (repo.is_default) return; // 이미 기본 저장소인 경우

    setConfirmTitle('기본 저장소 설정');
    setConfirmMessage(`"${repo.name}"을(를) 기본 저장소로 설정하시겠습니까?`);
    setConfirmAction(() => () => updateRepositoryDefault(repo.id, true));
    setOpenDialog(true);
  };

  // 저장소 기본 설정 업데이트
  const updateRepositoryDefault = async (repoId: number, isDefault: boolean) => {
    setLoading(true);
    setError(null);
    
    try {
      // 실제 API 호출
      await api.put(`/github-repos/${repoId}`, { is_default: isDefault });
      setSuccess('기본 저장소가 성공적으로 변경되었습니다.');
      fetchRepositories();
    } catch (err: any) {
      console.error('저장소 업데이트 오류:', err);
      
      // 오류 메시지 구성
      let errorMessage = '저장소 설정을 업데이트하는 중 오류가 발생했습니다.';
      
      if (err.response) {
        // 서버에서 응답이 왔지만 에러인 경우
        errorMessage += ` (${err.response.status})`;
        if (err.response.data && err.response.data.detail) {
          errorMessage += `: ${err.response.data.detail}`;
        }
      } else if (err.request) {
        // 요청은 보냈지만 응답이 없는 경우
        errorMessage = '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.';
      } else {
        // 요청 설정 중 오류 발생
        errorMessage += `: ${err.message || '알 수 없는 오류'}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 토큰 표시/숨김 토글
  const toggleTokenVisibility = (repoId: number) => {
    setShowTokens({
      ...showTokens,
      [repoId]: !showTokens[repoId]
    });
  };

  return (
    <>
      <Head>
        <title>GitHub 설정 - LLMNightRun</title>
        <meta name="description" content="GitHub 저장소 설정 관리" />
      </Head>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          GitHub 설정
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          GitHub 저장소를 연결하고 관리합니다. 연결된 저장소를 통해 생성된 코드를 저장하고 공유할 수 있습니다.
        </Typography>

        {/* 저장소 추가/수정 폼 */}
        <Card elevation={0} variant="outlined" sx={{ mb: 4, mt: 3 }}>
          <CardHeader 
            title={editMode ? "저장소 편집" : "새 GitHub 저장소 연결"} 
            avatar={<GitHubIcon />}
          />
          <CardContent>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    name="name"
                    label="저장소 이름"
                    value={formData.name}
                    onChange={handleChange}
                    fullWidth
                    required
                    helperText="GitHub 저장소 이름 (예: my-project)"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    name="owner"
                    label="소유자"
                    value={formData.owner}
                    onChange={handleChange}
                    fullWidth
                    required
                    helperText="GitHub 사용자명 또는 조직명"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    name="description"
                    label="설명"
                    value={formData.description}
                    onChange={handleChange}
                    fullWidth
                    multiline
                    rows={2}
                    helperText="저장소에 대한 간단한 설명 (선택 사항)"
                  />
                </Grid>
                <Grid item xs={12} md={8}>
                  <TextField
                    name="token"
                    label="GitHub 토큰"
                    value={formData.token}
                    onChange={handleChange}
                    fullWidth
                    required
                    type="password"
                    helperText="GitHub 개인 액세스 토큰 (repo 권한 필요)"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    name="branch"
                    label="기본 브랜치"
                    value={formData.branch}
                    onChange={handleChange}
                    fullWidth
                    helperText="기본 브랜치 이름 (일반적으로 main)"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        name="is_default"
                        checked={formData.is_default}
                        onChange={handleChange}
                        color="primary"
                      />
                    }
                    label="기본 저장소로 설정"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        name="is_private"
                        checked={formData.is_private}
                        onChange={handleChange}
                        color="primary"
                      />
                    }
                    label="비공개 저장소"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, gap: 1 }}>
                    {editMode && (
                      <Button
                        variant="outlined"
                        onClick={resetForm}
                        disabled={loading}
                      >
                        취소
                      </Button>
                    )}
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={20} /> : null}
                    >
                      {editMode ? '저장소 업데이트' : '저장소 추가'}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </form>
          </CardContent>
        </Card>

        {/* 저장소 목록 */}
        <Card elevation={0} variant="outlined">
          <CardHeader 
            title="연결된 GitHub 저장소" 
            action={
              <Tooltip title="새로고침">
                <IconButton onClick={fetchRepositories} disabled={loadingRepos}>
                  {loadingRepos ? <CircularProgress size={24} /> : <RefreshIcon />}
                </IconButton>
              </Tooltip>
            }
          />
          <CardContent>
            {repositories.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <Typography variant="body1" color="text.secondary">
                  {loadingRepos ? '저장소 목록을 불러오는 중...' : '연결된 GitHub 저장소가 없습니다.'}
                </Typography>
                {!loadingRepos && (
                  <Button 
                    variant="outlined" 
                    startIcon={<AddIcon />} 
                    sx={{ mt: 2 }}
                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                  >
                    새 저장소 추가
                  </Button>
                )}
              </Box>
            ) : (
              <List>
                {repositories.map((repo) => (
                  <ListItem
                    key={repo.id}
                    divider
                    secondaryAction={
                      <Box>
                        <Tooltip title="편집">
                          <IconButton edge="end" onClick={() => handleEditRepository(repo)}>
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="삭제">
                          <IconButton edge="end" onClick={() => confirmDeleteRepository(repo)}>
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    }
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">
                            {repo.owner}/{repo.name}
                          </Typography>
                          {repo.is_default && (
                            <Tooltip title="기본 저장소">
                              <SettingsIcon fontSize="small" color="primary" />
                            </Tooltip>
                          )}
                          {repo.is_private && (
                            <Tooltip title="비공개 저장소">
                              <LockIcon fontSize="small" />
                            </Tooltip>
                          )}
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography variant="body2" color="text.secondary" component="div">
                            {repo.description || '설명 없음'}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                            <Typography variant="body2" component="div" sx={{ mr: 1 }}>
                              토큰:
                            </Typography>
                            <TextField
                              variant="outlined"
                              size="small"
                              value={showTokens[repo.id] ? repo.token : '••••••••••••••••'}
                              InputProps={{
                                readOnly: true,
                                endAdornment: (
                                  <IconButton
                                    edge="end"
                                    onClick={() => toggleTokenVisibility(repo.id)}
                                    size="small"
                                  >
                                    {showTokens[repo.id] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                  </IconButton>
                                ),
                              }}
                              sx={{ flex: 1 }}
                            />
                            {!repo.is_default && (
                              <Button
                                variant="text"
                                size="small"
                                onClick={() => handleSetDefaultRepository(repo)}
                                sx={{ ml: 1 }}
                              >
                                기본으로 설정
                              </Button>
                            )}
                          </Box>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        </Card>

        {/* 확인 대화상자 */}
        <Dialog
          open={openDialog}
          onClose={() => setOpenDialog(false)}
        >
          <DialogTitle>{confirmTitle}</DialogTitle>
          <DialogContent>
            <DialogContentText>
              {confirmMessage}
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>취소</Button>
            <Button 
              onClick={() => {
                setOpenDialog(false);
                confirmAction();
              }} 
              variant="contained" 
              color="primary" 
              autoFocus
            >
              확인
            </Button>
          </DialogActions>
        </Dialog>

        {/* 알림 메시지 */}
        <Snackbar 
          open={!!error || !!success} 
          autoHideDuration={6000} 
          onClose={() => {
            setError(null);
            setSuccess(null);
          }}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert 
            onClose={() => {
              setError(null);
              setSuccess(null);
            }} 
            severity={error ? "error" : "success"} 
            variant="filled"
          >
            {error || success}
          </Alert>
        </Snackbar>
      </Container>
    </>
  );
};

export default GitHubSettingsPage;