import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Box, 
  Paper, 
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Chip,
  InputAdornment,
  IconButton,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { LLMType, Question } from '../types';
import { askLLM, createQuestion } from '../utils/api';

const SubmitPage: React.FC = () => {
  const router = useRouter();
  
  // 상태 관리
  const [question, setQuestion] = useState<string>('');
  const [tags, setTags] = useState<string[]>([]);
  const [currentTag, setCurrentTag] = useState<string>('');
  const [selectedLLMs, setSelectedLLMs] = useState<{[key in LLMType]?: boolean}>({
    [LLMType.OPENAI_API]: true,
    [LLMType.CLAUDE_API]: true
  });
  
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  
  // 태그 추가 핸들러
  const handleAddTag = () => {
    if (currentTag.trim() && !tags.includes(currentTag.trim())) {
      setTags([...tags, currentTag.trim()]);
      setCurrentTag('');
    }
  };
  
  // 태그 삭제 핸들러
  const handleDeleteTag = (tagToDelete: string) => {
    setTags(tags.filter((tag) => tag !== tagToDelete));
  };
  
  // 엔터 키로 태그 추가
  const handleTagKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleAddTag();
    }
  };
  
  // LLM 체크박스 변경 핸들러
  const handleLLMChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedLLMs({
      ...selectedLLMs,
      [event.target.name]: event.target.checked,
    });
  };
  
  // 선택된 LLM 목록 가져오기
  const getSelectedLLMs = (): LLMType[] => {
    return Object.entries(selectedLLMs)
      .filter(([_, isSelected]) => isSelected)
      .map(([llmType]) => llmType as LLMType);
  };
  
  // 질문 제출 핸들러
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!question.trim()) {
      setError('질문을 입력해주세요.');
      return;
    }
    
    const selectedLLMTypes = getSelectedLLMs();
    if (selectedLLMTypes.length === 0) {
      setError('하나 이상의 LLM을 선택해주세요.');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // 질문 객체 생성
      const questionData: Question = {
        content: question.trim(),
        tags: tags
      };
      
      // LLM별로 질문 요청 처리
      let questionId: number | undefined;
      console.log('선택된 LLM 유형:', selectedLLMTypes);
      
      for (const llmType of selectedLLMTypes) {
        console.log(`LLM 질문 시작: ${llmType}`);
        
        if (!questionId) {
          // 첫 번째 요청에서는 질문 객체를 생성하고 ID를 저장
          const result = await askLLM(llmType, questionData);
          console.log('LLM 응답 결과:', result);
          questionId = result.question.id;
        } else {
          // 이후 요청에서는 같은 질문 ID 사용
          await askLLM(llmType, { ...questionData, id: questionId });
        }
      }
      
      setSuccess(true);
      
      // 결과 페이지로 리디렉션
      setTimeout(() => {
        router.push(`/results?questionId=${questionId}`);
      }, 1500);
      
    } catch (err: any) {
      console.error('질문 제출 오류:', err);
      setError(typeof err.detail === 'string' ? err.detail : '질문을 처리하는 중에 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          새 질문 제출
        </Typography>
        
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          {success ? (
            <Alert severity="success" sx={{ mb: 2 }}>
              질문이 성공적으로 제출되었습니다. 결과 페이지로 이동합니다...
            </Alert>
          ) : error ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          ) : null}
          
          <form onSubmit={handleSubmit}>
            <TextField
              label="질문"
              multiline
              rows={6}
              fullWidth
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              required
              placeholder="LLM에게 물어볼 질문을 입력하세요..."
              sx={{ mb: 3 }}
            />
            
            <Box sx={{ mb: 3 }}>
              <TextField
                label="태그 추가"
                size="small"
                value={currentTag}
                onChange={(e) => setCurrentTag(e.target.value)}
                onKeyPress={handleTagKeyPress}
                disabled={loading}
                placeholder="태그 입력 후 엔터"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={handleAddTag}
                        disabled={!currentTag.trim() || loading}
                        edge="end"
                      >
                        <AddIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', mt: 1, gap: 0.5 }}>
                {tags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    onDelete={() => handleDeleteTag(tag)}
                    disabled={loading}
                    size="small"
                  />
                ))}
              </Box>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <FormLabel component="legend">LLM 선택</FormLabel>
              <FormGroup row>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedLLMs[LLMType.OPENAI_API] || false}
                      onChange={handleLLMChange}
                      name={LLMType.OPENAI_API}
                      disabled={loading}
                    />
                  }
                  label="OpenAI API (GPT-4)"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedLLMs[LLMType.CLAUDE_API] || false}
                      onChange={handleLLMChange}
                      name={LLMType.CLAUDE_API}
                      disabled={loading}
                    />
                  }
                  label="Claude API"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedLLMs[LLMType.LOCAL_LLM] || false}
                      onChange={handleLLMChange}
                      name={LLMType.LOCAL_LLM}
                      disabled={loading}
                    />
                  }
                  label="로컬 LLM (LM Studio)"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedLLMs[LLMType.OPENAI_WEB] || false}
                      onChange={handleLLMChange}
                      name={LLMType.OPENAI_WEB}
                      disabled={loading}
                    />
                  }
                  label="OpenAI 웹 (ChatGPT)"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedLLMs[LLMType.CLAUDE_WEB] || false}
                      onChange={handleLLMChange}
                      name={LLMType.CLAUDE_WEB}
                      disabled={loading}
                    />
                  }
                  label="Claude 웹"
                />
              </FormGroup>
            </FormControl>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="outlined"
                onClick={() => router.back()}
                disabled={loading}
              >
                취소
              </Button>
              
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
              >
                {loading ? '처리 중...' : '질문 제출'}
              </Button>
            </Box>
          </form>
        </Paper>
      </Box>
    </Container>
  );
};

export default SubmitPage;