import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  ListItemIcon,
  IconButton,
  Button,
  TextField,
  InputAdornment,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Divider,
  Tooltip,
  CircularProgress
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import DescriptionIcon from '@mui/icons-material/Description';
import CategoryIcon from '@mui/icons-material/Category';
import TagIcon from '@mui/icons-material/Tag';

import { PromptTemplate } from '../types';
import { fetchPromptTemplates, deletePromptTemplate } from '../utils/api';

interface PromptTemplateListProps {
  onEdit?: (template: PromptTemplate) => void;
  onNew?: () => void;
  onSelect?: (template: PromptTemplate) => void;
}

const PromptTemplateList: React.FC<PromptTemplateListProps> = ({
  onEdit,
  onNew,
  onSelect
}) => {
  // 상태
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [tagFilter, setTagFilter] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  
  // 삭제 확인 다이얼로그
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState<PromptTemplate | null>(null);
  
  // 알림
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  
  // 템플릿 목록 로드
  const loadTemplates = async () => {
    setLoading(true);
    try {
      const data = await fetchPromptTemplates();
      setTemplates(data);
      
      // 카테고리 및 태그 목록 추출
      const allCategories = new Set<string>();
      const allTags = new Set<string>();
      
      data.forEach(template => {
        allCategories.add(template.category);
        template.tags.forEach(tag => allTags.add(tag));
      });
      
      setCategories(Array.from(allCategories).sort());
      setTags(Array.from(allTags).sort());
      
      // 필터링 적용
      applyFilters(data, searchTerm, categoryFilter, tagFilter);
    } catch (error) {
      console.error('템플릿 로드 오류:', error);
      setSnackbarMessage(`템플릿 로드 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };
  
  // 첫 로드
  useEffect(() => {
    loadTemplates();
  }, []);
  
  // 필터 변경 시 적용
  useEffect(() => {
    applyFilters(templates, searchTerm, categoryFilter, tagFilter);
  }, [searchTerm, categoryFilter, tagFilter]);
  
  // 필터링 함수
  const applyFilters = (
    data: PromptTemplate[],
    search: string,
    category: string,
    tag: string
  ) => {
    let filtered = [...data];
    
    // 검색어 필터
    if (search) {
      const lowerSearch = search.toLowerCase();
      filtered = filtered.filter(
        template => 
          template.name.toLowerCase().includes(lowerSearch) ||
          (template.description && template.description.toLowerCase().includes(lowerSearch)) ||
          template.content.toLowerCase().includes(lowerSearch)
      );
    }
    
    // 카테고리 필터
    if (category) {
      filtered = filtered.filter(template => template.category === category);
    }
    
    // 태그 필터
    if (tag) {
      filtered = filtered.filter(template => template.tags.includes(tag));
    }
    
    setFilteredTemplates(filtered);
  };
  
  // 편집 처리
  const handleEdit = (template: PromptTemplate, event: React.MouseEvent) => {
    event.stopPropagation();
    if (onEdit) {
      onEdit(template);
    }
  };
  
  // 삭제 시작
  const handleDeleteStart = (template: PromptTemplate, event: React.MouseEvent) => {
    event.stopPropagation();
    setTemplateToDelete(template);
    setDeleteDialogOpen(true);
  };
  
  // 삭제 확인
  const handleDeleteConfirm = async () => {
    if (!templateToDelete) return;
    
    try {
      await deletePromptTemplate(templateToDelete.id!);
      
      // 성공 알림
      setSnackbarMessage('템플릿이 삭제되었습니다.');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      
      // 목록 새로고침
      await loadTemplates();
    } catch (error) {
      console.error('삭제 오류:', error);
      setSnackbarMessage(`삭제 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setDeleteDialogOpen(false);
      setTemplateToDelete(null);
    }
  };
  
  // 템플릿 선택
  const handleSelectTemplate = (template: PromptTemplate) => {
    if (onSelect) {
      onSelect(template);
    }
  };
  
  // 새 템플릿 생성
  const handleNew = () => {
    if (onNew) {
      onNew();
    }
  };
  
  // 필터 초기화
  const handleResetFilters = () => {
    setSearchTerm('');
    setCategoryFilter('');
    setTagFilter('');
  };

  return (
    <Box>
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" component="h2">
            프롬프트 템플릿
          </Typography>
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleNew}
          >
            새 템플릿
          </Button>
        </Box>
        
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="템플릿 검색..."
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
              <InputLabel>카테고리</InputLabel>
              <Select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                label="카테고리"
                displayEmpty
              >
                <MenuItem value="">전체 카테고리</MenuItem>
                {categories.map(category => (
                  <MenuItem key={category} value={category}>{category}</MenuItem>
                ))}
              </Select>
            </FormControl>
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
                {tags.map(tag => (
                  <MenuItem key={tag} value={tag}>{tag}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        
        {(searchTerm || categoryFilter || tagFilter) && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2">
                필터: 
                {searchTerm && (
                  <Chip 
                    label={`검색: ${searchTerm}`} 
                    size="small" 
                    onDelete={() => setSearchTerm('')}
                    sx={{ ml: 1 }}
                  />
                )}
                {categoryFilter && (
                  <Chip 
                    label={`카테고리: ${categoryFilter}`} 
                    size="small" 
                    onDelete={() => setCategoryFilter('')}
                    sx={{ ml: 1 }}
                  />
                )}
                {tagFilter && (
                  <Chip 
                    label={`태그: ${tagFilter}`} 
                    size="small" 
                    onDelete={() => setTagFilter('')}
                    sx={{ ml: 1 }}
                  />
                )}
              </Typography>
            </Box>
            
            <Button 
              size="small" 
              onClick={handleResetFilters}
            >
              필터 초기화
            </Button>
          </Box>
        )}
        
        <Divider sx={{ my: 2 }} />
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : filteredTemplates.length > 0 ? (
          <List>
            {filteredTemplates.map((template) => (
              <ListItem
                key={template.id}
                button
                onClick={() => handleSelectTemplate(template)}
                sx={{ 
                  borderRadius: 1,
                  mb: 1,
                  border: '1px solid',
                  borderColor: 'divider'
                }}
              >
                <ListItemIcon>
                  <DescriptionIcon />
                </ListItemIcon>
                <ListItemText
                  primary={template.name}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {template.description || '설명 없음'}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                        <Tooltip title="카테고리">
                          <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                            <CategoryIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">
                              {template.category}
                            </Typography>
                          </Box>
                        </Tooltip>
                        
                        {template.tags.length > 0 && (
                          <Tooltip title="태그">
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <TagIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                              <Box sx={{ display: 'flex', gap: 0.5 }}>
                                {template.tags.slice(0, 3).map(tag => (
                                  <Chip
                                    key={tag}
                                    label={tag}
                                    size="small"
                                    variant="outlined"
                                    sx={{ height: 20 }}
                                  />
                                ))}
                                {template.tags.length > 3 && (
                                  <Chip
                                    label={`+${template.tags.length - 3}`}
                                    size="small"
                                    variant="outlined"
                                    sx={{ height: 20 }}
                                  />
                                )}
                              </Box>
                            </Box>
                          </Tooltip>
                        )}
                      </Box>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton 
                    edge="end" 
                    aria-label="edit" 
                    onClick={(e) => handleEdit(template, e)}
                    sx={{ mr: 1 }}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton 
                    edge="end" 
                    aria-label="delete" 
                    onClick={(e) => handleDeleteStart(template, e)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        ) : (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography color="text.secondary">
              {templates.length === 0 
                ? '템플릿이 없습니다. 새 템플릿을 만들어 보세요.' 
                : '검색 결과가 없습니다.'}
            </Typography>
          </Box>
        )}
      </Paper>
      
      {/* 삭제 확인 다이얼로그 */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>템플릿 삭제</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {templateToDelete && `'${templateToDelete.name}' 템플릿을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} color="inherit">
            취소
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            삭제
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

export default PromptTemplateList;