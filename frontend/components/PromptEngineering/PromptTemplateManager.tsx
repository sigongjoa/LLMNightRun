import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  FormHelperText,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  TextField,
  Tooltip,
  Typography,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Info as InfoIcon,
  Delete as DeleteIcon,
  FileCopy as FileCopyIcon,
} from '@mui/icons-material';
import axios from 'axios';

// 프롬프트 템플릿 타입 정의
export interface PromptTemplate {
  id: string;
  name: string;
  description?: string;
  content: string;
  created_at?: string;
  updated_at?: string;
  is_system?: boolean;
  author?: string;
}

interface PromptTemplateManagerProps {
  onSelect?: (template: PromptTemplate) => void;
  readOnly?: boolean;
  showTitle?: boolean;
}

const PromptTemplateManager: React.FC<PromptTemplateManagerProps> = ({
  onSelect,
  readOnly = false,
  showTitle = true
}) => {
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isNewTemplate, setIsNewTemplate] = useState(false);
  const [editedTemplate, setEditedTemplate] = useState<Partial<PromptTemplate>>({});
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{open: boolean, message: string, severity: 'success' | 'error' | 'info'}>({
    open: false,
    message: '',
    severity: 'info'
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // 템플릿 목록 가져오기
  const fetchTemplates = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.get('/api/prompt-templates');
      if (response.data.success) {
        setTemplates(response.data.templates || []);
        
        // 선택된 템플릿이 있으면 유지, 없으면 첫 번째 템플릿 선택
        if (response.data.templates && response.data.templates.length > 0) {
          if (selectedTemplate) {
            const stillExists = response.data.templates.find((t: PromptTemplate) => t.id === selectedTemplate.id);
            if (!stillExists) {
              setSelectedTemplate(response.data.templates[0]);
            } else {
              const updated = response.data.templates.find((t: PromptTemplate) => t.id === selectedTemplate.id);
              setSelectedTemplate(updated);
            }
          } else {
            setSelectedTemplate(response.data.templates[0]);
          }
        } else {
          setSelectedTemplate(null);
        }
      } else {
        setError('템플릿을 불러오는데 실패했습니다: ' + response.data.message);
      }
    } catch (err) {
      console.error('템플릿 목록 불러오기 오류:', err);
      setError('템플릿을 불러오는데 실패했습니다. 네트워크 연결을 확인하세요.');
    } finally {
      setIsLoading(false);
    }
  };

  // 컴포넌트 마운트 시 템플릿 목록 가져오기
  useEffect(() => {
    fetchTemplates();
  }, []);

  // 템플릿 선택 처리
  const handleSelectTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setSelectedTemplate(template);
      // 선택 이벤트가 제공된 경우 호출
      if (onSelect) {
        onSelect(template);
      }
    }
  };

  // 편집 모드 시작
  const handleStartEditing = () => {
    if (selectedTemplate) {
      setEditedTemplate({ ...selectedTemplate });
      setIsEditing(true);
      setIsNewTemplate(false);
    }
  };

  // 새 템플릿 생성 모드 시작
  const handleCreateNew = () => {
    setEditedTemplate({
      name: '새 프롬프트 템플릿',
      description: '템플릿 설명을 입력하세요',
      content: '프롬프트 내용을 입력하세요'
    });
    setIsEditing(true);
    setIsNewTemplate(true);
  };

  // 템플릿 복제
  const handleDuplicate = () => {
    if (selectedTemplate) {
      setEditedTemplate({
        name: `${selectedTemplate.name} 복사본`,
        description: selectedTemplate.description,
        content: selectedTemplate.content
      });
      setIsEditing(true);
      setIsNewTemplate(true);
    }
  };

  // 편집 취소
  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedTemplate({});
  };

  // 편집 필드 변경 처리
  const handleEditChange = (field: keyof PromptTemplate, value: string) => {
    setEditedTemplate(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // 템플릿 저장
  const handleSaveTemplate = async () => {
    if (!editedTemplate.name || !editedTemplate.content) {
      setSnackbar({
        open: true,
        message: '이름과 내용은 필수 항목입니다',
        severity: 'error'
      });
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let response;
      
      if (isNewTemplate) {
        // 새 템플릿 생성
        response = await axios.post('/api/prompt-templates', editedTemplate);
      } else {
        // 기존 템플릿 업데이트
        response = await axios.put(`/api/prompt-templates/${editedTemplate.id}`, editedTemplate);
      }

      if (response.data.success) {
        setSnackbar({
          open: true,
          message: isNewTemplate ? '새 템플릿이 생성되었습니다' : '템플릿이 업데이트되었습니다',
          severity: 'success'
        });
        
        // 템플릿 목록 새로고침
        await fetchTemplates();
        
        // 편집 모드 종료
        setIsEditing(false);
        setEditedTemplate({});
      } else {
        setError(response.data.message || '저장 중 오류가 발생했습니다');
      }
    } catch (err) {
      console.error('템플릿 저장 오류:', err);
      setError('템플릿을 저장하는데 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  // 템플릿 삭제 다이얼로그 열기
  const handleOpenDeleteDialog = () => {
    if (selectedTemplate && !selectedTemplate.is_system) {
      setDeleteDialogOpen(true);
    } else {
      setSnackbar({
        open: true,
        message: '시스템 템플릿은 삭제할 수 없습니다',
        severity: 'error'
      });
    }
  };

  // 템플릿 삭제 처리
  const handleDeleteTemplate = async () => {
    if (!selectedTemplate) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.delete(`/api/prompt-templates/${selectedTemplate.id}`);
      
      if (response.data.success) {
        setSnackbar({
          open: true,
          message: '템플릿이 삭제되었습니다',
          severity: 'success'
        });
        
        // 템플릿 목록 새로고침
        await fetchTemplates();
      } else {
        setError(response.data.message || '삭제 중 오류가 발생했습니다');
      }
    } catch (err) {
      console.error('템플릿 삭제 오류:', err);
      setError('템플릿을 삭제하는데 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
      setDeleteDialogOpen(false);
    }
  };

  // 스낵바 닫기
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <Paper 
      elevation={0} 
      variant="outlined" 
      sx={{ 
        p: 2, 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        borderRadius: 2
      }}
    >
      {/* 헤더 */}
      {showTitle && (
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" component="h2" sx={{ fontWeight: 600 }}>
            프롬프트 템플릿 관리
            <Tooltip title="프롬프트 템플릿을 통해 AI와의 대화를 최적화할 수 있습니다">
              <IconButton size="small" sx={{ ml: 0.5 }}>
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Typography>
          
          {!readOnly && (
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={handleCreateNew}
              disabled={isLoading || isEditing}
              size="small"
            >
              새 템플릿
            </Button>
          )}
        </Box>
      )}

      {/* 오류 메시지 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 메인 컨텐츠 영역 */}
      <Box sx={{ display: 'flex', flexGrow: 1, gap: 2, overflow: 'hidden' }}>
        {/* 템플릿 목록 */}
        <Card variant="outlined" sx={{ width: '30%', overflow: 'auto' }}>
          <CardContent sx={{ p: 1, paddingBottom: '8px !important' }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
              템플릿 목록
            </Typography>
            
            {isLoading && templates.length === 0 ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                <CircularProgress size={24} />
              </Box>
            ) : templates.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', p: 2 }}>
                저장된 템플릿이 없습니다
              </Typography>
            ) : (
              <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
                {templates.map(template => (
                  <Box
                    key={template.id}
                    component="li"
                    onClick={() => handleSelectTemplate(template.id)}
                    sx={{
                      p: 1,
                      borderRadius: 1,
                      mb: 0.5,
                      cursor: 'pointer',
                      backgroundColor: selectedTemplate?.id === template.id ? 'action.selected' : 'transparent',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                      transition: 'background-color 0.2s'
                    }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {template.name}
                      {template.is_system && (
                        <Typography 
                          component="span" 
                          variant="caption" 
                          sx={{ 
                            ml: 1, 
                            px: 0.8, 
                            py: 0.2, 
                            bgcolor: 'primary.light', 
                            color: 'white', 
                            borderRadius: 1,
                            fontSize: '0.6rem'
                          }}
                        >
                          시스템
                        </Typography>
                      )}
                    </Typography>
                    
                    {template.description && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{
                          display: 'block',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {template.description}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>

        {/* 템플릿 상세 정보 / 편집 */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {isEditing ? (
            // 편집 모드
            <Card variant="outlined" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <CardContent sx={{ p: 2, flexGrow: 1, overflow: 'auto' }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                  {isNewTemplate ? '새 템플릿 생성' : '템플릿 편집'}
                </Typography>
                
                <TextField
                  fullWidth
                  label="템플릿 이름"
                  value={editedTemplate.name || ''}
                  onChange={(e) => handleEditChange('name', e.target.value)}
                  variant="outlined"
                  size="small"
                  margin="normal"
                  required
                  error={!editedTemplate.name}
                  helperText={!editedTemplate.name ? '이름은 필수 항목입니다' : ''}
                />
                
                <TextField
                  fullWidth
                  label="설명"
                  value={editedTemplate.description || ''}
                  onChange={(e) => handleEditChange('description', e.target.value)}
                  variant="outlined"
                  size="small"
                  margin="normal"
                  multiline
                  rows={2}
                />
                
                <TextField
                  fullWidth
                  label="프롬프트 내용"
                  value={editedTemplate.content || ''}
                  onChange={(e) => handleEditChange('content', e.target.value)}
                  variant="outlined"
                  margin="normal"
                  multiline
                  rows={10}
                  required
                  error={!editedTemplate.content}
                  helperText={!editedTemplate.content ? '내용은 필수 항목입니다' : '변수 사용 예: {{user_input}}, {{context}}'}
                  sx={{ 
                    fontFamily: '"Consolas", "Courier New", monospace', 
                    fontSize: '0.9rem',
                    '& .MuiInputBase-root': {
                      fontFamily: '"Consolas", "Courier New", monospace',
                      fontSize: '0.9rem',
                    }
                  }}
                />
              </CardContent>
              
              <Divider />
              
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                <Button
                  variant="outlined"
                  onClick={handleCancelEdit}
                  disabled={isLoading}
                  startIcon={<CloseIcon />}
                >
                  취소
                </Button>
                
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSaveTemplate}
                  disabled={isLoading || !editedTemplate.name || !editedTemplate.content}
                  startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
                >
                  저장
                </Button>
              </Box>
            </Card>
          ) : (
            // 보기 모드
            selectedTemplate ? (
              <Card variant="outlined" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <CardContent sx={{ p: 2, flexGrow: 1, overflow: 'auto' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h3" sx={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {selectedTemplate.name}
                      {selectedTemplate.is_system && (
                        <Typography 
                          component="span" 
                          variant="caption" 
                          sx={{ 
                            ml: 1, 
                            px: 0.8, 
                            py: 0.2, 
                            bgcolor: 'primary.light', 
                            color: 'white', 
                            borderRadius: 1,
                            fontSize: '0.7rem'
                          }}
                        >
                          시스템
                        </Typography>
                      )}
                    </Typography>
                    
                    {!readOnly && (
                      <Box>
                        <Tooltip title="템플릿 복제">
                          <IconButton onClick={handleDuplicate} size="small" sx={{ mr: 0.5 }}>
                            <FileCopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        
                        {!selectedTemplate.is_system && (
                          <>
                            <Tooltip title="템플릿 편집">
                              <IconButton onClick={handleStartEditing} size="small" sx={{ mr: 0.5 }}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            
                            <Tooltip title="템플릿 삭제">
                              <IconButton onClick={handleOpenDeleteDialog} size="small" color="error">
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                      </Box>
                    )}
                  </Box>
                  
                  {selectedTemplate.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {selectedTemplate.description}
                    </Typography>
                  )}
                  
                  <Divider sx={{ mb: 2 }} />
                  
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                    프롬프트 내용:
                  </Typography>
                  
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 2,
                      maxHeight: '400px',
                      overflow: 'auto',
                      bgcolor: 'grey.50',
                      fontFamily: '"Consolas", "Courier New", monospace',
                      fontSize: '0.9rem',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}
                  >
                    {selectedTemplate.content}
                  </Paper>
                  
                  {selectedTemplate.updated_at && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'right' }}>
                      최근 업데이트: {new Date(selectedTemplate.updated_at).toLocaleString()}
                      {selectedTemplate.author && ` | 작성자: ${selectedTemplate.author}`}
                    </Typography>
                  )}
                </CardContent>
                
                {onSelect && (
                  <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Button
                      variant="contained"
                      color="primary"
                      fullWidth
                      onClick={() => onSelect(selectedTemplate)}
                    >
                      이 템플릿 사용하기
                    </Button>
                  </Box>
                )}
              </Card>
            ) : (
              <Card variant="outlined" sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                    템플릿을 선택하거나 새로 생성하세요
                  </Typography>
                </CardContent>
              </Card>
            )
          )}
        </Box>
      </Box>

      {/* 삭제 확인 다이얼로그 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>템플릿 삭제</DialogTitle>
        <DialogContent>
          <Typography>
            정말로 <strong>{selectedTemplate?.name}</strong> 템플릿을 삭제하시겠습니까?
            이 작업은 되돌릴 수 없습니다.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>취소</Button>
          <Button onClick={handleDeleteTemplate} color="error" autoFocus>
            삭제
          </Button>
        </DialogActions>
      </Dialog>

      {/* 알림 스낵바 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default PromptTemplateManager;