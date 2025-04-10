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
  Divider
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';
import axios from 'axios';

// API 기본 URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

// 저장소 API 함수 정의
const fetchRepositories = async (): Promise<Repository[]> => {
  try {
    try {
      const response = await axios.get(`${API_BASE_URL}/github/repositories`);
      return response.data.repositories || [];
    } catch (apiError) {
      console.error('저장소 목록 조회 오류:', apiError);
      // API가 아직 준비되지 않은 경우 - 빈 배열 반환
      return [];
    }
  } catch (error) {
    console.error('예상치 못한 오류:', error);
    return [];
  }
};

const createRepository = async (data: CreateRepositoryRequest): Promise<Repository> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/github/repositories`, data);
    return response.data;
  } catch (error) {
    console.error('저장소 생성 오류:', error);
    throw error;
  }
};

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
  const [loading, setLoading] = useState(false);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  
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
  
  // 저장소 목록 로드 함수
  const loadRepositories = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetchRepositories();
      setRepositories(response);
    } catch (err) {
      console.error('저장소 목록 로드 오류:', err);
      setError('저장소 목록을 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  // 저장소 생성 함수
  const handleCreateRepository = async () => {
    // 필수 필드 확인
    if (!newRepo.name || !newRepo.owner || !newRepo.token) {
      alert('이름, 소유자, 토큰은 필수 입력 필드입니다.');
      return;
    }
    
    setLoading(true);
    setCreateError(null);
    
    try {
      const newRepository = await createRepository(newRepo as CreateRepositoryRequest);
      
      // 목록에 새 저장소 추가
      setRepositories(prev => [...prev, newRepository]);
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
    } catch (err) {
      console.error('저장소 생성 오류:', err);
      setCreateError('저장소를 생성하는 중 오류가 발생했습니다.');
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
          
          {repositories && repositories.map((repo) => (
            <MenuItem key={repo.id} value={repo.id}>
              {repo.owner}/{repo.name}
              {repo.is_default && (
                <Typography variant="caption" sx={{ ml: 1, opacity: 0.7 }}>
                  (기본)
                </Typography>
              )}
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
          </Grid>
          
          {createError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              저장소 추가 중 오류가 발생했습니다: {createError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>취소</Button>
          <Button 
            onClick={handleCreateRepository} 
            variant="contained" 
            disabled={loading}
          >
            {loading ? '저장 중...' : '저장소 추가'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default RepositorySelector;