import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Grid, 
  Card, 
  CardHeader, 
  CardContent, 
  CardActions,
  Button, 
  Alert, 
  CircularProgress,
  Tab,
  Tabs,
  TextField,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  GitHub as GitHubIcon,
  ContentCopy as CopyIcon,
  Code as CodeIcon,
  Search as SearchIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { CodeSnippet, CodeLanguage, Response, Question } from '../types';
import { fetchCodeSnippets, createCodeSnippet, fetchResponses, fetchQuestion } from '../utils/api';
import ExportButton, { ExportType } from '../components/ExportButton';

// 언어별 구문 강조 및 아이콘
const LANGUAGE_INFO: Record<CodeLanguage, { color: string; icon: string; name: string }> = {
  [CodeLanguage.PYTHON]: { color: '#3776ab', icon: 'py', name: 'Python' },
  [CodeLanguage.JAVASCRIPT]: { color: '#f7df1e', icon: 'js', name: 'JavaScript' },
  [CodeLanguage.TYPESCRIPT]: { color: '#3178c6', icon: 'ts', name: 'TypeScript' },
  [CodeLanguage.JAVA]: { color: '#b07219', icon: 'java', name: 'Java' },
  [CodeLanguage.CSHARP]: { color: '#178600', icon: 'cs', name: 'C#' },
  [CodeLanguage.CPP]: { color: '#f34b7d', icon: 'cpp', name: 'C++' },
  [CodeLanguage.GO]: { color: '#00add8', icon: 'go', name: 'Go' },
  [CodeLanguage.RUST]: { color: '#dea584', icon: 'rs', name: 'Rust' },
  [CodeLanguage.PHP]: { color: '#4f5d95', icon: 'php', name: 'PHP' },
  [CodeLanguage.RUBY]: { color: '#701516', icon: 'rb', name: 'Ruby' },
  [CodeLanguage.SWIFT]: { color: '#ffac45', icon: 'swift', name: 'Swift' },
  [CodeLanguage.KOTLIN]: { color: '#a97bff', icon: 'kt', name: 'Kotlin' },
  [CodeLanguage.OTHER]: { color: '#cccccc', icon: 'txt', name: '기타' },
};

