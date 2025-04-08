import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  List, 
  ListItem, 
  ListItemText, 
  Chip, 
  IconButton, 
  Divider,
  TextField,
  InputAdornment,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Badge,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent
} from '@mui/material';
import {
  Search as SearchIcon,
  Delete as DeleteIcon,
  Info as InfoIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Memory as MemoryIcon
} from '@mui/icons-material';
import axios from 'axios';

// 메모리 유형 정의
export enum MemoryType {
  CONVERSATION = "conversation",
  EXPERIMENT = "experiment",
  CODE = "code",
  RESULT = "result",
  NOTE = "note"
}

// 메모리 인터페이스 정의
export interface Memory {
  id: string;
  content: string;
  type: MemoryType;
  timestamp: number;
  metadata: Record<string, any>;
  score?: number;
}

// 메모리 검색 인터페이스 정의
export interface MemorySearch {
  query: string;
  top_k: number;
  memory_types?: MemoryType[];
  date_from?: string;
  date_to?: string;
  tags?: string[];
}

interface MemoryListProps {
  onSelectMemory?: (memory: Memory) => void;
  selectedMemoryId?: string;
}

const MemoryList: React.FC<MemoryListProps> = ({ onSelectMemory, selectedMemoryId }) => {
  // 상태 관리
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTypes, setSelectedTypes] = useState<MemoryType[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [openDeleteDialog, setOpenDeleteDialog] = useState<boolean>(false);
  const [deleteMemoryId, setDeleteMemoryId] = useState<string | null>(null);
  const [notificationOpen, setNotificationOpen] = useState<boolean>(false);
  const [notificationMessage, setNotificationMessage] = useState<string>('');
  const [notificationSeverity, setNotificationSeverity] = useState<'success' | 'error' | 'info'>('info');

  // 컴포넌트 마운트 시 메모리 로드
  useEffect(() => {
    loadMemories();
    countMemories();
  }, []);

  // 메모리 총 개수 조회
  const countMemories = async () => {
    try {
      const response = await axios.get('/api/memory/count', {
        baseURL: window.location.origin,
        timeout: 5000
      });
      setTotalCount(response.data.count);
    } catch (err) {
      console.error('메모리 개수 조회 실패:', err);
      // 오류 발생 시 현재 보여주는 메모리 수를 총개수로 설정
      setTotalCount(memories.length);
    }
  };

  // 메모리 로드 함수
  const loadMemories = async () => {
    setLoading(true);
    setError(null);
    try {
      const searchParams: MemorySearch = {
        query: searchQuery || '',
        top_k: 50,
      };
      
      if (selectedTypes.length > 0) {
        searchParams.memory_types = selectedTypes;
      }
      
      const response = await axios.post('/api/memory/search', searchParams, {
        baseURL: window.location.origin,  // 명시적 기본 URL
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000  // 10초 타임아웃
      });
      setMemories(response.data);
      
    } catch (err) {
      console.error('메모리 로드 실패:', err);
      setError('메모리를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 검색 실행
  const handleSearch = () => {
    loadMemories();
  };

  // 엔터 키로 검색
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // 메모리 삭제 다이얼로그 열기
  const handleOpenDeleteDialog = (memoryId: string) => {
    setDeleteMemoryId(memoryId);
    setOpenDeleteDialog(true);
  };

  // 메모리 삭제 확인
  const handleDeleteConfirm = async () => {
    if (!deleteMemoryId) return;
    
    try {
      await axios.delete(`/api/memory/delete/${deleteMemoryId}`, {
        baseURL: window.location.origin,
        timeout: 10000
      });
      
      // 메모리 목록에서 삭제된 항목 제거
      setMemories(memories.filter(memory => memory.id !== deleteMemoryId));
      
      // 알림 표시
      showNotification('메모리가 성공적으로 삭제되었습니다.', 'success');
      
      // 총 개수 업데이트
      countMemories();
    } catch (err) {
      console.error('메모리 삭제 실패:', err);
      showNotification('메모리 삭제 중 오류가 발생했습니다.', 'error');
    }
    
    setOpenDeleteDialog(false);
    setDeleteMemoryId(null);
  };

  // 필터 변경 처리
  const handleFilterChange = (event: SelectChangeEvent<typeof selectedTypes>) => {
    const {
      target: { value },
    } = event;
    
    // 문자열 배열로 타입 변환
    setSelectedTypes(
      typeof value === 'string' ? [value as MemoryType] : value as MemoryType[]
    );
  };

  // 알림 표시
  const showNotification = (message: string, severity: 'success' | 'error' | 'info') => {
    setNotificationMessage(message);
    setNotificationSeverity(severity);
    setNotificationOpen(true);
  };

  // 알림 닫기
  const handleCloseNotification = () => {
    setNotificationOpen(false);
  };

  // 메모리 타입에 따른 배지 색상
  const getColorByType = (type: MemoryType) => {
    switch (type) {
      case MemoryType.CONVERSATION: return 'primary';
      case MemoryType.EXPERIMENT: return 'secondary';
      case MemoryType.CODE: return 'success';
      case MemoryType.RESULT: return 'warning';
      case MemoryType.NOTE: return 'info';
      default: return 'default';
    }
  };

  // 날짜 포맷팅
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  return (
    <Box>
      {/* 메모리 통계 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item>
              <Badge badgeContent={totalCount} color="primary" max={999}>
                <MemoryIcon fontSize="large" color="primary" />
              </Badge>
            </Grid>
            <Grid item xs>
              <Typography variant="h6">LLM 메모리</Typography>
              <Typography variant="body2" color="text.secondary">
                벡터 데이터베이스에 저장된 총 {totalCount}개의 메모리
              </Typography>
            </Grid>
            <Grid item>
              <IconButton onClick={() => { loadMemories(); countMemories(); }} color="primary">
                <RefreshIcon />
              </IconButton>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 검색 및 필터 */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="메모리 검색"
              variant="outlined"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={handleSearch} edge="end">
                      <SearchIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth variant="outlined">
              <InputLabel id="memory-type-select-label">메모리 유형</InputLabel>
              <Select
                labelId="memory-type-select-label"
                id="memory-type-select"
                multiple
                value={selectedTypes}
                onChange={handleFilterChange}
                label="메모리 유형"
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as MemoryType[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {Object.values(MemoryType).map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* 메모리 목록 */}
      <Paper>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : memories.length > 0 ? (
          <List>
            {memories.map((memory, index) => (
              <React.Fragment key={memory.id}>
                {index > 0 && <Divider />}
                <ListItem
                  alignItems="flex-start"
                  selected={memory.id === selectedMemoryId}
                  sx={{
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.04)' },
                    ...(memory.id === selectedMemoryId && { bgcolor: 'rgba(63, 81, 181, 0.12) !important' })
                  }}
                  onClick={() => onSelectMemory && onSelectMemory(memory)}
                  secondaryAction={
                    <IconButton edge="end" onClick={(e) => {
                      e.stopPropagation();
                      handleOpenDeleteDialog(memory.id);
                    }}>
                      <DeleteIcon />
                    </IconButton>
                  }
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Chip
                          label={memory.type}
                          size="small"
                          color={getColorByType(memory.type) as any}
                          sx={{ mr: 1 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(memory.timestamp)}
                        </Typography>
                        {memory.score !== undefined && (
                          <Chip
                            label={`관련도: ${(memory.score * 100).toFixed(1)}%`}
                            size="small"
                            variant="outlined"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <>
                        <Typography
                          component="span"
                          variant="body2"
                          sx={{
                            display: 'inline',
                            wordBreak: 'break-word',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical',
                          }}
                        >
                          {memory.content}
                        </Typography>
                        {memory.metadata && memory.metadata.tags && memory.metadata.tags.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            {memory.metadata.tags.map((tag: string) => (
                              <Chip
                                key={tag}
                                label={tag}
                                size="small"
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5 }}
                              />
                            ))}
                          </Box>
                        )}
                      </>
                    }
                  />
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              {searchQuery ? '검색 결과가 없습니다.' : '저장된 메모리가 없습니다.'}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* 삭제 확인 다이얼로그 */}
      <Dialog
        open={openDeleteDialog}
        onClose={() => setOpenDeleteDialog(false)}
      >
        <DialogTitle>메모리 삭제</DialogTitle>
        <DialogContent>
          <DialogContentText>
            이 메모리를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDeleteDialog(false)}>취소</Button>
          <Button onClick={handleDeleteConfirm} color="error" autoFocus>
            삭제
          </Button>
        </DialogActions>
      </Dialog>

      {/* 알림 스낵바 */}
      <Snackbar
        open={notificationOpen}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
      >
        <Alert onClose={handleCloseNotification} severity={notificationSeverity} sx={{ width: '100%' }}>
          {notificationMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MemoryList;