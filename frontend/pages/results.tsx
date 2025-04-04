import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Grid, 
  Divider, 
  Chip, 
  Button, 
  Alert, 
  CircularProgress,
  Tab,
  Tabs,
  Card, 
  CardHeader, 
  CardContent,
  IconButton
} from '@mui/material';
import {
  Upload as UploadIcon,
  ContentCopy as CopyIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import { Question, Response, LLMType } from '../types';
import { fetchQuestion, fetchResponses, uploadToGitHub } from '../utils/api';

// LLM 유형별 아이콘 및 색상
const LLM_ICONS: Record<LLMType, { name: string; color: string }> = {
  [LLMType.OPENAI_API]: { name: 'OpenAI API', color: '#10a37f' },
  [LLMType.OPENAI_WEB]: { name: 'OpenAI 웹', color: '#10a37f' },
  [LLMType.CLAUDE_API]: { name: 'Claude API', color: '#7e57c2' },
  [LLMType.CLAUDE_WEB]: { name: 'Claude 웹', color: '#7e57c2' },
  [LLMType.MANUAL]: { name: '수동 입력', color: '#9e9e9e' },
};

const ResultsPage: React.FC = () => {
  const router = useRouter();
  const { questionId } = router.query;
  
  // 상태 관리
  const [question, setQuestion] = useState<Question | null>(null);
  const [responses, setResponses] = useState<Response[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [uploadLoading, setUploadLoading] = useState<boolean>(false);
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false);
  const [githubUrl, setGithubUrl] = useState<string | null>(null);
  
  // 데이터 로드
  useEffect(() => {
    const loadData = async () => {
      if (!questionId) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // 질문 및 응답 데이터 가져오기
        const [questionData, responsesData] = await Promise.all([
          fetchQuestion(Number(questionId)),
          fetchResponses(Number(questionId))
        ]);
        
        setQuestion(questionData);
        setResponses(responsesData);
      } catch (err: any) {
        console.error('결과 로딩 오류:', err);
        setError(err.detail || '데이터를 불러오는 중에 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    if (questionId) {
      loadData();
    }
  }, [questionId]);
  
  // 탭 변경 핸들러
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  // 텍스트 복사 함수
  const copyTextToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        alert('텍스트가 클립보드에 복사되었습니다.');
      })
      .catch(err => {
        console.error('텍스트 복사 오류:', err);
        alert('텍스트 복사 중 오류가 발생했습니다.');
      });
  };
  
  // GitHub 업로드 핸들러
  const handleGitHubUpload = async () => {
    if (!questionId) return;
    
    try {
      setUploadLoading(true);
      
      const result = await uploadToGitHub(Number(questionId));
      
      setUploadSuccess(true);
      setGithubUrl(result.url);
    } catch (err: any) {
      console.error('GitHub 업로드 오류:', err);
      setError(err.detail || 'GitHub 업로드 중 오류가 발생했습니다.');
    } finally {
      setUploadLoading(false);
    }
  };
  
  // 코드 추출 페이지로 이동
  const handleExtractCode = () => {
    if (!questionId) return;
    router.push(`/code-manager?questionId=${questionId}`);
  };
  
  // 날짜 포맷팅
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // 로딩 화면
  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ my: 4, textAlign: 'center' }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>결과를 불러오는 중...</Typography>
        </Box>
      </Container>
    );
  }
  
  // 오류 화면
  if (error) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
          <Button variant="contained" onClick={() => router.push('/')}>
            대시보드로 돌아가기
          </Button>
        </Box>
      </Container>
    );
  }
  
  // 데이터가 없는 경우
  if (!question || responses.length === 0) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Alert severity="info" sx={{ mb: 2 }}>
            질문을 찾을 수 없거나 아직 응답이 없습니다.
          </Alert>
          <Button variant="contained" onClick={() => router.push('/')}>
            대시보드로 돌아가기
          </Button>
        </Box>
      </Container>
    );
  }
  
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          LLM 응답 비교
        </Typography>
        
        {/* 질문 정보 */}
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            질문
          </Typography>
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>
            {question.content}
          </Typography>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
            <Box>
              {question.tags && question.tags.length > 0 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {question.tags.map((tag, index) => (
                    <Chip key={index} label={tag} size="small" variant="outlined" />
                  ))}
                </Box>
              )}
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                작성일: {formatDate(question.created_at)}
              </Typography>
            </Box>
            
            <Box>
              <Button
                variant="outlined"
                color="primary"
                startIcon={<CodeIcon />}
                onClick={handleExtractCode}
                sx={{ mr: 1 }}
              >
                코드 추출
              </Button>
              
              <Button
                variant="contained"
                color="primary"
                startIcon={uploadLoading ? <CircularProgress size={20} color="inherit" /> : <UploadIcon />}
                onClick={handleGitHubUpload}
                disabled={uploadLoading || uploadSuccess}
              >
                {uploadSuccess ? '업로드됨' : 'GitHub에 저장'}
              </Button>
            </Box>
          </Box>
          
          {uploadSuccess && githubUrl && (
            <Alert severity="success" sx={{ mt: 2 }}>
              GitHub에 성공적으로 업로드되었습니다.
              <Button
                size="small"
                color="inherit"
                href={githubUrl}
                target="_blank"
                sx={{ ml: 1 }}
              >
                보기
              </Button>
            </Alert>
          )}
        </Paper>
        
        {/* 응답 탭 */}
        <Box sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
            <Tabs
              value={activeTab}
              onChange={handleTabChange}
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab label="모든 응답 비교" />
              {responses.map((response, index) => (
                <Tab
                  key={response.id || index}
                  label={LLM_ICONS[response.llm_type].name}
                  iconPosition="start"
                  sx={{
                    color: LLM_ICONS[response.llm_type].color
                  }}
                />
              ))}
            </Tabs>
          </Box>
          
          {/* 모든 응답 비교 뷰 */}
          {activeTab === 0 && (
            <Grid container spacing={3}>
              {responses.map((response, index) => (
                <Grid item xs={12} md={6} lg={responses.length > 2 ? 4 : 6} key={response.id || index}>
                  <Card elevation={3}>
                    <CardHeader
                      title={LLM_ICONS[response.llm_type].name}
                      subheader={formatDate(response.created_at)}
                      sx={{
                        backgroundColor: `${LLM_ICONS[response.llm_type].color}10`,
                        '& .MuiCardHeader-title': {
                          color: LLM_ICONS[response.llm_type].color,
                          fontWeight: 'bold'
                        }
                      }}
                      action={
                        <IconButton
                          aria-label="copy"
                          onClick={() => copyTextToClipboard(response.content)}
                          size="small"
                        >
                          <CopyIcon />
                        </IconButton>
                      }
                    />
                    <CardContent>
                      <Typography
                        variant="body2"
                        sx={{
                          whiteSpace: 'pre-wrap',
                          maxHeight: '400px',
                          overflowY: 'auto'
                        }}
                      >
                        {response.content}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
          
          {/* 개별 응답 탭 */}
          {responses.map((response, index) => (
            activeTab === index + 1 && (
              <Box key={response.id || index}>
                <Card elevation={3}>
                  <CardHeader
                    title={LLM_ICONS[response.llm_type].name}
                    subheader={formatDate(response.created_at)}
                    sx={{
                      backgroundColor: `${LLM_ICONS[response.llm_type].color}10`,
                      '& .MuiCardHeader-title': {
                        color: LLM_ICONS[response.llm_type].color,
                        fontWeight: 'bold'
                      }
                    }}
                    action={
                      <IconButton
                        aria-label="copy"
                        onClick={() => copyTextToClipboard(response.content)}
                      >
                        <CopyIcon />
                      </IconButton>
                    }
                  />
                  <CardContent>
                    <Typography
                      variant="body1"
                      sx={{
                        whiteSpace: 'pre-wrap'
                      }}
                    >
                      {response.content}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            )
          ))}
        </Box>
      </Box>
    </Container>
  );
};

export default ResultsPage;