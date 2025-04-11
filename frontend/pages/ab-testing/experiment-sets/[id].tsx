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
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import Layout from '../../../components/Layout';
import { useRouter } from 'next/router';
import { useApi } from '../../../src/hooks/useApi';

// DO NOT CHANGE CODE: 이 코드는 AB 테스트 실험 세트 상세 페이지의 기본 구조입니다.
// TEMP: 임시 구현 코드입니다. 데이터 연동 및 오류 처리 개선 예정입니다.
const ExperimentSetDetailPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const api = useApi();
  const [isLoading, setIsLoading] = useState(true);
  const [experimentSet, setExperimentSet] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    if (id) {
      fetchExperimentSetData();
    }
  }, [id]);

  const fetchExperimentSetData = async () => {
    setIsLoading(true);
    try {
      const response = await api.get(`/ab-testing/experiment-sets/${id}`);
      if (response.status === 200) {
        setExperimentSet(response.data);
      }
    } catch (error) {
      console.error('실험 세트 데이터 로딩 오류:', error);
      setSnackbar({
        open: true,
        message: '실험 세트 정보를 불러오는 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunExperimentSet = async () => {
    try {
      setIsLoading(true);
      const response = await api.post(`/ab-testing/experiment-sets/${id}/run`);
      if (response.status === 200) {
        setSnackbar({
          open: true,
          message: '실험 세트가 성공적으로 실행되었습니다.',
          severity: 'success'
        });
        // 잠시 후 결과 페이지로 이동
        setTimeout(() => {
          router.push(`/ab-testing/results/${id}`);
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

  const handleGoBack = () => {
    router.push('/ab-testing');
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

  if (!experimentSet) {
    return (
      <Layout>
        <Container>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <IconButton onClick={handleGoBack} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" component="h1">
              실험 세트 상세 정보
            </Typography>
          </Box>
          <Alert severity="error">
            실험 세트를 찾을 수 없습니다. 이미 삭제되었거나 접근 권한이 없습니다.
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
              실험 세트: {experimentSet.name}
            </Typography>
          </Box>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  기본 정보
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Typography variant="body1" paragraph>
                  {experimentSet.description || '설명 없음'}
                </Typography>
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', mr: 1 }}>
                    생성일:
                  </Typography>
                  <Typography variant="body2">
                    {new Date(experimentSet.created_at).toLocaleString()}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', mr: 1 }}>
                    상태:
                  </Typography>
                  <Chip 
                    label={experimentSet.status || '대기 중'} 
                    color={
                      experimentSet.status === 'completed' ? 'success' : 
                      experimentSet.status === 'running' ? 'primary' :
                      experimentSet.status === 'failed' ? 'error' : 'default'
                    }
                    size="small"
                  />
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  비교 모델
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {experimentSet.models && experimentSet.models.length > 0 ? (
                  <List dense>
                    {experimentSet.models.map((model) => (
                      <ListItem key={model.id}>
                        <ListItemText 
                          primary={model.name} 
                          secondary={model.description} 
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    모델 정보가 없습니다.
                  </Typography>
                )}
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  비교 프롬프트
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {experimentSet.prompts && experimentSet.prompts.length > 0 ? (
                  <List dense>
                    {experimentSet.prompts.map((prompt) => (
                      <ListItem key={prompt.id}>
                        <ListItemText 
                          primary={prompt.name} 
                          secondary={prompt.description} 
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    프롬프트 정보가 없습니다.
                  </Typography>
                )}
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  평가 지표
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {experimentSet.metrics && experimentSet.metrics.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {experimentSet.metrics.map((metric) => (
                      <Chip 
                        key={metric.id}
                        label={metric.name} 
                        size="medium"
                      />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    평가 지표 정보가 없습니다.
                  </Typography>
                )}
              </Grid>

              <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Button variant="outlined" onClick={handleGoBack}>
                  목록으로
                </Button>
                <Button 
                  variant="contained" 
                  color="primary"
                  startIcon={<PlayArrowIcon />}
                  onClick={handleRunExperimentSet}
                  disabled={experimentSet.status === 'running'}
                >
                  {experimentSet.status === 'running' ? '실행 중...' : '실험 실행'}
                </Button>
              </Grid>
            </Grid>
          </Paper>

          {/* 이전 실행 결과가 있는 경우 표시 */}
          {experimentSet.previous_runs && experimentSet.previous_runs.length > 0 && (
            <Box sx={{ mt: 4 }}>
              <Typography variant="h5" gutterBottom>
                이전 실행 결과
              </Typography>
              <Grid container spacing={2}>
                {experimentSet.previous_runs.map((run) => (
                  <Grid item xs={12} md={6} key={run.id}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {new Date(run.created_at).toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          상태: {run.status}
                        </Typography>
                        <Button 
                          size="small" 
                          variant="outlined"
                          onClick={() => router.push(`/ab-testing/results/${run.id}`)}
                        >
                          결과 보기
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
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

export default ExperimentSetDetailPage;
