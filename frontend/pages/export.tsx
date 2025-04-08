import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import {
  Container,
  Typography,
  Box,
  Grid,
  Paper,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Checkbox,
  Button,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Chip,
  Snackbar,
  Alert,
  CircularProgress
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import CodeIcon from '@mui/icons-material/Code';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import Head from 'next/head';
import Layout from '../components/Layout';
import ExportButton from '../components/ExportButton';
import BatchExportDialog, { BatchExportItem } from '../components/BatchExportDialog';
import { Question, CodeSnippet } from '../types';
import { fetchQuestions, fetchCodeSnippets } from '../utils/api';

enum TabType {
  QUESTIONS = 'questions',
  CODE_SNIPPETS = 'code_snippets',
  AGENT_LOGS = 'agent_logs',
}

const ExportPage: NextPage = () => {
  // 탭 상태
  const [activeTab, setActiveTab] = useState<TabType>(TabType.QUESTIONS);
  
  // 데이터 상태
  const [questions, setQuestions] = useState<Question[]>([]);
  const [codeSnippets, setCodeSnippets] = useState<CodeSnippet[]>([]);
  const [agentLogs, setAgentLogs] = useState<any[]>([]); // 에이전트 로그 타입 정의 필요
  
  // 필터링 상태
  const [searchTerm, setSearchTerm] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [allTags, setAllTags] = useState<string[]>([]);
  
  // 선택 상태
  const [selectedItems, setSelectedItems] = useState<BatchExportItem[]>([]);
  const [batchDialogOpen, setBatchDialogOpen] = useState(false);
  
  // 로딩 상태
  const [loading, setLoading] = useState(false);
  
  // 알림 상태
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  
  // 초기 데이터 로드
  useEffect(() => {
    loadData();
  }, []);
  
  // 탭 변경 시 데이터 다시 로드
  useEffect(() => {
    loadData();
  }, [activeTab]);
  
  // 데이터 로드 함수
  const loadData = async () => {
    setLoading(true);
    
    try {
      switch (activeTab) {
        case TabType.QUESTIONS:
          const questionsData = await fetchQuestions();
          setQuestions(questionsData);
          extractTags(questionsData.map(q => q.tags));
          break;
          
        case TabType.CODE_SNIPPETS:
          const snippetsData = await fetchCodeSnippets();
          setCodeSnippets(snippetsData);
          extractTags(snippetsData.map(s => s.tags));
          break;
          
        case TabType.AGENT_LOGS:
          // 에이전트 로그 API 호출 (구현 필요)
          // const logsData = await fetchAgentLogs();
          // setAgentLogs(logsData);
          setAgentLogs([]);
          break;
      }
    } catch (error) {
      console.error('데이터 로드 오류:', error);
      setSnackbarMessage(`데이터 로드 중 오류가 발생했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };
  
  // 태그 추출 및 설정
  const extractTags = (tagLists: string[][]) => {
    const tagSet = new Set<string>();
    
    tagLists.forEach(tags => {
      tags.forEach(tag => tagSet.add(tag));
    });
    
    setAllTags(Array.from(tagSet).sort());
  };
  
  // 탭 변경 처리
  const handleTabChange = (event: React.SyntheticEvent, newValue: TabType) => {
    setActiveTab(newValue);
    setSearchTerm('');
    setTagFilter('');
    setSelectedItems([]);
  };
  
  // 아이템 선택 처리
  const handleItemSelect = (item: BatchExportItem) => {
    const existingIndex = selectedItems.findIndex(
      i => i.type === item.type && i.id === item.id
    );
    
    if (existingIndex >= 0) {
      // 이미 선택된 항목이면 제거
      setSelectedItems(selectedItems.filter((_, i) => i !== existingIndex));
    } else {
      // 새 항목이면 추가
      setSelectedItems([...selectedItems, item]);
    }
  };
  
  // 아이템 필터링
  const getFilteredItems = () => {
    switch (activeTab) {
      case TabType.QUESTIONS:
        return questions.filter(question => {
          const matchesSearch = !searchTerm || 
            question.content.toLowerCase().includes(searchTerm.toLowerCase());
          const matchesTag = !tagFilter || 
            question.tags.includes(tagFilter);
          
          return matchesSearch && matchesTag;
        });
        
      case TabType.CODE_SNIPPETS:
        return codeSnippets.filter(snippet => {
          const matchesSearch = !searchTerm || 
            snippet.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (snippet.description && snippet.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
            snippet.content.toLowerCase().includes(searchTerm.toLowerCase());
          const matchesTag = !tagFilter || 
            snippet.tags.includes(tagFilter);
          
          return matchesSearch && matchesTag;
        });
        
      case TabType.AGENT_LOGS:
        // 에이전트 로그 필터링 (구현 필요)
        return agentLogs;
        
      default:
        return [];
    }
  };
  
  // 아이템 섹션 렌더링
  const renderItems = () => {
    const filteredItems = getFilteredItems();
    
    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      );
    }
    
    if (filteredItems.length === 0) {
      return (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            표시할 항목이 없습니다.
          </Typography>
        </Box>
      );
    }
    
    return (
      <List>
        {activeTab === TabType.QUESTIONS && 
          renderQuestions(filteredItems as Question[])}
        
        {activeTab === TabType.CODE_SNIPPETS && 
          renderCodeSnippets(filteredItems as CodeSnippet[])}
        
        {activeTab === TabType.AGENT_LOGS && 
          renderAgentLogs(filteredItems)}
      </List>
    );
  };
  
  // 질문 항목 렌더링
  const renderQuestions = (items: Question[]) => {
    return items.map(question => {
      const isSelected = selectedItems.some(
        item => item.type === 'question' && item.id === question.id
      );
      
      return (
        <ListItem
          key={`question-${question.id}`}
          sx={{ 
            borderRadius: 1,
            mb: 1,
            border: '1px solid',
            borderColor: 'divider',
            bgcolor: isSelected ? 'action.selected' : 'background.paper'
          }}
        >
          <ListItemIcon>
            <Checkbox
              edge="start"
              checked={isSelected}
              onChange={() => handleItemSelect({
                type: 'question',
                id: question.id!,
                title: question.content.substring(0, 50) + (question.content.length > 50 ? '...' : '')
              })}
            />
          </ListItemIcon>
          
          <ListItemIcon>
            <QuestionAnswerIcon />
          </ListItemIcon>
          
          <ListItemText
            primary={`질문 #${question.id}`}
            secondary={
              <Box>
                <Typography variant="body2" noWrap>
                  {question.content}
                </Typography>
                {question.tags.length > 0 && (
                  <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
                    {question.tags.map(tag => (
                      <Chip
                        key={tag}
                        label={tag}
                        size="small"
                        variant="outlined"
                        sx={{ height: 20 }}
                      />
                    ))}
                  </Box>
                )}
              </Box>
            }
          />
          
          <ListItemSecondaryAction>
            <ExportButton
              type="question"
              id={question.id!}
              size="small"
              buttonText="내보내기"
            />
          </ListItemSecondaryAction>
        </ListItem>
      );
    });
  };
  
  // 코드 스니펫 항목 렌더링
  const renderCodeSnippets = (items: CodeSnippet[]) => {
    return items.map(snippet => {
      const isSelected = selectedItems.some(
        item => item.type === 'code_snippet' && item.id === snippet.id
      );
      
      return (
        <ListItem
          key={`snippet-${snippet.id}`}
          sx={{ 
            borderRadius: 1,
            mb: 1,
            border: '1px solid',
            borderColor: 'divider',
            bgcolor: isSelected ? 'action.selected' : 'background.paper'
          }}
        >
          <ListItemIcon>
            <Checkbox
              edge="start"
              checked={isSelected}
              onChange={() => handleItemSelect({
                type: 'code_snippet',
                id: snippet.id!,
                title: snippet.title
              })}
            />
          </ListItemIcon>
          
          <ListItemIcon>
            <CodeIcon />
          </ListItemIcon>
          
          <ListItemText
            primary={snippet.title}
            secondary={
              <Box>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {snippet.description || `${snippet.language} 코드 스니펫`}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                  <Chip
                    label={snippet.language}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ mr: 1 }}
                  />
                  {snippet.tags.length > 0 && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {snippet.tags.map(tag => (
                        <Chip
                          key={tag}
                          label={tag}
                          size="small"
                          variant="outlined"
                          sx={{ height: 20 }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              </Box>
            }
          />
          
          <ListItemSecondaryAction>
            <ExportButton
              type="code_snippet"
              id={snippet.id!}
              size="small"
              buttonText="내보내기"
            />
          </ListItemSecondaryAction>
        </ListItem>
      );
    });
  };
  
  // 에이전트 로그 항목 렌더링
  const renderAgentLogs = (items: any[]) => {
    // 에이전트 로그 렌더링 (구현 필요)
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography color="text.secondary">
          에이전트 로그 기능은 아직 준비 중입니다.
        </Typography>
      </Box>
    );
  };
  
  // 필터 초기화
  const handleResetFilters = () => {
    setSearchTerm('');
    setTagFilter('');
  };
  
  // 일괄 내보내기 시작
  const handleBatchExport = () => {
    if (selectedItems.length === 0) {
      setSnackbarMessage('내보낼 항목을 하나 이상 선택해주세요.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }
    
    setBatchDialogOpen(true);
  };
  
  // 일괄 내보내기 완료
  const handleBatchExportSuccess = () => {
    setSnackbarMessage('선택한 항목이 성공적으로 내보내졌습니다.');
    setSnackbarSeverity('success');
    setSnackbarOpen(true);
    setSelectedItems([]);
  };

  return (
    <>
      <Head>
        <title>내보내기 - LLMNightRun</title>
        <meta name="description" content="질문, 응답, 코드 스니펫을 다양한 형식으로 내보내기" />
      </Head>
      
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            내보내기
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            질문, 응답, 코드 스니펫을 다양한 형식으로 내보내기
          </Typography>
        </Box>
        
        <Paper sx={{ mb: 2 }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab label="질문 및 응답" value={TabType.QUESTIONS} />
            <Tab label="코드 스니펫" value={TabType.CODE_SNIPPETS} />
            <Tab label="에이전트 로그" value={TabType.AGENT_LOGS} />
          </Tabs>
        </Paper>
        
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="검색..."
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
            <Grid item xs={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>태그</InputLabel>
                <Select
                  value={tagFilter}
                  onChange={(e) => setTagFilter(e.target.value)}
                  label="태그"
                  displayEmpty
                >
                  <MenuItem value="">전체 태그</MenuItem>
                  {allTags.map(tag => (
                    <MenuItem key={tag} value={tag}>{tag}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                onClick={handleResetFilters}
                disabled={!searchTerm && !tagFilter}
              >
                필터 초기화
              </Button>
            </Grid>
          </Grid>
        </Paper>
        
        <Paper sx={{ mb: 3 }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {activeTab === TabType.QUESTIONS ? '질문 및 응답' : 
               activeTab === TabType.CODE_SNIPPETS ? '코드 스니펫' : 
               '에이전트 로그'}
            </Typography>
            
            <Button
              variant="contained"
              color="primary"
              startIcon={<FileDownloadIcon />}
              onClick={handleBatchExport}
              disabled={selectedItems.length === 0}
            >
              선택 항목 내보내기 ({selectedItems.length})
            </Button>
          </Box>
          <Divider />
          
          {renderItems()}
        </Paper>
      </Container>
      
      {/* 일괄 내보내기 다이얼로그 */}
      <BatchExportDialog
        open={batchDialogOpen}
        items={selectedItems}
        onClose={() => setBatchDialogOpen(false)}
        onSuccess={handleBatchExportSuccess}
      />
      
      {/* 알림 스낵바 */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default ExportPage;