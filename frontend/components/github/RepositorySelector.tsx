import React, { useState, useEffect, ChangeEvent } from 'react';
import { 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Button, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField, 
  Box, 
  Typography, 
  CircularProgress,
  Grid,
  FormControlLabel,
  Switch,
  Tooltip,
  IconButton,
  Alert,
  Divider,
  Menu
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import axios from 'axios';
import { API_BASE_URL, GITHUB_API_URL, CORS_FIXED_API_URL } from '../../utils/constants';

// 저장소 유형 정의
interface Repository {
  id: number;
  name: string;
  owner: string;
  description?: string;
  is_default: boolean;
  is_private: boolean;
  url?: string;
  branch: string;
}

// 저장소 생성 요청 유형 정의
interface CreateRepositoryRequest {
  name: string;
  owner: string;
  token: string;
  description?: string;
  is_default: boolean;
  is_private: boolean;
  branch: string;
}

// 컴포넌트 props 유형 정의
interface RepositorySelectorProps {
  value: number | null;
  onChange: (repoId: number | null) => void;
  disabled?: boolean;
}

/**
 * GitHub 저장소 선택 컴포넌트
 * 
 * - 기존 저장소 선택
 * - 새 저장소 추가 다이얼로그
 * - 저장소 목록 새로고침
 */
const RepositorySelector: React.FC<RepositorySelectorProps> = ({ value, onChange, disabled = false }) => {
  // 로컬 상태
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [testSuccess, setTestSuccess] = useState<boolean>(false);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  
  const [newRepo, setNewRepo] = useState<Partial<CreateRepositoryRequest>>({
    name: '',
    owner: '',
    token: '',
    description: '',
    is_default: false,
    is_private: true,
    branch: 'main'
  });
  
  // 컴포넌트 마운트 시 저장소 목록 로드
  useEffect(() => {
    loadRepositories();
  }, []);
  
  // 비상용 백업 데이터 - 모든 API 접근이 실패할 경우
  const FALLBACK_REPOSITORIES = [
    {
      id: 1,
      name: "emergency-fallback-repo",
      owner: "user",
      description: "모든 API 시도가 실패하여 표시되는 비상 데이터입니다. 서버를 확인해주세요.",
      is_default: true,
      is_private: false,
      url: "https://github.com/user/emergency-fallback-repo",
      branch: "main"
    }
  ];

  // 저장소 목록 로드 함수
  const loadRepositories = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 개발 환경에서는 여러 엔드포인트를 시도하고, 프로덕션에서는 메인 API만 사용
      const isDevelopment = process.env.NODE_ENV === 'development';
      
      if (isDevelopment) {
        // 개발 환경에서는 여러 엔드포인트 시도
        let lastError;
        
        // 1. CORS 패치된 백엔드 서버 시도
        try {
          const response = await axios.get(`${CORS_FIXED_API_URL}/github-repos/`, { timeout: 5000 });
          console.log('CORS 패치된 백엔드 GitHub 응답:', response.data);
          
          // 응답 처리
          let repoData = response.data;
          if (!Array.isArray(repoData)) {
            if (repoData && Array.isArray(repoData.repositories)) {
              repoData = repoData.repositories;
            } else {
              throw new Error('응답 데이터가 올바른 형식이 아닙니다');
            }
          }
          
          setRepositories(repoData);
          return;
        } catch (mainErr) {
          console.warn('메인 백엔드 GitHub API 접속 실패:', mainErr);
          lastError = mainErr;
          
          // 2. 디버그 엔드포인트 시도
          try {
            const response = await axios.get(`${API_BASE_URL}/debug/github-repos`, { timeout: 3000 });
            console.log('디버그 GitHub 응답:', response.data);
            setRepositories(response.data);
            return;
          } catch (debugErr) {
            console.warn('디버그 엔드포인트 접속 실패:', debugErr);
            
            // 3. GitHub 프록시 서버 시도 (개발 환경에서만)
            try {
              const response = await axios.get(`${GITHUB_API_URL}/github-repos/`, { timeout: 3000 });
              console.log('GitHub 전용 프록시 서버 응답:', response.data);
              setRepositories(response.data);
              return;
            } catch (proxyErr) {
              console.error('모든 API 시도 실패:', proxyErr);
              lastError = proxyErr;
              
              // 마지막 보안 조치: 모든 API가 실패해도 앱이 작동하도록 비상용 데이터 사용
              console.warn('비상용 백업 데이터로 대체합니다 - 개발 모드 전용');
              setRepositories(FALLBACK_REPOSITORIES);
              setError('모든 API 시도 실패. 비상용 데이터를 표시합니다. (백엔드 서버 연결 필요)');
              return;
            }
          }
        }
        
        // 모든 시도 실패 시 마지막 오류로 처리
        if (lastError) {
          throw lastError;
        }
      } else {
        // 프로덕션 환경에서는 메인 API만 사용
        const response = await axios.get(`${API_BASE_URL}/github-repos/`);
        
        // 응답 처리
        let repoData = response.data;
        if (!Array.isArray(repoData)) {
          if (repoData && Array.isArray(repoData.repositories)) {
            repoData = repoData.repositories;
          } else {
            throw new Error('응답 데이터가 올바른 형식이 아닙니다');
          }
        }
        
        setRepositories(repoData);
      }
    } catch (err: any) {
      console.error('저장소 목록 로드 오류:', err);
      
      // 오류 메시지 구성
      let errorMessage = '저장소 목록을 불러오는 중 오류가 발생했습니다.';
      
      if (err.response) {
        // 서버에서 응답이 왔지만 에러인 경우
        errorMessage += ` (${err.response.status}: ${err.response.statusText})`;
        if (err.response.data && err.response.data.detail) {
          errorMessage += ` - ${err.response.data.detail}`;
        }
      } else if (err.request) {
        // 요청은 보냈지만 응답이 없는 경우
        if (err.code === 'ECONNABORTED') {
          errorMessage = '서버 응답 시간이 초과되었습니다. 나중에 다시 시도해주세요.';
        } else {
          errorMessage = '서버에 연결할 수 없습니다. 네트워크 연결을 확인하세요.';
        }
      } else {
        // 요청 설정 중 오류 발생
        errorMessage += ` - ${err.message || '알 수 없는 오류'}`;
      }
      
      setError(errorMessage);
      
      // 개발 모드에서만 마지막 보안 조치로 비상용 데이터 사용
      if (process.env.NODE_ENV === 'development') {
        console.warn('비상용 백업 데이터로 대체합니다 - 개발 모드 전용');
        setRepositories(FALLBACK_REPOSITORIES);
      } else {
        setRepositories([]); // 프로덕션에서는 빈 배열 설정
      }
    } finally {
      setLoading(false);
    }
  };
  
  // 저장소 연결 테스트
  const handleTestConnection = async () => {
    if (!newRepo.name || !newRepo.owner || !newRepo.token) {
      alert('이름, 소유자, 토큰은 모두 필수 입력 필드입니다.');
      return;
    }
    
    setTestingConnection(true);
    setCreateError(null);
    setTestSuccess(false);
    
    try {
      // GitHub 연결 테스트 API 호출
      const response = await axios.post(`${API_BASE_URL}/github/test-connection`, {
        repo_url: `${newRepo.owner}/${newRepo.name}`,
        token: newRepo.token,
        username: newRepo.owner
      });
      
      if (response.data.success) {
        // 연결 테스트 성공
        setTestSuccess(true);
        setCreateError(null);
      } else {
        // 테스트는 실행됐지만 실패한 경우
        setTestSuccess(false);
        setCreateError(`연결 테스트 실패: ${response.data.message}\n${response.data.error || ''}`);
      }
    } catch (error: any) {
      console.error('GitHub 연결 테스트 오류:', error);
      setTestSuccess(false);
      
      if (error.response) {
        setCreateError(`GitHub 연결 테스트 오류: ${error.response.data?.detail || error.message}`);
      } else {
        setCreateError('연결 테스트 중 오류가 발생했습니다.');
      }
    } finally {
      setTestingConnection(false);
    }
  };
  
  // 저장소 생성 함수
  const handleCreateRepository = async () => {
    // 필수 필드 확인
    if (!newRepo.name || !newRepo.owner || !newRepo.token) {
      alert('이름, 소유자, 토큰은 필수 입력 필드입니다.');
      return;
    }
    
    // 테스트 성공 확인 (개발 모드에서는 건너뜀)
    if (!testSuccess && process.env.NODE_ENV !== 'development') {
      const confirmAdd = window.confirm('GitHub 연결 테스트를 수행하지 않았거나 실패했습니다. 그래도 계속하시겠습니까?');
      if (!confirmAdd) return;
    }
    
    setLoading(true);
    setCreateError(null);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/github-repos`, newRepo);
      
      // 성공적으로 생성된 경우 목록에 추가
      await loadRepositories();
      setDialogOpen(false);
      
      // 폼 초기화
      setNewRepo({
        name: '',
        owner: '',
        token: '',
        description: '',
        is_default: false,
        is_private: true,
        branch: 'main'
      });
      
      setTestSuccess(false);
    } catch (err: any) {
      console.error('저장소 생성 오류:', err);
      
      if (err.response) {
        setCreateError(`저장소 생성 실패: ${err.response.data?.detail || err.message}`);
      } else {
        setCreateError('저장소를 생성하는 중 오류가 발생했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  // 메뉴 열기 핸들러
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, repo: Repository) => {
    setSelectedRepo(repo);
    setAnchorEl(event.currentTarget);
  };

  // 메뉴 닫기 핸들러
  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // 저장소 편집 다이얼로그 열기
  const handleOpenEditDialog = () => {
    if (selectedRepo) {
      setNewRepo({
        name: selectedRepo.name,
        owner: selectedRepo.owner,
        token: '', // 토큰은 보안상의 이유로 다시 입력해야 함
        description: selectedRepo.description || '',
        is_default: selectedRepo.is_default,
        is_private: selectedRepo.is_private,
        branch: selectedRepo.branch || 'main'
      });
      setEditDialogOpen(true);
      handleMenuClose();
    }
  };

  // 저장소 삭제 다이얼로그 열기
  const handleOpenDeleteDialog = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  // 저장소 편집 함수
  const handleEditRepository = async () => {
    if (!selectedRepo) return;
    
    // 필수 필드 확인
    if (!newRepo.name || !newRepo.owner) {
      alert('이름과 소유자는 필수 입력 필드입니다.');
      return;
    }
    
    setLoading(true);
    setCreateError(null);
    
    try {
      const updateData = {...newRepo};
      
      // 토큰이 비어있으면 업데이트 데이터에서 제외
      if (!updateData.token) {
        delete updateData.token;
      }
      
      await axios.put(`${API_BASE_URL}/github-repos/${selectedRepo.id}`, updateData);
      
      // 성공적으로 수정된 경우 목록 새로고침
      await loadRepositories();
      setEditDialogOpen(false);
      
      // 폼 초기화
      setNewRepo({
        name: '',
        owner: '',
        token: '',
        description: '',
        is_default: false,
        is_private: true,
        branch: 'main'
      });
      
      setSelectedRepo(null);
    } catch (err: any) {
      console.error('저장소 수정 오류:', err);
      
      if (err.response) {
        setCreateError(`저장소 수정 실패: ${err.response.data?.detail || err.message}`);
      } else {
        setCreateError('저장소를 수정하는 중 오류가 발생했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  // 저장소 삭제 함수
  const handleDeleteRepository = async () => {
    if (!selectedRepo) return;
    
    setLoading(true);
    
    try {
      await axios.delete(`${API_BASE_URL}/github-repos/${selectedRepo.id}`);
      
      // 성공적으로 삭제된 경우 목록 새로고침
      await loadRepositories();
      setDeleteDialogOpen(false);
      
      // 현재 선택된 저장소가 삭제된 경우 선택 취소
      if (value === selectedRepo.id) {
        onChange(null);
      }
      
      setSelectedRepo(null);
    } catch (err: any) {
      console.error('저장소 삭제 오류:', err);
      alert(`저장소 삭제 실패: ${err.response?.data?.detail || err.message || '알 수 없는 오류'}`);
    } finally {
      setLoading(false);
    }
  };
  
  // 저장소 변경 핸들러
  const handleRepositoryChange = (event: any) => {
    const value = event.target.value;
    onChange(value ? Number(value) : null);
  };
  
  // 폼 입력 변경 핸들러
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown; checked?: boolean }>) => {
    const target = e.target as HTMLInputElement;
    const name = target.name as string;
    const value = target.value;
    const checked = target.checked;
    const type = target.type;
    
    setNewRepo({
      ...newRepo,
      [name]: type === 'checkbox' || name === 'is_default' || name === 'is_private' ? checked : value
    });
    
    // 연결 정보가 변경되면 테스트 상태 초기화
    if (name === 'name' || name === 'owner' || name === 'token') {
      setTestSuccess(false);
    }
  };
  
  return (
    <>
      <FormControl fullWidth variant="outlined" disabled={disabled || loading}>
        <InputLabel id="repository-select-label">GitHub 저장소</InputLabel>
        <Select
          labelId="repository-select-label"
          value={value === null ? '' : value}
          onChange={handleRepositoryChange}
          label="GitHub 저장소"
          startAdornment={
            <Box sx={{ display: 'flex', ml: -1, mr: 1 }}>
              <Tooltip title="새 저장소 추가">
                <IconButton 
                  size="small" 
                  onClick={(e) => {
                    e.stopPropagation();
                    setDialogOpen(true);
                  }}
                  disabled={disabled}
                >
                  <AddIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="저장소 목록 새로고침">
                <IconButton 
                  size="small" 
                  onClick={(e) => {
                    e.stopPropagation();
                    loadRepositories();
                  }}
                  disabled={disabled || loading}
                >
                  {loading ? (
                    <CircularProgress size={18} />
                  ) : (
                    <RefreshIcon fontSize="small" />
                  )}
                </IconButton>
              </Tooltip>
            </Box>
          }
        >
          <MenuItem value="">
            <em>저장소 선택</em>
          </MenuItem>
          
          {repositories && Array.isArray(repositories) && repositories.map((repo) => (
            <MenuItem key={repo.id} value={repo.id} sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                {repo.owner}/{repo.name}
                {repo.is_default && (
                  <Typography variant="caption" sx={{ ml: 1, opacity: 0.7 }}>
                    (기본)
                  </Typography>
                )}
              </div>
              <IconButton
                size="small"
                edge="end"
                onClick={(e) => {
                  e.stopPropagation();
                  handleMenuOpen(e, repo);
                }}
                sx={{ ml: 1 }}
              >
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      
      {/* 새 저장소 추가 다이얼로그 */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>새 GitHub 저장소 설정</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2, mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              GitHub 저장소 정보를 입력하세요. 토큰은 저장소 액세스 권한이 있는 개인 액세스 토큰이어야 합니다.
            </Typography>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                name="owner"
                label="저장소 소유자"
                placeholder="GitHub 사용자 이름 또는 조직명"
                value={newRepo.owner}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                name="name"
                label="저장소 이름"
                placeholder="my-awesome-repo"
                value={newRepo.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                required
                name="token"
                label="GitHub 토큰"
                placeholder="ghp_..."
                type="password"
                value={newRepo.token}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                name="description"
                label="설명 (선택 사항)"
                placeholder="저장소 설명"
                value={newRepo.description}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="branch"
                label="기본 브랜치"
                value={newRepo.branch}
                onChange={handleInputChange}
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
            
            <Grid item xs={12}>
              <Button 
                fullWidth 
                variant="outlined" 
                color="primary"
                onClick={handleTestConnection}
                disabled={testingConnection || !newRepo.name || !newRepo.owner || !newRepo.token}
                startIcon={testingConnection ? <CircularProgress size={18} /> : testSuccess ? <CheckCircleIcon color="success" /> : null}
              >
                {testingConnection ? '연결 테스트 중...' : testSuccess ? '연결 테스트 성공' : 'GitHub 연결 테스트'}
              </Button>
            </Grid>
          </Grid>
          
          {testSuccess && (
            <Alert severity="success" sx={{ mt: 2 }} icon={<CheckCircleIcon />}>
              GitHub 연결 테스트가 성공했습니다! 저장소에 성공적으로 연결되었습니다.
            </Alert>
          )}
          
          {createError && (
            <Alert severity="error" sx={{ mt: 2 }} icon={<ErrorIcon />}>
              {createError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            취소
          </Button>
          <Button 
            onClick={handleCreateRepository} 
            variant="contained" 
            color="primary"
            disabled={loading}
          >
            {loading ? '저장 중...' : '저장소 추가'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 저장소 편집 다이얼로그 */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>GitHub 저장소 편집</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2, mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              GitHub 저장소 정보를 수정하세요. 토큰은 변경하지 않으려면 비워두세요.
            </Typography>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                name="owner"
                label="저장소 소유자"
                value={newRepo.owner}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                name="name"
                label="저장소 이름"
                value={newRepo.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                name="token"
                label="GitHub 토큰 (변경 시에만 입력)"
                type="password"
                value={newRepo.token}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                name="description"
                label="설명 (선택 사항)"
                value={newRepo.description}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="branch"
                label="기본 브랜치"
                value={newRepo.branch}
                onChange={handleInputChange}
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
          
          {createError && (
            <Alert severity="error" sx={{ mt: 2 }} icon={<ErrorIcon />}>
              {createError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>
            취소
          </Button>
          <Button 
            onClick={handleEditRepository} 
            variant="contained" 
            color="primary"
            disabled={loading}
          >
            {loading ? '저장 중...' : '저장소 수정'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 저장소 삭제 확인 다이얼로그 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>저장소 삭제 확인</DialogTitle>
        <DialogContent>
          <Typography>
            정말로 저장소 <strong>{selectedRepo?.owner}/{selectedRepo?.name}</strong>을(를) 삭제하시겠습니까?
          </Typography>
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            이 작업은 되돌릴 수 없으며, 로컬 설정만 삭제됩니다. GitHub의 원격 저장소는 영향을 받지 않습니다.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            취소
          </Button>
          <Button 
            onClick={handleDeleteRepository} 
            variant="contained" 
            color="error"
            disabled={loading}
          >
            {loading ? '삭제 중...' : '삭제'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 저장소 옵션 메뉴 */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleOpenEditDialog}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          편집
        </MenuItem>
        <MenuItem onClick={handleOpenDeleteDialog}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          삭제
        </MenuItem>
      </Menu>
    </>
  );
};

export default RepositorySelector;