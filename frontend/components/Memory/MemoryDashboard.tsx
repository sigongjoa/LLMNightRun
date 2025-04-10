import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Tabs,
  Tab,
  Divider,
  Button,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  Avatar,
  CircularProgress,
  useTheme
} from '@mui/material';
import {
  Memory as MemoryIcon,
  DataUsage as DataUsageIcon,
  Storage as StorageIcon,
  BubbleChart as BubbleChartIcon
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../../utils/constants';
import MemoryList, { Memory } from './MemoryList';
import MemoryDetail from './MemoryDetail';
import CreateMemoryForm from './CreateMemoryForm';

// 탭 인터페이스
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`memory-tabpanel-${index}`}
      aria-labelledby={`memory-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const MemoryDashboard: React.FC = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [memoryCount, setMemoryCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 메모리 개수 로드
  useEffect(() => {
    loadMemoryCount();
    
    // 오류 처리를 위한 서버 상태 확인
    checkServerStatus();
  }, []);

  // 서버 상태 확인
  const checkServerStatus = async () => {
    try {
      await axios.get(`${API_BASE_URL}/memory/health`, {
        timeout: 30000 // 30초로 타임아웃 증가
      });
      setError(null);
    } catch (err) {
      console.error('메모리 시스템 상태 확인 실패:', err);
      setError('메모리 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
    }
  };

  const loadMemoryCount = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/memory/count`, {
        timeout: 30000 // 30초로 타임아웃 증가
      });
      setMemoryCount(response.data.count);
      setError(null);
    } catch (err) {
      console.error('메모리 개수 로드 실패:', err);
      setError('메모리 정보를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 탭 변경 처리
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 메모리 선택 처리
  const handleSelectMemory = (memory: Memory) => {
    setSelectedMemory(memory);
    // 모바일에서는 선택 시 상세 탭으로 이동
    if (window.innerWidth < 960) {
      setTabValue(1);
    }
  };

  // 메모리 생성 후 새로고침
  const handleMemoryCreated = () => {
    loadMemoryCount();
    setSelectedMemory(null); // 선택 초기화
  };

  // 대시보드 통계 카드 렌더링
  const renderStatCards = () => {
    return (
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ 
              display: 'flex', 
              alignItems: 'center',
              paddingBottom: '16px !important' 
            }}>
              <Avatar
                sx={{
                  bgcolor: theme.palette.primary.main,
                  width: 56,
                  height: 56,
                  mr: 2
                }}
              >
                <MemoryIcon fontSize="large" />
              </Avatar>
              <Box>
                <Typography variant="h5" component="div">
                  {loading ? <CircularProgress size={24} /> : memoryCount}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  총 메모리 수
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ 
              display: 'flex', 
              alignItems: 'center',
              paddingBottom: '16px !important' 
            }}>
              <Avatar
                sx={{
                  bgcolor: theme.palette.secondary.main,
                  width: 56,
                  height: 56,
                  mr: 2
                }}
              >
                <StorageIcon fontSize="large" />
              </Avatar>
              <Box>
                <Typography variant="h6" component="div">
                  FAISS
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Vector DB 엔진
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ 
              display: 'flex', 
              alignItems: 'center',
              paddingBottom: '16px !important' 
            }}>
              <Avatar
                sx={{
                  bgcolor: theme.palette.info.main,
                  width: 56,
                  height: 56,
                  mr: 2
                }}
              >
                <BubbleChartIcon fontSize="large" />
              </Avatar>
              <Box>
                <Typography variant="h6" component="div">
                  MiniLM-L6-v2
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  임베딩 모델
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        LLM 메모리 관리
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        LLM이 과거 대화, 실험, 코드와 같은 정보를 기억하고 참조할 수 있도록 Vector DB를 통한 메모리를 관리합니다.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* 대시보드 통계 카드 */}
      {renderStatCards()}

      {/* 모바일용 탭 인터페이스 */}
      <Box sx={{ display: { xs: 'block', md: 'none' } }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ mb: 2 }}
        >
          <Tab label="메모리 목록" />
          <Tab label="메모리 상세" />
          <Tab label="새 메모리" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <MemoryList 
            onSelectMemory={handleSelectMemory}
            selectedMemoryId={selectedMemory?.id}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <MemoryDetail 
            memory={selectedMemory}
            onRefresh={loadMemoryCount}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <CreateMemoryForm onMemoryCreated={handleMemoryCreated} />
        </TabPanel>
      </Box>

      {/* 데스크탑용 그리드 레이아웃 */}
      <Box sx={{ display: { xs: 'none', md: 'block' } }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <MemoryList 
              onSelectMemory={handleSelectMemory}
              selectedMemoryId={selectedMemory?.id}
            />
          </Grid>
          <Grid item xs={12} md={8}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <MemoryDetail 
                  memory={selectedMemory}
                  onRefresh={loadMemoryCount}
                />
              </Grid>
              <Grid item xs={12}>
                <CreateMemoryForm onMemoryCreated={handleMemoryCreated} />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default MemoryDashboard;