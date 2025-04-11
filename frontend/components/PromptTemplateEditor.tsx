import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
  Grid,
  Divider,
  CircularProgress
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import PreviewIcon from '@mui/icons-material/Visibility';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteIcon from '@mui/icons-material/Delete';

import { PromptTemplate, PromptVariable, LLMType } from '../types';
import { createPromptTemplate, updatePromptTemplate, previewPrompt, executePrompt } from '../utils/api';

// 프롬프트 변수를 템플릿에서 추출하는 함수
const extractVariables = (content: string): string[] => {
  const regex = /\{\{(.*?)\}\}/g;
  const matches = [...content.matchAll(regex)];
  const variables = matches.map(match => match[1].trim());
  
  // 중복 제거
  return Array.from(new Set(variables));
};

// 카테고리 목록
const CATEGORIES = [
  '일반',
  '코드 생성',
  '설명',
  '요약',
  '분석',
  '데이터',
  '변환',
  '교육',
  '마케팅',
  '기타'
];

interface PromptTemplateEditorProps {
  template?: PromptTemplate;
  onSave?: (template: PromptTemplate) => void;
  onCancel?: () => void;
  onDelete?: (id: number) => void;
}

const PromptTemplateEditor: React.FC<PromptTemplateEditorProps> = ({
  template,
  onSave,
  onCancel,
  onDelete
}) => {
  // 상태
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [content, setContent] = useState(template?.content || '');
  const [systemPrompt, setSystemPrompt] = useState(template?.system_prompt || '');
  const [category, setCategory] = useState(template?.category || '일반');
  const [tags, setTags] = useState<string[]>(template?.tags || []);
  const [tagInput, setTagInput] = useState('');
  
  const [variables, setVariables] = useState<PromptVariable[]>([]);
  const [previewContent, setPreviewContent] = useState('');
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false);
  const [selectedLlmType, setSelectedLlmType] = useState<LLMType>(LLMType.OPENAI_API);
  
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  
  // 변수 추출 및 상태 업데이트
  useEffect(() => {
    const extractedVars = extractVariables(content);
    
    // 기존 값 유지하면서 새 변수 추가
    setVariables(prevVars => {
      const existingVars = new Map(prevVars.map(v => [v.name, v]));
      
      return extractedVars.map(name => {
        if (existingVars.has(name)) {
          return existingVars.get(name)!;
        }
        return { name, value: '', description: '' };
      });
    });
  }, [content]);
  
  // 템플릿이 변경될 때 상태 업데이트
  useEffect(() => {
    if (template) {
      setName(template.name);
      setDescription(template.description || '');
      setContent(template.content);
      setSystemPrompt(template.system_prompt || '');
      setCategory(template.category);
      setTags(template.tags);
    }
  }, [template]);
  
  // 변수 값 변경 처리
  const handleVariableChange = (index: number, field: 'value' | 'description', value: string) => {
    const updatedVars = [...variables];
    updatedVars[index] = { ...updatedVars[index], [field]: value };
    setVariables(updatedVars);
  };
  
  // 태그 추가 처리
  const handleAddTag = () => {
    if (tagInput && !tags.includes(tagInput)) {
      setTags([...tags, tagInput]);
      setTagInput('');
    }
  };
  
  // 태그 삭제 처리
  const handleDeleteTag = (tagToDelete: string) => {
    setTags(tags.filter(tag => tag !== tagToDelete));
  };
  
  // 미리보기 처리
  const handlePreview = async () => {
    if (!content) {
      setSnackbarMessage('프롬프트 템플릿 내용을 입력해주세요.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }
    
    setPreviewLoading(true);
    
    try {
      // 변수값을 객체로 변환
      const variablesObj = variables.reduce<Record<string, string>>((obj, variable) => {
        obj[variable.name] = variable.value;
        return obj;
      }, {});
      
      // 미리보기 API 호출
      const result = await previewPrompt(content, systemPrompt, variablesObj);
      setPreviewContent(result);
    } catch (error) {
      console.error('미리보기 오류:', error);
      setSnackbarMessage(`미리보기 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setPreviewLoading(false);
    }
  };
  
  // 저장 처리
  const handleSave = async () => {
    // 유효성 검사
    if (!name) {
      setSnackbarMessage('템플릿 이름을 입력해주세요.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }
    
    if (!content) {
      setSnackbarMessage('프롬프트 템플릿 내용을 입력해주세요.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }
    
    setLoading(true);
    
    try {
      // 템플릿 데이터 구성
      const templateData: PromptTemplate = {
        name,
        description,
        content,
        system_prompt: systemPrompt,
        template_variables: variables.map(v => v.name),
        category,
        tags
      };
      
      // ID가 있으면 업데이트, 없으면 생성
      let savedTemplate;
      if (template?.id) {
        savedTemplate = await updatePromptTemplate(template.id, templateData);
      } else {
        savedTemplate = await createPromptTemplate(templateData);
      }
      
      // 저장 완료 알림
      setSnackbarMessage('프롬프트 템플릿이 저장되었습니다.');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      
      // 저장 콜백 호출
      if (onSave) {
        onSave(savedTemplate);
      }
    } catch (error) {
      console.error('저장 오류:', error);
      setSnackbarMessage(`저장 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };
  
  // 실행 처리
  const handleExecute = async () => {
    if (!template?.id) {
      setSnackbarMessage('템플릿을 먼저 저장해주세요.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }
    
    setExecuteDialogOpen(true);
  };
  
  // 실행 확인 처리
  const handleExecuteConfirm = async () => {
    setLoading(true);
    
    try {
      // 변수값을 객체로 변환
      const variablesObj = variables.reduce<Record<string, string>>((obj, variable) => {
        obj[variable.name] = variable.value;
        return obj;
      }, {});
      
      // 실행 API 호출
      await executePrompt(template!.id!, content, systemPrompt, variablesObj, selectedLlmType);
      
      // 성공 알림
      setSnackbarMessage('프롬프트가 성공적으로 실행되었습니다.');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      
      // 다이얼로그 닫기
      setExecuteDialogOpen(false);
    } catch (error) {
      console.error('실행 오류:', error);
      setSnackbarMessage(`실행 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };
  
  // 삭제 처리
  const handleDelete = () => {
    if (template?.id && onDelete) {
      onDelete(template.id);
    }
  };

  return (
    <Box>
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          {template?.id ? '프롬프트 템플릿 편집' : '새 프롬프트 템플릿'}
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              label="템플릿 이름"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              fullWidth
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>카테고리</InputLabel>
              <Select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                label="카테고리"
              >
                {CATEGORIES.map((cat) => (
                  <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        
        <TextField
          label="설명"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          fullWidth
          multiline
          rows={2}
          margin="normal"
        />
        
        <Box sx={{ mt: 2, mb: 1 }}>
          <Typography variant="subtitle1">태그</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
            {tags.map((tag) => (
              <Chip
                key={tag}
                label={tag}
                onDelete={() => handleDeleteTag(tag)}
                color="primary"
                variant="outlined"
              />
            ))}
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <TextField
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                placeholder="새 태그"
                size="small"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddTag();
                    e.preventDefault();
                  }
                }}
              />
              <Button onClick={handleAddTag} size="small" sx={{ ml: 1 }}>
                추가
              </Button>
            </Box>
          </Box>
        </Box>
        
        <TextField
          label="시스템 프롬프트"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          fullWidth
          multiline
          rows={3}
          margin="normal"
          placeholder="LM Studio에 전송할 시스템 프롬프트를 입력하세요. 변수는 {{변수명}} 형식으로 사용할 수 있습니다."
          helperText="예: 당신은 {{역할}} 전문가입니다. 전문적인 관점에서 답변해주세요."
        />
        
        <TextField
          label="사용자 프롬프트 템플릿"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          fullWidth
          multiline
          rows={8}
          margin="normal"
          required
          placeholder="변수는 {{변수명}} 형식으로 입력하세요."
          helperText="예: 당신은 {{역할}}로서 {{주제}}에 대해 설명해주세요."
        />
      </Paper>
      
      {variables.length > 0 && (
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            변수 설정
          </Typography>
          
          {variables.map((variable, index) => (
            <Box key={variable.name} sx={{ mb: 2 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={3}>
                  <Typography fontWeight="bold">
                    {`{{${variable.name}}}`}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={5}>
                  <TextField
                    label="값"
                    value={variable.value}
                    onChange={(e) => handleVariableChange(index, 'value', e.target.value)}
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    label="설명"
                    value={variable.description}
                    onChange={(e) => handleVariableChange(index, 'description', e.target.value)}
                    fullWidth
                    size="small"
                    placeholder="선택사항"
                  />
                </Grid>
              </Grid>
            </Box>
          ))}
          
          <Button 
            variant="outlined"
            color="primary"
            onClick={handlePreview}
            startIcon={previewLoading ? <CircularProgress size={20} /> : <PreviewIcon />}
            disabled={previewLoading}
            sx={{ mt: 2 }}
          >
            미리보기
          </Button>
          
          {previewContent && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="subtitle1" gutterBottom>미리보기 결과:</Typography>
              <Typography variant="body1" whiteSpace="pre-wrap">
                {previewContent}
              </Typography>
            </Box>
          )}
        </Paper>
      )}
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
        <Box>
          {template?.id && onDelete && (
            <Button
              variant="outlined"
              color="error"
              onClick={handleDelete}
              startIcon={<DeleteIcon />}
            >
              삭제
            </Button>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          {onCancel && (
            <Button
              variant="outlined"
              color="inherit"
              onClick={onCancel}
            >
              취소
            </Button>
          )}
          
          <Button
            variant="contained"
            color="primary"
            onClick={handleSave}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
            disabled={loading}
          >
            저장
          </Button>
          
          <Button
            variant="contained"
            color="secondary"
            onClick={handleExecute}
            startIcon={<PlayArrowIcon />}
            disabled={!template?.id || loading}
          >
            실행
          </Button>
        </Box>
      </Box>
      
      {/* 실행 다이얼로그 */}
      <Dialog open={executeDialogOpen} onClose={() => setExecuteDialogOpen(false)}>
        <DialogTitle>프롬프트 실행</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            이 프롬프트 템플릿을 선택한 LLM으로 실행하시겠습니까?
          </Typography>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>LLM 유형</InputLabel>
            <Select
              value={selectedLlmType}
              onChange={(e) => setSelectedLlmType(e.target.value as LLMType)}
              label="LLM 유형"
            >
              <MenuItem value={LLMType.OPENAI_API}>OpenAI API</MenuItem>
              <MenuItem value={LLMType.CLAUDE_API}>Claude API</MenuItem>
              <MenuItem value={LLMType.LOCAL_LLM}>Local LLM</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecuteDialogOpen(false)} color="inherit">
            취소
          </Button>
          <Button 
            onClick={handleExecuteConfirm}
            color="primary"
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
          >
            {loading ? '처리 중...' : '실행'}
          </Button>
        </DialogActions>
      </Dialog>
      
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
    </Box>
  );
};

export default PromptTemplateEditor;