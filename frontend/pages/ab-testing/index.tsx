import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tabs,
  Tab,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  Alert,
  Snackbar
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import CompareIcon from '@mui/icons-material/Compare';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import { useApi } from '../../src/hooks/useApi';

// 탭 패널 인터페이스
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// 탭 패널 컴포넌트
function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ab-testing-tabpanel-${index}`}
      aria-labelledby={`ab-testing-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

// A/B 테스트 페이지
const ABTestingPage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [experimentSets, setExperimentSets] = useState([]);
  const [experimentTemplates, setExperimentTemplates] = useState([]);
  const [selectedExperimentSet, setSelectedExperimentSet] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const router = useRouter();
  const api = useApi();

  // 탭 변경 핸들러
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 데이터 로드
  useEffect(() => {
    fetchData();
  }, []);

  // 데이터 가져오기
  const fetchData = async () => {
    setIsLoading(true);
    try {
      // 실험 세트 가져오기
      const experimentsResponse = await api.get('/ab-testing/experiment-sets');
      if (experimentsResponse.status === 200) {
        setExperimentSets(experimentsResponse.data);
      }

      // 템플릿 가져오기
      const templatesResponse = await api.get('/ab-testing/templates');
      if (templatesResponse.status === 200) {
        setExperimentTemplates(templatesResponse.data);
      }
    } catch (error) {
      console.error('데이터 로딩 오류:', error);
      setSnackbar({
        open: true,
        message: '데이터를 불러오는 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 실험 세트 생성 페이지로 이동
  const handleCreateExperimentSet = () => {
    router.push('/ab-testing/create');
  };

  // 템플릿 생성 페이지로 이동
  const handleCreateTemplate = () => {
    router.push('/ab-testing/templates/create');
  };

  // 실험 세트 실행
  const handleRunExperimentSet = async (setId) => {
    try {
      setIsLoading(true);
      const response = await api.post(`/ab-testing/experiment-sets/${setId}/run`);
      if (response.status === 200) {
        setSnackbar({
          open: true,
          message: '실험 세트가 성공적으로 실행되었습니다.',
          severity: 'success'
        });
        // 잠시 후 결과 페이지로 이동
        setTimeout(() => {
          router.push(`/ab-testing/results/${setId}`);
        }, 1500);
      }
    } catch (error) {
      console.error('실험 세트 실행 오류:', error);
      setSnackbar({
        open: true,
        message: '실험 세트 실행 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 실험 세트 상세 페이지로 이동
  const handleViewExperimentSet = (setId) => {
    router.push(`/ab-testing/experiment-sets/${setId}`);
  };

  // 템플릿 상세 페이지로 이동
  const handleViewTemplate = (templateId) => {
    router.push(`/ab-testing/templates/${templateId}`);
  };

  // 스낵바 닫기
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // 로딩 중 표시
  if (isLoading) {
    return (
      <Layout>
        <Container>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <CircularProgress />
          </Box>
        </Container>
      </Layout>
    );
  }

  return (
    <Layout>
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" gutterBottom component="h1">
            A/B 테스트 관리
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            LLM 모델과 프롬프트 조합의 성능을 비교 평가할 수 있는 A/B 테스트 시스템입니다.
          </Typography>

          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="ab testing tabs">
              <Tab label="실험 세트" id="ab-testing-tab-0" />
              <Tab label="템플릿" id="ab-testing-tab-1" />
            </Tabs>
          </Box>

          {/* 실험 세트 탭 */}
          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleCreateExperimentSet}
              >
                새 실험 세트 생성
              </Button>
            </Box>

            {experimentSets.length === 0 ? (
              <Alert severity="info">
                등록된 실험 세트가 없습니다. 새 실험 세트를 생성하세요.
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {experimentSets.map((set) => (
                  <Grid item xs={12} md={6} key={set.id}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {set.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {set.description || '설명 없음'}
                        </Typography>
                        <Typography variant="body2">
                          실험 수: {set.experiment_count || 0}
                        </Typography>
                        <Typography variant="body2">
                          생성 일시: {new Date(set.created_at).toLocaleString()}
                        </Typography>
                        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                          <Button
                            size="small"
                            onClick={() => handleViewExperimentSet(set.id)}
                            sx={{ mr: 1 }}
                          >
                            상세보기
                          </Button>
                          <Button
                            size="small"
                            variant="contained"
                            color="primary"
                            startIcon={<PlayArrowIcon />}
                            onClick={() => handleRunExperimentSet(set.id)}
                          >
                            실행
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </TabPanel>

          {/* 템플릿 탭 */}
          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleCreateTemplate}
              >
                새 템플릿 생성
              </Button>
            </Box>

            {experimentTemplates.length === 0 ? (
              <Alert severity="info">
                등록된 템플릿이 없습니다. 새 템플릿을 생성하세요.
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {experimentTemplates.map((template) => (
                  <Grid item xs={12} md={6} key={template.id}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {template.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {template.description || '설명 없음'}
                        </Typography>
                        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                          <Button
                            size="small"
                            onClick={() => handleViewTemplate(template.id)}
                          >
                            상세보기
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </TabPanel>
        </Box>

        {/* 스낵바 알림 */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Layout>
  );
};

export default ABTestingPage;
