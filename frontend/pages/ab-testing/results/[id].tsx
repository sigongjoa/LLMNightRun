import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Button,
  CircularProgress,
  Alert,
  Snackbar,
  IconButton,
  Divider,
  Chip,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/Download';
import Layout from '../../../components/Layout';
import { useRouter } from 'next/router';
import { useApi } from '../../../src/hooks/useApi';

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
      id={`ab-testing-result-tabpanel-${index}`}
      aria-labelledby={`ab-testing-result-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

// DO NOT CHANGE CODE: 이 코드는 AB 테스트 결과 페이지의 기본 구조입니다.
// TEMP: 임시 구현 코드입니다. 실제 결과 데이터 시각화 및 추가 기능 구현 예정입니다.
const ExperimentResultsPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const api = useApi();
  const [isLoading, setIsLoading] = useState(true);
  const [experimentResults, setExperimentResults] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    if (id) {
      fetchResultsData();
    }
  }, [id]);

  const fetchResultsData = async () => {
    setIsLoading(true);
    try {
      const response = await api.get(`/ab-testing/results/${id}`);
      if (response.status === 200) {
        setExperimentResults(response.data);
      }
    } catch (error) {
      console.error('실험 결과 데이터 로딩 오류:', error);
      setSnackbar({
        open: true,
        message: '실험 결과를 불러오는 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleGoBack = () => {
    router.push(`/ab-testing/experiment-sets/${experimentResults?.experiment_set_id || ''}`);
  };

  const handleExportResults = async () => {
    try {
      const response = await api.get(`/ab-testing/results/${id}/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ab-testing-results-${id}.csv`);
      document.body.appendChild(link);
      link.click();
      
      setSnackbar({
        open: true,
        message: '결과가 성공적으로 내보내기 되었습니다.',
        severity: 'success'
      });
    } catch (error) {
      console.error('결과 내보내기 오류:', error);
      setSnackbar({
        open: true,
        message: '결과 내보내기 중 오류가 발생했습니다.',
        severity: 'error'
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

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

  if (!experimentResults) {
    return (
      <Layout>
        <Container>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <IconButton onClick={() => router.push('/ab-testing')} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" component="h1">
              실험 결과
            </Typography>
          </Box>
          <Alert severity="error">
            실험 결과를 찾을 수 없습니다. 아직 완료되지 않았거나 접근 권한이 없습니다.
          </Alert>
        </Container>
      </Layout>
    );
  }

  return (
    <Layout>
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <IconButton onClick={handleGoBack} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" component="h1">
              실험 결과: {experimentResults.experiment_set_name}
            </Typography>
          </Box>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  결과 요약
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          실행 일시
                        </Typography>
                        <Typography variant="body1">
                          {new Date(experimentResults.run_at).toLocaleString()}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          총 실험 수
                        </Typography>
                        <Typography variant="body1">
                          {experimentResults.total_experiments || 0}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          상태
                        </Typography>
                        <Chip 
                          label={experimentResults.status || '완료됨'} 
                          color={
                            experimentResults.status === 'completed' ? 'success' : 
                            experimentResults.status === 'running' ? 'primary' :
                            experimentResults.status === 'failed' ? 'error' : 'default'
                          }
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Grid>

              <Grid item xs={12}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                  <Tabs value={tabValue} onChange={handleTabChange} aria-label="experiment results tabs">
                    <Tab label="모델 비교" id="experiment-results-tab-0" />
                    <Tab label="프롬프트 비교" id="experiment-results-tab-1" />
                    <Tab label="상세 결과" id="experiment-results-tab-2" />
                  </Tabs>
                </Box>

                {/* 모델 비교 탭 */}
                <TabPanel value={tabValue} index={0}>
                  {experimentResults.model_comparison ? (
                    <TableContainer component={Paper}>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>모델</TableCell>
                            {experimentResults.model_comparison.metrics?.map((metric) => (
                              <TableCell key={metric.id}>{metric.name}</TableCell>
                            ))}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {experimentResults.model_comparison.models?.map((model) => (
                            <TableRow key={model.id}>
                              <TableCell>{model.name}</TableCell>
                              {experimentResults.model_comparison.metrics?.map((metric) => (
                                <TableCell key={`${model.id}-${metric.id}`}>
                                  {experimentResults.model_comparison.scores?.[model.id]?.[metric.id] || '-'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Alert severity="info">모델 비교 데이터가 없습니다.</Alert>
                  )}
                </TabPanel>

                {/* 프롬프트 비교 탭 */}
                <TabPanel value={tabValue} index={1}>
                  {experimentResults.prompt_comparison ? (
                    <TableContainer component={Paper}>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>프롬프트</TableCell>
                            {experimentResults.prompt_comparison.metrics?.map((metric) => (
                              <TableCell key={metric.id}>{metric.name}</TableCell>
                            ))}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {experimentResults.prompt_comparison.prompts?.map((prompt) => (
                            <TableRow key={prompt.id}>
                              <TableCell>{prompt.name}</TableCell>
                              {experimentResults.prompt_comparison.metrics?.map((metric) => (
                                <TableCell key={`${prompt.id}-${metric.id}`}>
                                  {experimentResults.prompt_comparison.scores?.[prompt.id]?.[metric.id] || '-'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Alert severity="info">프롬프트 비교 데이터가 없습니다.</Alert>
                  )}
                </TabPanel>

                {/* 상세 결과 탭 */}
                <TabPanel value={tabValue} index={2}>
                  {experimentResults.detailed_results && experimentResults.detailed_results.length > 0 ? (
                    <TableContainer component={Paper} sx={{ maxHeight: 440 }}>
                      <Table stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>실험 ID</TableCell>
                            <TableCell>모델</TableCell>
                            <TableCell>프롬프트</TableCell>
                            <TableCell>평가 지표</TableCell>
                            <TableCell>점수</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {experimentResults.detailed_results.map((result) => (
                            <TableRow key={result.id}>
                              <TableCell>{result.experiment_id}</TableCell>
                              <TableCell>{result.model_name}</TableCell>
                              <TableCell>{result.prompt_name}</TableCell>
                              <TableCell>{result.metric_name}</TableCell>
                              <TableCell>{result.score}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Alert severity="info">상세 결과 데이터가 없습니다.</Alert>
                  )}
                </TabPanel>
              </Grid>

              <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Button variant="outlined" onClick={handleGoBack}>
                  돌아가기
                </Button>
                <Button 
                  variant="contained" 
                  color="primary"
                  startIcon={<DownloadIcon />}
                  onClick={handleExportResults}
                >
                  결과 내보내기
                </Button>
              </Grid>
            </Grid>
          </Paper>
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
// END-DO-NOT-CHANGE

export default ExperimentResultsPage;
