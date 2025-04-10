import React, { useEffect, useState } from 'react';
import { Container, Grid, Typography, Card, CardContent, CardHeader, Box } from '@mui/material';
import { Question, Response } from '../types';
import StatsCard from '../components/StatsCard';
import RecentQuestions from '../components/RecentQuestions';
import { fetchQuestions, fetchResponses } from '../utils/api';

const Dashboard: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [responses, setResponses] = useState<Response[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [questionsData, responsesData] = await Promise.all([
          fetchQuestions(),
          fetchResponses()
        ]);
        setQuestions(questionsData);
        setResponses(responsesData);
        setError(null);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('데이터를 불러오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // 통계 계산
  const stats = {
    totalQuestions: questions.length,
    totalResponses: responses.length,
    uniqueLLMs: [...new Set(responses.map(r => r.llm_type))].length,
    avgResponsesPerQuestion: questions.length 
      ? (responses.length / questions.length).toFixed(1) 
      : '0'
  };

  // 최근 질문 (최대 5개)
  const recentQuestions = [...questions]
    .sort((a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime())
    .slice(0, 5);

  return (
    <Container>
      <Box sx={{ my: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          LLMNightRun 대시보드
        </Typography>
        
        {error && (
          <Typography color="error" sx={{ mb: 2 }}>
            {error}
          </Typography>
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
            <Card>
              <CardHeader title="시스템 상태" />
              <CardContent>
                <Typography variant="body1" component="div" color="text.secondary" sx={{ mb: 1 }}>
                  API 상태: <span style={{ color: '#4caf50', fontWeight: 'bold' }}>정상</span>
                </Typography>
                <Typography variant="body1" component="div" color="text.secondary" sx={{ mb: 1 }}>
                  OpenAI API: <span style={{ color: '#4caf50', fontWeight: 'bold' }}>연결됨</span>
                </Typography>
                <Typography variant="body1" component="div" color="text.secondary" sx={{ mb: 1 }}>
                  Claude API: <span style={{ color: '#4caf50', fontWeight: 'bold' }}>연결됨</span>
                </Typography>
                <Typography variant="body1" component="div" color="text.secondary" sx={{ mb: 1 }}>
                  GitHub 연동: <span style={{ color: '#4caf50', fontWeight: 'bold' }}>활성화</span>
                </Typography>
                <Typography variant="body1" component="div" color="text.secondary">
                  MCP 서버: <span style={{ color: '#4caf50', fontWeight: 'bold' }}>실행 중 (2)</span>
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default Dashboard;