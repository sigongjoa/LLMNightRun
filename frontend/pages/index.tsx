import React, { useEffect, useState } from 'react';
import { Container, Grid, Typography, Card, CardContent, CardHeader, Box, Alert } from '@mui/material';
import { Question, Response } from '../types';
import StatsCard from '../components/StatsCard';
import RecentQuestions from '../components/RecentQuestions';
import SystemStatusPanel from '../components/SystemStatusPanel'; // 새 컴포넌트 추가
import { fetchQuestions, fetchResponses, getApiStatus } from '../utils/api';

const Dashboard: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [responses, setResponses] = useState<Response[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean>(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // 더미 데이터로 설정 (API 호출 대신)
        setQuestions([]);
        setResponses([]);
        console.log('대시보드: 데이터 로딩 스킵됨 (API 호출 비활성화)');
        
        setApiConnected(true);
        setError(null);
      } catch (err: any) {
        console.error('Error loading dashboard data:', err);
        setError('데이터를 불러오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // 안전하게 통계 계산
  const stats = {
    totalQuestions: questions?.length || 0,
    totalResponses: responses?.length || 0,
    uniqueLLMs: responses && Array.isArray(responses) 
      ? [...new Set(responses.map(r => r.llm_type))].length 
      : 0,
    avgResponsesPerQuestion: questions?.length 
      ? ((responses?.length || 0) / questions.length).toFixed(1) 
      : '0'
  };

  // 최근 질문 (최대 5개)
  const recentQuestions = Array.isArray(questions) 
    ? [...questions]
        .sort((a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime())
        .slice(0, 5)
    : [];

  return (
    <Container>
      <Box sx={{ my: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          LLMNightRun 대시보드
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {!apiConnected && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            백엔드 서버 연결이 원활하지 않습니다. 서버 상태를 확인해주세요.
          </Alert>
        )}

        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard 
              title="총 질문" 
              value={stats.totalQuestions} 
              loading={loading} 
              icon="QuestionAnswer" 
              color="#3f51b5"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard 
              title="총 응답" 
              value={stats.totalResponses} 
              loading={loading} 
              icon="Chat" 
              color="#4caf50"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard 
              title="사용 중인 LLM" 
              value={stats.uniqueLLMs} 
              loading={loading} 
              icon="Psychology" 
              color="#ff9800"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard 
              title="질문당 평균 응답" 
              value={stats.avgResponsesPerQuestion} 
              loading={loading} 
              icon="Analytics" 
              color="#f44336"
            />
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader title="최근 질문" />
              <CardContent>
                <RecentQuestions questions={recentQuestions} loading={loading} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <SystemStatusPanel />
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default Dashboard;