const CodeManagerPage: React.FC = () => {
  const router = useRouter();
  const { questionId, responseId } = router.query;
  
  // 상태 관리
  const [codeSnippets, setCodeSnippets] = useState<CodeSnippet[]>([]);
  const [question, setQuestion] = useState<Question | null>(null);
  const [responses, setResponses] = useState<Response[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  
  // 코드 스니펫 편집 관련 상태
  const [editDialogOpen, setEditDialogOpen] = useState<boolean>(false);
  const [currentSnippet, setCurrentSnippet] = useState<CodeSnippet | null>(null);
  const [editedTitle, setEditedTitle] = useState<string>('');
  const [editedDescription, setEditedDescription] = useState<string>('');
  const [editedContent, setEditedContent] = useState<string>('');
  const [editedLanguage, setEditedLanguage] = useState<CodeLanguage>(CodeLanguage.OTHER);
  const [editedTags, setEditedTags] = useState<string[]>([]);
  const [currentTag, setCurrentTag] = useState<string>('');
  
  // 데이터 로드
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 코드 스니펫 로드
        let snippets: CodeSnippet[] = [];
        
        if (questionId) {
          // 특정 질문과 관련된 코드 스니펫 로드
          snippets = await fetchCodeSnippets(undefined, undefined, 0, 100, Number(questionId));
          
          // 질문 정보 로드
          const questionData = await fetchQuestion(Number(questionId));
          setQuestion(questionData);
          
          // 질문에 대한 응답 로드
          const responsesData = await fetchResponses(Number(questionId));
          setResponses(responsesData);
        } else if (responseId) {
          // 특정 응답과 관련된 코드 스니펫 로드
          snippets = await fetchCodeSnippets(undefined, undefined, 0, 100, undefined, Number(responseId));
        } else {
          // 모든 코드 스니펫 로드
          snippets = await fetchCodeSnippets();
        }
        
        setCodeSnippets(snippets);
      } catch (err: any) {
        console.error('코드 스니펫 로딩 오류:', err);
        setError(err.detail || '데이터를 불러오는 중에 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [questionId, responseId]);
  
  // 검색 및 필터링된 스니펫
  const filteredSnippets = codeSnippets.filter(snippet => {
    // 검색어 필터링
    const searchMatch = 
      searchTerm === '' || 
      snippet.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (snippet.description && snippet.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
      snippet.content.toLowerCase().includes(searchTerm.toLowerCase());
    
    // 언어 필터링
    const languageMatch = selectedLanguage === '' || snippet.language === selectedLanguage;
    
    // 태그 필터링
    const tagMatch = 
      selectedTags.length === 0 || 
      selectedTags.every(tag => snippet.tags.includes(tag));
    
    return searchMatch && languageMatch && tagMatch;
  });
  
  // 스니펫 태그 추가 핸들러
  const handleAddTag = () => {
    if (currentTag.trim() && !editedTags.includes(currentTag.trim())) {
      setEditedTags([...editedTags, currentTag.trim()]);
      setCurrentTag('');
    }
  };
  
  // 스니펫 태그 삭제 핸들러
  const handleDeleteTag = (tagToDelete: string) => {
    setEditedTags(editedTags.filter(tag => tag !== tagToDelete));
  };
  
  // 태그 필터 추가
  const handleAddTagFilter = (tag: string) => {
    if (!selectedTags.includes(tag)) {
      setSelectedTags([...selectedTags, tag]);
    }
  };
  
  // 태그 필터 삭제
  const handleRemoveTagFilter = (tag: string) => {
    setSelectedTags(selectedTags.filter(t => t !== tag));
  };
  
  // 엔터 키로 태그 추가
  const handleTagKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleAddTag();
    }
  };
  
  // 스니펫 편집 다이얼로그 열기
  const handleOpenEditDialog = (snippet: CodeSnippet) => {
    setCurrentSnippet(snippet);
    setEditedTitle(snippet.title);
    setEditedDescription(snippet.description || '');
    setEditedContent(snippet.content);
    setEditedLanguage(snippet.language);
    setEditedTags([...snippet.tags]);
    setEditDialogOpen(true);
  };
  
  // 스니펫 편집 다이얼로그 닫기
  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setCurrentSnippet(null);
  };
  
  // 스니펫 저장
  const handleSaveSnippet = async () => {
    // TODO: API 연동하여 스니펫 저장 구현
    handleCloseEditDialog();
  };
  
  // 코드 복사
  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
      .then(() => {
        alert('코드가 클립보드에 복사되었습니다.');
      })
      .catch(err => {
        console.error('코드 복사 오류:', err);
        alert('코드 복사 중 오류가 발생했습니다.');
      });
  };
  
  // GitHub에 코드 저장
  const handleSaveToGitHub = (snippetId: number) => {
    // TODO: GitHub 업로드 기능 구현
    alert(`스니펫 ID ${snippetId}을(를) GitHub에 저장합니다.`);
  };
  
  // 로딩 화면
  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ my: 4, textAlign: 'center' }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>코드 스니펫을 불러오는 중...</Typography>
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
  
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            코드 관리자
          </Typography>
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
          >
            새 코드 스니펫
          </Button>
        </Box>
        
        {question && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="subtitle1">
              "{question.content.substring(0, 100)}..." 질문에 대한 코드 스니펫을 관리하고 있습니다.
            </Typography>
          </Alert>
        )}
        
        {/* 검색 및 필터링 */}
        <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="코드 검색"
                variant="outlined"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>언어 필터</InputLabel>
                <Select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  label="언어 필터"
                  startAdornment={
                    <InputAdornment position="start">
                      <FilterIcon />
                    </InputAdornment>
                  }
                >
                  <MenuItem value="">모든 언어</MenuItem>
                  {Object.entries(LANGUAGE_INFO).map(([key, value]) => (
                    <MenuItem key={key} value={key}>
                      {value.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
          
          {/* 태그 필터 */}
          {selectedTags.length > 0 && (
            <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {selectedTags.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  onDelete={() => handleRemoveTagFilter(tag)}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          )}
        </Paper>
        
        {/* 스니펫 목록 */}
        {filteredSnippets.length === 0 ? (
          <Alert severity="info">
            {searchTerm || selectedLanguage || selectedTags.length > 0 
              ? '검색 조건에 맞는 코드 스니펫이 없습니다.' 
              : '저장된 코드 스니펫이 없습니다.'}
          </Alert>
        ) : (
          <Grid container spacing={3}>
            {filteredSnippets.map((snippet) => (
              <Grid item xs={12} md={6} key={snippet.id}>
                <Card elevation={3}>
                  <CardHeader
                    title={snippet.title}
                    subheader={`${LANGUAGE_INFO[snippet.language].name} • 버전 ${snippet.version}`}
                    sx={{
                      backgroundColor: `${LANGUAGE_INFO[snippet.language].color}10`,
                      '& .MuiCardHeader-title': {
                        fontWeight: 'bold'
                      }
                    }}
                  />
                  
                  {snippet.description && (
                    <CardContent sx={{ pt: 1, pb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        {snippet.description}
                      </Typography>
                    </CardContent>
                  )}
                  
                  <CardContent>
                    <Box 
                      sx={{ 
                        bgcolor: '#f5f5f5', 
                        p: 1.5, 
                        borderRadius: 1,
                        maxHeight: '200px',
                        overflow: 'auto',
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        whiteSpace: 'pre-wrap'
                      }}
                    >
                      {snippet.content.length > 500 
                        ? `${snippet.content.substring(0, 500)}...` 
                        : snippet.content}
                    </Box>
                    
                    {snippet.tags.length > 0 && (
                      <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {snippet.tags.map((tag, index) => (
                          <Chip
                            key={index}
                            label={tag}
                            size="small"
                            variant="outlined"
                            onClick={() => handleAddTagFilter(tag)}
                          />
                        ))}
                      </Box>
                    )}
                  </CardContent>
                  
                  <CardActions sx={{ justifyContent: 'flex-end' }}>
                    <Tooltip title="코드 복사">
                      <IconButton 
                        size="small" 
                        onClick={() => handleCopyCode(snippet.content)}
                      >
                        <CopyIcon />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="GitHub에 저장">
                      <IconButton 
                        size="small"
                        onClick={() => handleSaveToGitHub(snippet.id!)}
                        color="primary"
                      >
                        <GitHubIcon />
                      </IconButton>
                    </Tooltip>

                    <ExportButton
                      type={ExportType.CODE_SNIPPET}
                      id={snippet.id!}
                      buttonText=""
                      buttonVariant="text"
                      buttonSize="small"
                      tooltip="내보내기"
                    />
                    
                    <Tooltip title="수정">
                      <IconButton 
                        size="small"
                        onClick={() => handleOpenEditDialog(snippet)}
                        color="secondary"
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
      
      {/* 스니펫 편집 다이얼로그 */}
      <Dialog
        open={editDialogOpen}
        onClose={handleCloseEditDialog}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>
          코드 스니펫 편집
        </DialogTitle>
        
        <DialogContent>
          <TextField
            label="제목"
            fullWidth
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            margin="normal"
            required
          />
          
          <TextField
            label="설명"
            fullWidth
            value={editedDescription}
            onChange={(e) => setEditedDescription(e.target.value)}
            margin="normal"
            multiline
            rows={2}
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>언어</InputLabel>
            <Select
              value={editedLanguage}
              onChange={(e) => setEditedLanguage(e.target.value as CodeLanguage)}
              label="언어"
            >
              {Object.entries(LANGUAGE_INFO).map(([key, value]) => (
                <MenuItem key={key} value={key}>
                  {value.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <TextField
            label="코드"
            fullWidth
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            margin="normal"
            multiline
            rows={10}
            required
            inputProps={{
              style: { fontFamily: 'monospace' }
            }}
          />
          
          <Box sx={{ mt: 2 }}>
            <TextField
              label="태그 추가"
              size="small"
              value={currentTag}
              onChange={(e) => setCurrentTag(e.target.value)}
              onKeyPress={handleTagKeyPress}
              placeholder="태그 입력 후 엔터"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleAddTag}
                      disabled={!currentTag.trim()}
                      edge="end"
                    >
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', mt: 1, gap: 0.5 }}>
              {editedTags.map((tag, index) => (
                <Chip
                  key={index}
                  label={tag}
                  onDelete={() => handleDeleteTag(tag)}
                  size="small"
                />
              ))}
            </Box>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>취소</Button>
          <Button 
            onClick={handleSaveSnippet} 
            variant="contained" 
            color="primary"
            startIcon={<SaveIcon />}
          >
            저장
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default CodeManagerPage;