import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  LinearProgress,
  Tab,
  Tabs
} from '@mui/material';

import {
  Search as SearchIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayArrowIcon,
  Storage as StorageIcon,
  CleaningServices as CleaningServicesIcon,
  History as HistoryIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  BarChart as BarChartIcon
} from '@mui/icons-material';

import api from '../../utils/api';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`indexing-tabpanel-${index}`}
      aria-labelledby={`indexing-tab-${index}`}
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

const CodebaseIndexing = ({ codebaseId }) => {
  const [activeTab, setActiveTab] = useState(0);
  
  // 인덱싱 상태 관리
  const [indexingStatus, setIndexingStatus] = useState(null);
  const [indexingSettings, setIndexingSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // 설정 편집 상태
  const [editSettingsOpen, setEditSettingsOpen] = useState(false);
  const [editedSettings, setEditedSettings] = useState(null);
  
// 패턴 관리
  const [currentPattern, setCurrentPattern] = useState('');
  const [patternType, setPatternType] = useState('exclude'); // 'exclude' 또는 'priority'
  
  // 검색 상태
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  
  // 모달 상태
  const [settingsChanged, setSettingsChanged] = useState(false);
  
  // 초기 데이터 로드
  useEffect(() => {
    if (codebaseId) {
      loadIndexingStatus();
    }
  }, [codebaseId]);
  
  // 인덱싱 상태 로드
  const loadIndexingStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/codebases/${codebaseId}/indexing/status`);
      setIndexingStatus(response.data);
      setIndexingSettings(response.data.settings);
      
      // 5초마다 상태 업데이트 (인덱싱 중일 때)
      if (response.data.status.is_indexing_now) {
        setTimeout(loadIndexingStatus, 5000);
      }
      
    } catch (err) {
      console.error('인덱싱 상태 로딩 오류:', err);
      setError('인덱싱 상태를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  // 인덱싱 트리거
  const handleTriggerIndexing = async (isFullIndex = false) => {
    try {
      setLoading(true);
      
      await api.post(`/codebases/${codebaseId}/indexing/trigger`, {
        codebase_id: codebaseId,
        is_full_index: isFullIndex
      });
      
      // 상태 새로고침
      await loadIndexingStatus();
      
    } catch (err) {
      console.error('인덱싱 트리거 오류:', err);
      setError('인덱싱을 시작하는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  // 인덱싱 설정 저장
  const handleSaveSettings = async () => {
    try {
      setLoading(true);
      
      // 변경된 설정만 전송
      const changedSettings = {};
      for (const key in editedSettings) {
        if (JSON.stringify(editedSettings[key]) !== JSON.stringify(indexingSettings[key])) {
          changedSettings[key] = editedSettings[key];
        }
      }
      
      await api.patch(`/codebases/${codebaseId}/indexing/settings`, changedSettings);
      
      // 상태 새로고침
      await loadIndexingStatus();
      
      // 모달 닫기
      setEditSettingsOpen(false);
      setSettingsChanged(false);
      
    } catch (err) {
      console.error('설정 저장 오류:', err);
      setError('설정을 저장하는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  // 패턴 추가
  const handleAddPattern = () => {
    if (!currentPattern.trim()) return;
    
    const newSettings = { ...editedSettings };
    const patternList = patternType === 'exclude' ? 'excluded_patterns' : 'priority_patterns';
    
    if (!newSettings[patternList].includes(currentPattern)) {
      newSettings[patternList] = [...newSettings[patternList], currentPattern];
      setEditedSettings(newSettings);
      setCurrentPattern('');
      setSettingsChanged(true);
    }
  };
  
  // 패턴 삭제
  const handleDeletePattern = (pattern, type) => {
    const newSettings = { ...editedSettings };
    const patternList = type === 'exclude' ? 'excluded_patterns' : 'priority_patterns';
    
    newSettings[patternList] = newSettings[patternList].filter(p => p !== pattern);
    setEditedSettings(newSettings);
    setSettingsChanged(true);
  };
  
  // 임베딩 정리
  const handleCleanupEmbeddings = async () => {
    try {
      setLoading(true);
      
      await api.post(`/codebases/${codebaseId}/indexing/cleanup`);
      
      // 상태 새로고침
      await loadIndexingStatus();
      
    } catch (err) {
      console.error('임베딩 정리 오류:', err);
      setError('임베딩 정리 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  // 코드 검색
  const handleSearchCode = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      setSearching(true);
      
      const response = await api.post(`/codebases/${codebaseId}/indexing/search`, {
        codebase_id: codebaseId,
        query: searchQuery,
        limit: 10,
        threshold: 0.5
      });
      
      setSearchResults(response.data.results);
      
    } catch (err) {
      console.error('코드 검색 오류:', err);
      setError('코드 검색 중 오류가 발생했습니다.');
    } finally {
      setSearching(false);
    }
  };
  
  // 설정 편집 모달 열기
  const handleOpenSettingsModal = () => {
    setEditedSettings({ ...indexingSettings });
    setEditSettingsOpen(true);
    setSettingsChanged(false);
  };
  
  // 탭 변경 핸들러
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  // 상태 표시기 렌더링
  const renderStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'pending':
        return <PendingIcon color="warning" />;
      case 'in_progress':
        return <CircularProgress size={20} />;
      default:
        return null;
    }
  };
  
  // 로딩 중
  if (loading && !indexingStatus) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>인덱싱 데이터를 불러오는 중...</Typography>
      </Box>
    );
  }
  
  // 오류 상태
  if (error && !indexingStatus) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button 
          variant="outlined" 
          onClick={loadIndexingStatus} 
          startIcon={<RefreshIcon />}
          sx={{ mt: 2 }}
        >
          다시 시도
        </Button>
      </Box>
    );
  }
  
  // 데이터 없음
  if (!indexingStatus) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">인덱싱 데이터가 없습니다.</Alert>
      </Box>
    );
  }
  
  return (
    <Box sx={{ width: '100%' }}>
      {/* 상단 요약 정보 */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader 
                title="인덱싱 상태" 
                action={
                  <IconButton onClick={loadIndexingStatus}>
                    <RefreshIcon />
                  </IconButton>
                }
              />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">상태</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                      {indexingStatus.status.is_indexing_now ? (
                        <>
                          <CircularProgress size={20} sx={{ mr: 1 }} />
                          <Typography>인덱싱 진행 중</Typography>
                        </>
                      ) : (
                        <Typography>대기 중</Typography>
                      )}
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">인덱싱 활성화</Typography>
                    <Typography>
                      {indexingSettings.is_enabled ? '활성화됨' : '비활성화됨'}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">임베딩 모델</Typography>
                    <Typography>{indexingSettings.embedding_model}</Typography>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">인덱싱 주기</Typography>
                    <Typography>
                      {indexingSettings.frequency === 'manual' ? '수동' : 
                       indexingSettings.frequency === 'on_commit' ? '커밋 시' :
                       indexingSettings.frequency === 'hourly' ? '매시간' :
                       indexingSettings.frequency === 'daily' ? '매일' : '매주'}
                    </Typography>
                  </Grid>
                </Grid>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="body2" color="text.secondary" gutterBottom>통계</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Typography variant="body2">임베딩 수</Typography>
                    <Typography variant="h6">{indexingStatus.statistics.total_embeddings}</Typography>
                  </Grid>
                  
                  <Grid item xs={4}>
                    <Typography variant="body2">인덱싱된 파일</Typography>
                    <Typography variant="h6">{indexingStatus.statistics.indexed_files}</Typography>
                  </Grid>
                  
                  <Grid item xs={4}>
                    <Typography variant="body2">마지막 인덱싱</Typography>
                    <Typography variant="body2">
                      {indexingStatus.statistics.last_indexed_at ? 
                        new Date(indexingStatus.statistics.last_indexed_at).toLocaleString() : 
                        '없음'}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader 
                title="인덱싱 작업" 
                action={
                  <IconButton onClick={handleOpenSettingsModal}>
                    <SettingsIcon />
                  </IconButton>
                }
              />
              <CardContent>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    인덱싱 실행
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      startIcon={<PlayArrowIcon />}
                      onClick={() => handleTriggerIndexing(false)}
                      disabled={indexingStatus.status.is_indexing_now || !indexingSettings.is_enabled}
                    >
                      증분 인덱싱 시작
                    </Button>
                    
                    <Button
                      variant="outlined"
                      startIcon={<PlayArrowIcon />}
                      onClick={() => handleTriggerIndexing(true)}
                      disabled={indexingStatus.status.is_indexing_now || !indexingSettings.is_enabled}
                    >
                      전체 인덱싱 시작
                    </Button>
                  </Box>
                </Box>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  최근 인덱싱 실행
                </Typography>
                
                {indexingStatus.status.last_run.id ? (
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {renderStatusIcon(indexingStatus.status.last_run.status)}
                      <Typography sx={{ ml: 1 }}>
                        {indexingStatus.status.last_run.status === 'completed' ? '완료됨' :
                         indexingStatus.status.last_run.status === 'failed' ? '실패' :
                         indexingStatus.status.last_run.status === 'pending' ? '대기 중' :
                         '진행 중'}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      <Typography variant="body2">
                        시작: {indexingStatus.status.last_run.start_time ? 
                          new Date(indexingStatus.status.last_run.start_time).toLocaleString() : 
                          '대기 중'}
                      </Typography>
                      {indexingStatus.status.last_run.end_time && (
                        <Typography variant="body2">
                          종료: {new Date(indexingStatus.status.last_run.end_time).toLocaleString()}
                        </Typography>
                      )}
                      <Typography variant="body2">
                        처리된 파일: {indexingStatus.status.last_run.files_processed}
                      </Typography>
                      <Typography variant="body2">
                        인덱싱된 파일: {indexingStatus.status.last_run.files_indexed}
                      </Typography>
                    </Box>
                    
                    {indexingStatus.status.last_run.error_message && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        {indexingStatus.status.last_run.error_message}
                      </Alert>
                    )}
                  </Box>
                ) : (
                  <Typography>인덱싱 실행 내역이 없습니다.</Typography>
                )}
                
                <Divider sx={{ my: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    variant="outlined"
                    startIcon={<CleaningServicesIcon />}
                    onClick={handleCleanupEmbeddings}
                    disabled={indexingStatus.status.is_indexing_now}
                  >
                    임베딩 정리
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
      
      {/* 탭 내비게이션 */}
      <Box sx={{ width: '100%', mb: 3 }}>
        <Paper>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="fullWidth"
            indicatorColor="primary"
            textColor="primary"
          >
            <Tab icon={<SearchIcon />} label="코드 검색" />
            <Tab icon={<StorageIcon />} label="인덱싱 설정" />
            <Tab icon={<HistoryIcon />} label="인덱싱 기록" />
          </Tabs>
        </Paper>
      </Box>
      
      {/* 코드 검색 탭 */}
      <TabPanel value={activeTab} index={0}>
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>코드 검색</Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <TextField
                fullWidth
                label="코드 검색어 입력"
                variant="outlined"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchCode()}
                sx={{ mr: 2 }}
              />
              <Button
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={handleSearchCode}
                disabled={!searchQuery.trim() || searching}
              >
                {searching ? <CircularProgress size={24} /> : '검색'}
              </Button>
            </Box>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              키워드로 코드를 검색하거나, 자연어 질문을 통해 코드베이스를 탐색할 수 있습니다.
            </Typography>
            
            <Box>
              <Chip label="예시: 파일 저장 함수" onClick={() => setSearchQuery('파일 저장 함수')} sx={{ m: 0.5 }} />
              <Chip label="예시: 데이터베이스 연결" onClick={() => setSearchQuery('데이터베이스 연결')} sx={{ m: 0.5 }} />
              <Chip label="예시: 인증 관련 코드" onClick={() => setSearchQuery('인증 관련 코드')} sx={{ m: 0.5 }} />
            </Box>
          </Paper>
          
          {/* 검색 결과 */}
          {searchResults.length > 0 && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>검색 결과 ({searchResults.length})</Typography>
              
              {searchResults.map((result, index) => (
                <Accordion key={index} sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                      <Box>
                        <Typography fontWeight="bold">
                          {result.file_path}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          유사도: {Math.round(result.similarity_score * 100)}%
                        </Typography>
                      </Box>
                      <Chip 
                        size="small" 
                        label={result.metadata?.language || '기타'} 
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box
                      component="pre"
                      sx={{
                        fontFamily: 'monospace',
                        p: 2,
                        bgcolor: '#f5f5f5',
                        borderRadius: 1,
                        overflow: 'auto'
                      }}
                    >
                      {result.content}
                    </Box>
                    
                    {result.metadata?.code_elements && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>코드 요소</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {result.metadata.code_elements.classes?.map((cls, i) => (
                            <Chip key={`class-${i}`} label={`클래스: ${cls}`} size="small" color="primary" variant="outlined" />
                          ))}
                          {result.metadata.code_elements.functions?.map((func, i) => (
                            <Chip key={`func-${i}`} label={`함수: ${func}`} size="small" color="secondary" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}
            </Paper>
          )}
          
          {searchQuery && searchResults.length === 0 && !searching && (
            <Alert severity="info">
              검색 결과가 없습니다. 다른 키워드로 검색해보세요.
            </Alert>
          )}
        </Box>
      </TabPanel>
      
      {/* 인덱싱 설정 탭 */}
      <TabPanel value={activeTab} index={1}>
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">인덱싱 설정</Typography>
            <Button
              variant="contained"
              startIcon={<SettingsIcon />}
              onClick={handleOpenSettingsModal}
            >
              설정 편집
            </Button>
          </Box>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>기본 설정</Typography>
              <List>
                <ListItem>
                  <ListItemText 
                    primary="인덱싱 활성화" 
                    secondary={indexingSettings.is_enabled ? '활성화됨' : '비활성화됨'} 
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText 
                    primary="인덱싱 주기" 
                    secondary={
                      indexingSettings.frequency === 'manual' ? '수동' : 
                      indexingSettings.frequency === 'on_commit' ? '커밋 시' :
                      indexingSettings.frequency === 'hourly' ? '매시간' :
                      indexingSettings.frequency === 'daily' ? '매일' : '매주'
                    } 
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText 
                    primary="임베딩 모델" 
                    secondary={indexingSettings.embedding_model} 
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText 
                    primary="청크 크기" 
                    secondary={`${indexingSettings.chunk_size} 문자`} 
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText 
                    primary="청크 겹침" 
                    secondary={`${indexingSettings.chunk_overlap} 문자`} 
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText 
                    primary="주석 포함" 
                    secondary={indexingSettings.include_comments ? '포함' : '미포함'} 
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText 
                    primary="최대 파일 수" 
                    secondary={`인덱싱 실행당 ${indexingSettings.max_files_per_run}개 파일`} 
                  />
                </ListItem>
              </List>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>패턴 설정</Typography>
              
              <Accordion defaultExpanded sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>제외 패턴 ({indexingSettings.excluded_patterns.length})</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {indexingSettings.excluded_patterns.length > 0 ? (
                    <List dense>
                      {indexingSettings.excluded_patterns.map((pattern, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={pattern} />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography color="text.secondary">제외 패턴이 없습니다.</Typography>
                  )}
                </AccordionDetails>
              </Accordion>
              
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>우선순위 패턴 ({indexingSettings.priority_patterns.length})</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {indexingSettings.priority_patterns.length > 0 ? (
                    <List dense>
                      {indexingSettings.priority_patterns.map((pattern, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={pattern} />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography color="text.secondary">우선순위 패턴이 없습니다.</Typography>
                  )}
                </AccordionDetails>
              </Accordion>
            </Grid>
          </Grid>
        </Paper>
      </TabPanel>
      
      {/* 인덱싱 기록 탭 */}
      <TabPanel value={activeTab} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>인덱싱 실행 기록</Typography>
          
          {indexingStatus.status.recent_runs.length > 0 ? (
            <List>
              {indexingStatus.status.recent_runs.map((run, index) => (
                <React.Fragment key={run.id}>
                  <ListItem alignItems="flex-start">
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {renderStatusIcon(run.status)}
                          <Typography sx={{ ml: 1, fontWeight: 'bold' }}>
                            {run.is_full_index ? '전체 인덱싱' : '증분 인덱싱'}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" component="span">
                            시작: {run.start_time ? new Date(run.start_time).toLocaleString() : '대기 중'}
                          </Typography>
                          <br />
                          {run.end_time && (
                            <Typography variant="body2" component="span">
                              종료: {new Date(run.end_time).toLocaleString()}
                            </Typography>
                          )}
                          <br />
                          <Typography variant="body2" component="span">
                            인덱싱된 파일: {run.files_indexed}개
                          </Typography>
                        </Box>
                      }
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Chip
                        label={
                          run.status === 'completed' ? '완료됨' :
                          run.status === 'failed' ? '실패' :
                          run.status === 'pending' ? '대기 중' :
                          '진행 중'
                        }
                        color={
                          run.status === 'completed' ? 'success' :
                          run.status === 'failed' ? 'error' :
                          run.status === 'pending' ? 'warning' :
                          'info'
                        }
                        size="small"
                      />
                    </Box>
                  </ListItem>
                  {index < indexingStatus.status.recent_runs.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          ) : (
            <Typography color="text.secondary">인덱싱 실행 기록이 없습니다.</Typography>
          )}
        </Paper>
      </TabPanel>
      
      {/* 설정 편집 다이얼로그 */}
      <Dialog
        open={editSettingsOpen}
        onClose={() => setEditSettingsOpen(false)}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>인덱싱 설정 편집</DialogTitle>
        <DialogContent>
          {editedSettings && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={editedSettings.is_enabled}
                        onChange={(e) => {
                          setEditedSettings({ ...editedSettings, is_enabled: e.target.checked });
                          setSettingsChanged(true);
                        }}
                      />
                    }
                    label="인덱싱 활성화"
                  />
                  
                  <FormControl fullWidth margin="normal">
                    <InputLabel>인덱싱 주기</InputLabel>
                    <Select
                      value={editedSettings.frequency}
                      onChange={(e) => {
                        setEditedSettings({ ...editedSettings, frequency: e.target.value });
                        setSettingsChanged(true);
                      }}
                      label="인덱싱 주기"
                    >
                      <MenuItem value="manual">수동</MenuItem>
                      <MenuItem value="on_commit">커밋 시</MenuItem>
                      <MenuItem value="hourly">매시간</MenuItem>
                      <MenuItem value="daily">매일</MenuItem>
                      <MenuItem value="weekly">매주</MenuItem>
                    </Select>
                  </FormControl>
                  
                  <TextField
                    fullWidth
                    label="임베딩 모델"
                    value={editedSettings.embedding_model}
                    onChange={(e) => {
                      setEditedSettings({ ...editedSettings, embedding_model: e.target.value });
                      setSettingsChanged(true);
                    }}
                    margin="normal"
                  />
                  
                  <TextField
                    fullWidth
                    label="청크 크기"
                    type="number"
                    value={editedSettings.chunk_size}
                    onChange={(e) => {
                      setEditedSettings({ 
                        ...editedSettings, 
                        chunk_size: parseInt(e.target.value) || 0 
                      });
                      setSettingsChanged(true);
                    }}
                    margin="normal"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">문자</InputAdornment>,
                    }}
                  />
                  
                  <TextField
                    fullWidth
                    label="청크 겹침"
                    type="number"
                    value={editedSettings.chunk_overlap}
                    onChange={(e) => {
                      setEditedSettings({ 
                        ...editedSettings, 
                        chunk_overlap: parseInt(e.target.value) || 0 
                      });
                      setSettingsChanged(true);
                    }}
                    margin="normal"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">문자</InputAdornment>,
                    }}
                  />
                  
                  <TextField
                    fullWidth
                    label="최대 파일 수"
                    type="number"
                    value={editedSettings.max_files_per_run}
                    onChange={(e) => {
                      setEditedSettings({ 
                        ...editedSettings, 
                        max_files_per_run: parseInt(e.target.value) || 0 
                      });
                      setSettingsChanged(true);
                    }}
                    margin="normal"
                    helperText="인덱싱 실행당 최대 처리 파일 수"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={editedSettings.include_comments}
                        onChange={(e) => {
                          setEditedSettings({ ...editedSettings, include_comments: e.target.checked });
                          setSettingsChanged(true);
                        }}
                      />
                    }
                    label="주석 포함"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Box sx={{ mb: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>패턴 유형</InputLabel>
                      <Select
                        value={patternType}
                        onChange={(e) => setPatternType(e.target.value)}
                        label="패턴 유형"
                      >
                        <MenuItem value="exclude">제외 패턴</MenuItem>
                        <MenuItem value="priority">우선순위 패턴</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                  
                  <Box sx={{ display: 'flex', mb: 2 }}>
                    <TextField
                      fullWidth
                      label={patternType === 'exclude' ? '제외할 파일 패턴' : '우선순위 파일 패턴'}
                      value={currentPattern}
                      onChange={(e) => setCurrentPattern(e.target.value)}
                      placeholder={patternType === 'exclude' ? '예: *.log, node_modules/*' : '예: src/*.py, main.py'}
                      sx={{ mr: 1 }}
                    />
                    <Button
                      variant="outlined"
                      onClick={handleAddPattern}
                      disabled={!currentPattern.trim()}
                    >
                      추가
                    </Button>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      {patternType === 'exclude' ? '제외 패턴' : '우선순위 패턴'}
                    </Typography>
                    
                    <Paper variant="outlined" sx={{ p: 1, maxHeight: '300px', overflow: 'auto' }}>
                      {patternType === 'exclude' ? (
                        editedSettings.excluded_patterns.length > 0 ? (
                          <List dense disablePadding>
                            {editedSettings.excluded_patterns.map((pattern, index) => (
                              <ListItem key={index} dense>
                                <ListItemText primary={pattern} />
                                <IconButton
                                  edge="end"
                                  size="small"
                                  onClick={() => handleDeletePattern(pattern, 'exclude')}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </ListItem>
                            ))}
                          </List>
                        ) : (
                          <Typography color="text.secondary" sx={{ p: 1 }}>
                            제외 패턴이 없습니다.
                          </Typography>
                        )
                      ) : (
                        editedSettings.priority_patterns.length > 0 ? (
                          <List dense disablePadding>
                            {editedSettings.priority_patterns.map((pattern, index) => (
                              <ListItem key={index} dense>
                                <ListItemText primary={pattern} />
                                <IconButton
                                  edge="end"
                                  size="small"
                                  onClick={() => handleDeletePattern(pattern, 'priority')}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </ListItem>
                            ))}
                          </List>
                        ) : (
                          <Typography color="text.secondary" sx={{ p: 1 }}>
                            우선순위 패턴이 없습니다.
                          </Typography>
                        )
                      )}
                    </Paper>
                  </Box>
                  
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>패턴 사용 예시</Typography>
                    <List dense>
                      <ListItem dense>
                        <ListItemText 
                          primary="*.log" 
                          secondary="모든 로그 파일 제외" 
                        />
                      </ListItem>
                      <ListItem dense>
                        <ListItemText 
                          primary="node_modules/*" 
                          secondary="node_modules 디렉토리 내 모든 파일 제외" 
                        />
                      </ListItem>
                      <ListItem dense>
                        <ListItemText 
                          primary="src/*.py" 
                          secondary="src 디렉토리의 모든 Python 파일 우선순위 지정" 
                        />
                      </ListItem>
                    </List>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditSettingsOpen(false)}>취소</Button>
          <Button
            onClick={handleSaveSettings}
            variant="contained"
            color="primary"
            disabled={!settingsChanged}
          >
            설정 저장
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CodebaseIndexing;import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  LinearProgress,
  Tab,
  Tabs
} from '@mui/material';

import {
  Search as SearchIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayArrowIcon,
  Storage as StorageIcon,
  CleaningServices as CleaningServicesIcon,
  History as HistoryIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  BarChart as BarChartIcon
} from '@mui/icons-material';

import api from '../../utils/api';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`indexing-tabpanel-${index}`}
      aria-labelledby={`indexing-tab-${index}`}
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

const CodebaseIndexing = ({ codebaseId }) => {
  const [activeTab, setActiveTab] = useState(0);
  
  // 인덱싱 상태 관리
  const [indexingStatus, setIndexingStatus] = useState(null);
  const [indexingSettings, setIndexingSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // 설정 편집 상태
  const [editSettingsOpen, setEditSettingsOpen] = useState(false);
  const [editedSettings, setEditedSettings] = useState(null);
  
// 패턴 관리
const [currentPattern, setCurrentPattern] = useState('');
const [patternType, setPatternType] = useState('exclude'); // 'exclude' 또는 'priority'

// 검색 상태
const [searchQuery, setSearchQuery] = useState('');
const [searchResults, setSearchResults] = useState([]);
const [searching, setSearching] = useState(false);

// 모달 상태
const [settingsChanged, setSettingsChanged] = useState(false);

// 초기 데이터 로드
useEffect(() => {
  if (codebaseId) {
    loadIndexingStatus();
  }
}, [codebaseId]);

// 인덱싱 상태 로드
const loadIndexingStatus = async () => {
  try {
    setLoading(true);
    setError(null);
    
    const response = await api.get(`/codebases/${codebaseId}/indexing/status`);
    setIndexingStatus(response.data);
    setIndexingSettings(response.data.settings);
    
    // 5초마다 상태 업데이트 (인덱싱 중일 때)
    if (response.data.status.is_indexing_now) {
      setTimeout(loadIndexingStatus, 5000);
    }
    
  } catch (err) {
    console.error('인덱싱 상태 로딩 오류:', err);
    setError('인덱싱 상태를 불러오는 중 오류가 발생했습니다.');
  } finally {
    setLoading(false);
  }
};

// 인덱싱 트리거
const handleTriggerIndexing = async (isFullIndex = false) => {
  try {
    setLoading(true);
    
    await api.post(`/codebases/${codebaseId}/indexing/trigger`, {
      codebase_id: codebaseId,
      is_full_index: isFullIndex
    });
    
    // 상태 새로고침
    await loadIndexingStatus();
    
  } catch (err) {
    console.error('인덱싱 트리거 오류:', err);
    setError('인덱싱을 시작하는 중 오류가 발생했습니다.');
  } finally {
    setLoading(false);
  }
};

// 인덱싱 설정 저장
const handleSaveSettings = async () => {
  try {
    setLoading(true);
    
    // 변경된 설정만 전송
    const changedSettings = {};
    for (const key in editedSettings) {
      if (JSON.stringify(editedSettings[key]) !== JSON.stringify(indexingSettings[key])) {
        changedSettings[key] = editedSettings[key];
      }
    }
    
    await api.patch(`/codebases/${codebaseId}/indexing/settings`, changedSettings);
    
    // 상태 새로고침
    await loadIndexingStatus();
    
    // 모달 닫기
    setEditSettingsOpen(false);
    setSettingsChanged(false);
    
  } catch (err) {
    console.error('설정 저장 오류:', err);
    setError('설정을 저장하는 중 오류가 발생했습니다.');
  } finally {
    setLoading(false);
  }
};

// 패턴 추가
const handleAddPattern = () => {
  if (!currentPattern.trim()) return;
  
  const newSettings = { ...editedSettings };
  const patternList = patternType === 'exclude' ? 'excluded_patterns' : 'priority_patterns';
  
  if (!newSettings[patternList].includes(currentPattern)) {
    newSettings[patternList] = [...newSettings[patternList], currentPattern];
    setEditedSettings(newSettings);
    setCurrentPattern('');
    setSettingsChanged(true);
  }
};

// 패턴 삭제
const handleDeletePattern = (pattern, type) => {
  const newSettings = { ...editedSettings };
  const patternList = type === 'exclude' ? 'excluded_patterns' : 'priority_patterns';
  
  newSettings[patternList] = newSettings[patternList].filter(p => p !== pattern);
  setEditedSettings(newSettings);
  setSettingsChanged(true);
};

// 임베딩 정리
const handleCleanupEmbeddings = async () => {
  try {
    setLoading(true);
    
    await api.post(`/codebases/${codebaseId}/indexing/cleanup`);
    
    // 상태 새로고침
    await loadIndexingStatus();
    
  } catch (err) {
    console.error('임베딩 정리 오류:', err);
    setError('임베딩 정리 중 오류가 발생했습니다.');
  } finally {
    setLoading(false);
  }
};

// 코드 검색
const handleSearchCode = async () => {
  if (!searchQuery.trim()) return;
  
  try {
    setSearching(true);
    
    const response = await api.post(`/codebases/${codebaseId}/indexing/search`, {
      codebase_id: codebaseId,
      query: searchQuery,
      limit: 10,
      threshold: 0.5
    });
    
    setSearchResults(response.data.results);
    
  } catch (err) {
    console.error('코드 검색 오류:', err);
    setError('코드 검색 중 오류가 발생했습니다.');
  } finally {
    setSearching(false);
  }
};

// 설정 편집 모달 열기
const handleOpenSettingsModal = () => {
  setEditedSettings({ ...indexingSettings });
  setEditSettingsOpen(true);
  setSettingsChanged(false);
};

// 탭 변경 핸들러
const handleTabChange = (event, newValue) => {
  setActiveTab(newValue);
};

// 상태 표시기 렌더링
const renderStatusIcon = (status) => {
  switch (status) {
    case 'completed':
      return <CheckIcon color="success" />;
    case 'failed':
      return <ErrorIcon color="error" />;
    case 'pending':
      return <PendingIcon color="warning" />;
    case 'in_progress':
      return <CircularProgress size={20} />;
    default:
      return null;
  }
};

// 로딩 중
if (loading && !indexingStatus) {
  return (
    <Box sx={{ p: 3, textAlign: 'center' }}>
      <CircularProgress />
      <Typography sx={{ mt: 2 }}>인덱싱 데이터를 불러오는 중...</Typography>
    </Box>
  );
}

// 오류 상태
if (error && !indexingStatus) {
  return (
    <Box sx={{ p: 3 }}>
      <Alert severity="error">{error}</Alert>
      <Button 
        variant="outlined" 
        onClick={loadIndexingStatus} 
        startIcon={<RefreshIcon />}
        sx={{ mt: 2 }}
      >
        다시 시도
      </Button>
    </Box>
  );
}

// 데이터 없음
if (!indexingStatus) {
  return (
    <Box sx={{ p: 3 }}>
      <Alert severity="info">인덱싱 데이터가 없습니다.</Alert>
    </Box>
  );
}

return (
  <Box sx={{ width: '100%' }}>
    {/* 상단 요약 정보 */}
    <Box sx={{ mb: 3 }}>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="인덱싱 상태" 
              action={
                <IconButton onClick={loadIndexingStatus}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">상태</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                    {indexingStatus.status.is_indexing_now ? (
                      <>
                        <CircularProgress size={20} sx={{ mr: 1 }} />
                        <Typography>인덱싱 진행 중</Typography>
                      </>
                    ) : (
                      <Typography>대기 중</Typography>
                    )}
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">인덱싱 활성화</Typography>
                  <Typography>
                    {indexingSettings.is_enabled ? '활성화됨' : '비활성화됨'}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">임베딩 모델</Typography>
                  <Typography>{indexingSettings.embedding_model}</Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">인덱싱 주기</Typography>
                  <Typography>
                    {indexingSettings.frequency === 'manual' ? '수동' : 
                     indexingSettings.frequency === 'on_commit' ? '커밋 시' :
                     indexingSettings.frequency === 'hourly' ? '매시간' :
                     indexingSettings.frequency === 'daily' ? '매일' : '매주'}
                  </Typography>
                </Grid>
              </Grid>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="body2" color="text.secondary" gutterBottom>통계</Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Typography variant="body2">임베딩 수</Typography>
                  <Typography variant="h6">{indexingStatus.statistics.total_embeddings}</Typography>
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="body2">인덱싱된 파일</Typography>
                  <Typography variant="h6">{indexingStatus.statistics.indexed_files}</Typography>
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="body2">마지막 인덱싱</Typography>
                  <Typography variant="body2">
                    {indexingStatus.statistics.last_indexed_at ? 
                      new Date(indexingStatus.statistics.last_indexed_at).toLocaleString() : 
                      '없음'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="인덱싱 작업" 
              action={
                <IconButton onClick={handleOpenSettingsModal}>
                  <SettingsIcon />
                </IconButton>
              }
            />
            <CardContent>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  인덱싱 실행
                </Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<PlayArrowIcon />}
                    onClick={() => handleTriggerIndexing(false)}
                    disabled={indexingStatus.status.is_indexing_now || !indexingSettings.is_enabled}
                  >
                    증분 인덱싱 시작
                  </Button>
                  
                  <Button
                    variant="outlined"
                    startIcon={<PlayArrowIcon />}
                    onClick={() => handleTriggerIndexing(true)}
                    disabled={indexingStatus.status.is_indexing_now || !indexingSettings.is_enabled}
                  >
                    전체 인덱싱 시작
                  </Button>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                최근 인덱싱 실행
              </Typography>
              
              {indexingStatus.status.last_run.id ? (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    {renderStatusIcon(indexingStatus.status.last_run.status)}
                    <Typography sx={{ ml: 1 }}>
                      {indexingStatus.status.last_run.status === 'completed' ? '완료됨' :
                       indexingStatus.status.last_run.status === 'failed' ? '실패' :
                       indexingStatus.status.last_run.status === 'pending' ? '대기 중' :
                       '진행 중'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <Typography variant="body2">
                      시작: {indexingStatus.status.last_run.start_time ? 
                        new Date(indexingStatus.status.last_run.start_time).toLocaleString() : 
                        '대기 중'}
                    </Typography>
                    {indexingStatus.status.last_run.end_time && (
                      <Typography variant="body2">
                        종료: {new Date(indexingStatus.status.last_run.end_time).toLocaleString()}
                      </Typography>
                    )}
                    <Typography variant="body2">
                      처리된 파일: {indexingStatus.status.last_run.files_processed}
                    </Typography>
                    <Typography variant="body2">
                      인덱싱된 파일: {indexingStatus.status.last_run.files_indexed}
                    </Typography>
                  </Box>
                  
                  {indexingStatus.status.last_run.error_message && (
                    <Alert severity="error" sx={{ mt: 1 }}>
                      {indexingStatus.status.last_run.error_message}
                    </Alert>
                  )}
                </Box>
              ) : (
                <Typography>인덱싱 실행 내역이 없습니다.</Typography>
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  startIcon={<CleaningServicesIcon />}
                  onClick={handleCleanupEmbeddings}
                  disabled={indexingStatus.status.is_indexing_now}
                >
                  임베딩 정리
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
    
    {/* 탭 내비게이션 */}
    <Box sx={{ width: '100%', mb: 3 }}>
      <Paper>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab icon={<SearchIcon />} label="코드 검색" />
          <Tab icon={<StorageIcon />} label="인덱싱 설정" />
          <Tab icon={<HistoryIcon />} label="인덱싱 기록" />
        </Tabs>
      </Paper>
    </Box>
    
    {/* 코드 검색 탭 */}
    <TabPanel value={activeTab} index={0}>
      <Box>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>코드 검색</Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TextField
              fullWidth
              label="코드 검색어 입력"
              variant="outlined"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearchCode()}
              sx={{ mr: 2 }}
            />
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleSearchCode}
              disabled={!searchQuery.trim() || searching}
            >
              {searching ? <CircularProgress size={24} /> : '검색'}
            </Button>
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            키워드로 코드를 검색하거나, 자연어 질문을 통해 코드베이스를 탐색할 수 있습니다.
          </Typography>
          
          <Box>
            <Chip label="예시: 파일 저장 함수" onClick={() => setSearchQuery('파일 저장 함수')} sx={{ m: 0.5 }} />
            <Chip label="예시: 데이터베이스 연결" onClick={() => setSearchQuery('데이터베이스 연결')} sx={{ m: 0.5 }} />
            <Chip label="예시: 인증 관련 코드" onClick={() => setSearchQuery('인증 관련 코드')} sx={{ m: 0.5 }} />
          </Box>
        </Paper>
        
        {/* 검색 결과 */}
        {searchResults.length > 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>검색 결과 ({searchResults.length})</Typography>
            
            {searchResults.map((result, index) => (
              <Accordion key={index} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography fontWeight="bold">
                        {result.file_path}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        유사도: {Math.round(result.similarity_score * 100)}%
                      </Typography>
                    </Box>
                    <Chip 
                      size="small" 
                      label={result.metadata?.language || '기타'} 
                      sx={{ ml: 1 }}
                    />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box
                    component="pre"
                    sx={{
                      fontFamily: 'monospace',
                      p: 2,
                      bgcolor: '#f5f5f5',
                      borderRadius: 1,
                      overflow: 'auto'
                    }}
                  >
                    {result.content}
                  </Box>
                  
                  {result.metadata?.code_elements && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>코드 요소</Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {result.metadata.code_elements.classes?.map((cls, i) => (
                          <Chip key={`class-${i}`} label={`클래스: ${cls}`} size="small" color="primary" variant="outlined" />
                        ))}
                        {result.metadata.code_elements.functions?.map((func, i) => (
                          <Chip key={`func-${i}`} label={`함수: ${func}`} size="small" color="secondary" variant="outlined" />
                        ))}
                      </Box>
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            ))}
          </Paper>
        )}
        
        {searchQuery && searchResults.length === 0 && !searching && (
          <Alert severity="info">
            검색 결과가 없습니다. 다른 키워드로 검색해보세요.
          </Alert>
        )}
      </Box>
    </TabPanel>
    
    {/* 인덱싱 설정 탭 */}
    <TabPanel value={activeTab} index={1}>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">인덱싱 설정</Typography>
          <Button
            variant="contained"
            startIcon={<SettingsIcon />}
            onClick={handleOpenSettingsModal}
          >
            설정 편집
          </Button>
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>기본 설정</Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="인덱싱 활성화" 
                  secondary={indexingSettings.is_enabled ? '활성화됨' : '비활성화됨'} 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="인덱싱 주기" 
                  secondary={
                    indexingSettings.frequency === 'manual' ? '수동' : 
                    indexingSettings.frequency === 'on_commit' ? '커밋 시' :
                    indexingSettings.frequency === 'hourly' ? '매시간' :
                    indexingSettings.frequency === 'daily' ? '매일' : '매주'
                  } 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="임베딩 모델" 
                  secondary={indexingSettings.embedding_model} 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="청크 크기" 
                  secondary={`${indexingSettings.chunk_size} 문자`} 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="청크 겹침" 
                  secondary={`${indexingSettings.chunk_overlap} 문자`} 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="주석 포함" 
                  secondary={indexingSettings.include_comments ? '포함' : '미포함'} 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="최대 파일 수" 
                  secondary={`인덱싱 실행당 ${indexingSettings.max_files_per_run}개 파일`} 
                />
              </ListItem>
            </List>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>패턴 설정</Typography>
            
            <Accordion defaultExpanded sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>제외 패턴 ({indexingSettings.excluded_patterns.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {indexingSettings.excluded_patterns.length > 0 ? (
                  <List dense>
                    {indexingSettings.excluded_patterns.map((pattern, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={pattern} />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography color="text.secondary">제외 패턴이 없습니다.</Typography>
                )}
              </AccordionDetails>
            </Accordion>
            
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>우선순위 패턴 ({indexingSettings.priority_patterns.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {indexingSettings.priority_patterns.length > 0 ? (
                  <List dense>
                    {indexingSettings.priority_patterns.map((pattern, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={pattern} />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography color="text.secondary">우선순위 패턴이 없습니다.</Typography>
                )}
              </AccordionDetails>
            </Accordion>
          </Grid>
        </Grid>
      </Paper>
    </TabPanel>
    
    {/* 인덱싱 기록 탭 */}
    <TabPanel value={activeTab} index={2}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>인덱싱 실행 기록</Typography>
        
        {indexingStatus.status.recent_runs.length > 0 ? (
          <List>
            {indexingStatus.status.recent_runs.map((run, index) => (
              <React.Fragment key={run.id}>
                <ListItem alignItems="flex-start">
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {renderStatusIcon(run.status)}
                        <Typography sx={{ ml: 1, fontWeight: 'bold' }}>
                          {run.is_full_index ? '전체 인덱싱' : '증분 인덱싱'}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" component="span">
                          시작: {run.start_time ? new Date(run.start_time).toLocaleString() : '대기 중'}
                        </Typography>
                        <br />
                        {run.end_time && (
                          <Typography variant="body2" component="span">
                            종료: {new Date(run.end_time).toLocaleString()}
                          </Typography>
                        )}
                        <br />
                        <Typography variant="body2" component="span">
                          인덱싱된 파일: {run.files_indexed}개
                        </Typography>
                      </Box>
                    }
                  />
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Chip
                      label={
                        run.status === 'completed' ? '완료됨' :
                        run.status === 'failed' ? '실패' :
                        run.status === 'pending' ? '대기 중' :
                        '진행 중'
                      }
                      color={
                        run.status === 'completed' ? 'success' :
                        run.status === 'failed' ? 'error' :
                        run.status === 'pending' ? 'warning' :
                        'info'
                      }
                      size="small"
                    />
                  </Box>
                </ListItem>
                {index < indexingStatus.status.recent_runs.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Typography color="text.secondary">인덱싱 실행 기록이 없습니다.</Typography>
        )}
      </Paper>
    </TabPanel>
    
    {/* 설정 편집 다이얼로그 */}
    <Dialog
      open={editSettingsOpen}
      onClose={() => setEditSettingsOpen(false)}
      fullWidth
      maxWidth="md"
    >
      <DialogTitle>인덱싱 설정 편집</DialogTitle>
      <DialogContent>
        {editedSettings && (
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={editedSettings.is_enabled}
                      onChange={(e) => {
                        setEditedSettings({ ...editedSettings, is_enabled: e.target.checked });
                        setSettingsChanged(true);
                      }}
                    />
                  }
                  label="인덱싱 활성화"
                />
                
                <FormControl fullWidth margin="normal">
                  <InputLabel>인덱싱 주기</InputLabel>
                  <Select
                    value={editedSettings.frequency}
                    onChange={(e) => {
                      setEditedSettings({ ...editedSettings, frequency: e.target.value });
                      setSettingsChanged(true);
                    }}
                    label="인덱싱 주기"
                  >
                    <MenuItem value="manual">수동</MenuItem>
                    <MenuItem value="on_commit">커밋 시</MenuItem>
                    <MenuItem value="hourly">매시간</MenuItem>
                    <MenuItem value="daily">매일</MenuItem>
                    <MenuItem value="weekly">매주</MenuItem>
                  </Select>
                </FormControl>
                
                <TextField
                  fullWidth
                  label="임베딩 모델"
                  value={editedSettings.embedding_model}
                  onChange={(e) => {
                    setEditedSettings({ ...editedSettings, embedding_model: e.target.value });
                    setSettingsChanged(true);
                  }}
                  margin="normal"
                />
                
                <TextField
                  fullWidth
                  label="청크 크기"
                  type="number"
                  value={editedSettings.chunk_size}
                  onChange={(e) => {
                    setEditedSettings({ 
                      ...editedSettings, 
                      chunk_size: parseInt(e.target.value) || 0 
                    });
                    setSettingsChanged(true);
                  }}
                  margin="normal"
                  InputProps={{
                    endAdornment: <InputAdornment position="end">문자</InputAdornment>,
                  }}
                />
                
                <TextField
                  fullWidth
                  label="청크 겹침"
                  type="number"
                  value={editedSettings.chunk_overlap}
                  onChange={(e) => {
                    setEditedSettings({ 
                      ...editedSettings, 
                      chunk_overlap: parseInt(e.target.value) || 0 
                    });
                    setSettingsChanged(true);
                  }}
                  margin="normal"
                  InputProps={{
                    endAdornment: <InputAdornment position="end">문자</InputAdornment>,
                  }}
                />
                
                <TextField
                  fullWidth
                  label="최대 파일 수"
                  type="number"
                  value={editedSettings.max_files_per_run}
                  onChange={(e) => {
                    setEditedSettings({ 
                      ...editedSettings, 
                      max_files_per_run: parseInt(e.target.value) || 0 
                    });
                    setSettingsChanged(true);
                  }}
                  margin="normal"
                  helperText="인덱싱 실행당 최대 처리 파일 수"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={editedSettings.include_comments}
                      onChange={(e) => {
                        setEditedSettings({ ...editedSettings, include_comments: e.target.checked });
                        setSettingsChanged(true);
                      }}
                    />
                  }
                  label="주석 포함"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <FormControl fullWidth>
                    <InputLabel>패턴 유형</InputLabel>
                    <Select
                      value={patternType}
                      onChange={(e) => setPatternType(e.target.value)}
                      label="패턴 유형"
                    >
                      <MenuItem value="exclude">제외 패턴</MenuItem>
                      <MenuItem value="priority">우선순위 패턴</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
                
                <Box sx={{ display: 'flex', mb: 2 }}>
                  <TextField
                    fullWidth
                    label={patternType === 'exclude' ? '제외할 파일 패턴' : '우선순위 파일 패턴'}
                    value={currentPattern}
                    onChange={(e) => setCurrentPattern(e.target.value)}
                    placeholder={patternType === 'exclude' ? '예: *.log, node_modules/*' : '예: src/*.py, main.py'}
                    sx={{ mr: 1 }}
                  />
                  <Button
                    variant="outlined"
                    onClick={handleAddPattern}
                    disabled={!currentPattern.trim()}
                  >
                    추가
                  </Button>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {patternType === 'exclude' ? '제외 패턴' : '우선순위 패턴'}
                  </Typography>
                  
                  <Paper variant="outlined" sx={{ p: 1, maxHeight: '300px', overflow: 'auto' }}>
                    {patternType === 'exclude' ? (
                      editedSettings.excluded_patterns.length > 0 ? (
                        <List dense disablePadding>
                          {editedSettings.excluded_patterns.map((pattern, index) => (
                            <ListItem key={index} dense>
                              <ListItemText primary={pattern} />
                              <IconButton
                                edge="end"
                                size="small"
                                onClick={() => handleDeletePattern(pattern, 'exclude')}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </ListItem>
                          ))}
                        </List>
                      ) : (
                        <Typography color="text.secondary" sx={{ p: 1 }}>
                          제외 패턴이 없습니다.
                        </Typography>
                      )
                    ) : (
                      editedSettings.priority_patterns.length > 0 ? (
                        <List dense disablePadding>
                          {editedSettings.priority_patterns.map((pattern, index) => (
                            <ListItem key={index} dense>
                              <ListItemText primary={pattern} />
                              <IconButton
                                edge="end"
                                size="small"
                                onClick={() => handleDeletePattern(pattern, 'priority')}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </ListItem>
                          ))}
                        </List>
                      ) : (
                        <Typography color="text.secondary" sx={{ p: 1 }}>
                          우선순위 패턴이 없습니다.
                        </Typography>
                      )
                    )}
                  </Paper>
                </Box>
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>패턴 사용 예시</Typography>
                  <List dense>
                    <ListItem dense>
                      <ListItemText 
                        primary="*.log" 
                        secondary="모든 로그 파일 제외" 
                      />
                    </ListItem>
                    <ListItem dense>
                      <ListItemText 
                        primary="node_modules/*" 
                        secondary="node_modules 디렉토리 내 모든 파일 제외" 
                      />
                    </ListItem>
                    <ListItem dense>
                      <ListItemText 
                        primary="src/*.py" 
                        secondary="src 디렉토리의 모든 Python 파일 우선순위 지정" 
                      />
                    </ListItem>
                  </List>
                </Box>
              </Grid>
            </Grid>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setEditSettingsOpen(false)}>취소</Button>
        <Button
          onClick={handleSaveSettings}
          variant="contained"
          color="primary"
          disabled={!settingsChanged}
        >
          설정 저장
        </Button>
      </DialogActions>
    </Dialog>
  </Box>
);
};