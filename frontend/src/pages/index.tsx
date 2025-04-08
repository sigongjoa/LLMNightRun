import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Grid, 
  TextField, 
  Typography, 
  Chip,
  Divider,
  Paper,
  IconButton
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import DeleteIcon from '@mui/icons-material/Delete';
import HistoryIcon from '@mui/icons-material/History';
import Layout from '../components/layout/Layout';
import { LoadingIndicator, CodeBlock } from '../components/ui';
import { useAskLLM, useQuestions } from '../hooks';
import { LLMType, Question } from '../types';
import { useNotification } from '../contexts';

const HomePage: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [selectedLLM, setSelectedLLM] = useState<LLMType>(LLMType.OPENAI_API);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

  // 질문 목록 조회
  const { data: questions, isLoading: isLoadingQuestions } = useQuestions({ limit: 5 });
  
  // LLM 질문 요청 훅
  const { mutate: askLLM, isLoading: isAsking } = useAskLLM();
  
  // 알림 컨텍스트
  const { showNotification } = useNotification();

  // 질문 제출 처리
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!question.trim()) {
      showNotification('질문을 입력해주세요.', 'warning');
      return;
    }
    
    const questionData: Question = {
      content: question.trim(),
      tags: tags.length > 0 ? tags : undefined,
    };
    
    askLLM(
      { llmType: selectedLLM, question: questionData },
      {
        onSuccess: (data) => {
          showNotification('질문이 성공적으로 처리되었습니다.', 'success');
          setQuestion('');
          setTags([]);
        },
        onError: (error: any) => {
          showNotification(`오류 발생: ${error.detail || '알 수 없는 오류'}`, 'error');
        },
      }
    );
  };

  // 태그 추가 처리
  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  // 태그 삭제 처리
  const handleDeleteTag = (tagToDelete: string) => {
    setTags(tags.filter((tag) => tag !== tagToDelete));
  };

  // 태그 입력 키 이벤트 처리
  const handleTagKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  return (
    <Layout title="질문 & 응답">
      <Grid container spacing={3}>
        {/* 질문 양식 */}
        <Grid item xs={12} md={7}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" component="h1" gutterBottom>
              LLM에 질문하기
            </Typography>
            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="질문"
                placeholder="질문을 입력하세요..."
                multiline
                rows={4}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                margin="normal"
                variant="outlined"
                disabled={isAsking}
              />
              
              {/* 태그 입력 영역 */}
              <Box sx={{ mt: 2, mb: 1 }}>
                <Typography variant="subtitle2">태그 (선택사항)</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TextField
                    size="small"
                    placeholder="태그 추가"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={handleTagKeyDown}
                    disabled={isAsking}
                    sx={{ mr: 1 }}
                  />
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={handleAddTag}
                    disabled={!newTag.trim() || isAsking}
                  >
                    추가
                  </Button>
                </Box>
                
                {/* 태그 표시 영역 */}
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {tags.map((tag) => (
                    <Chip
                      key={tag}
                      label={tag}
                      onDelete={() => handleDeleteTag(tag)}
                      size="small"
                      disabled={isAsking}
                    />
                  ))}
                </Box>
              </Box>
              
              {/* LLM 선택 옵션 */}
              <Box sx={{ mt: 2, mb: 3 }}>
                <Typography variant="subtitle2">LLM 선택</Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Button
                    variant={selectedLLM === LLMType.OPENAI_API ? 'contained' : 'outlined'}
                    size="small"
                    onClick={() => setSelectedLLM(LLMType.OPENAI_API)}
                    disabled={isAsking}
                  >
                    OpenAI
                  </Button>
                  <Button
                    variant={selectedLLM === LLMType.CLAUDE_API ? 'contained' : 'outlined'}
                    size="small"
                    onClick={() => setSelectedLLM(LLMType.CLAUDE_API)}
                    disabled={isAsking}
                  >
                    Claude
                  </Button>
                  <Button
                    variant={selectedLLM === LLMType.LOCAL_LLM ? 'contained' : 'outlined'}
                    size="small"
                    onClick={() => setSelectedLLM(LLMType.LOCAL_LLM)}
                    disabled={isAsking}
                  >
                    로컬 LLM
                  </Button>
                </Box>
              </Box>
              
              {/* 제출 버튼 */}
              <Button
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                endIcon={<SendIcon />}
                disabled={isAsking || !question.trim()}
                fullWidth
              >
                {isAsking ? '처리 중...' : '질문하기'}
              </Button>
            </form>
          </Paper>
        </Grid>
        
        {/* 최근 질문 목록 */}
        <Grid item xs={12} md={5}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <HistoryIcon sx={{ mr: 1 }} />
              <Typography variant="h5" component="h2">
                최근 질문
              </Typography>
            </Box>
            
            {isLoadingQuestions ? (
              <LoadingIndicator message="질문 목록 로딩 중..." />
            ) : questions && questions.length > 0 ? (
              <Box>
                {questions.map((q) => (
                  <Card key={q.id} sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {q.content}
                      </Typography>
                      {q.tags && q.tags.length > 0 && (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                          {q.tags.map((tag) => (
                            <Chip key={tag} label={tag} size="small" variant="outlined" />
                          ))}
                        </Box>
                      )}
                      <Box
                        sx={{
                          mt: 1,
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          {q.created_at && new Date(q.created_at).toLocaleString()}
                        </Typography>
                        <IconButton size="small" color="error">
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  아직 질문 내역이 없습니다
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* 응답 영역 */}
        {isAsking && (
          <Grid item xs={12}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <LoadingIndicator message={`${selectedLLM} 응답 생성 중...`} />
            </Paper>
          </Grid>
        )}
      </Grid>
    </Layout>
  );
};

export default HomePage;
