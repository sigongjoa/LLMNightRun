import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Paper,
  Grid,
  Chip,
  Stack,
  Alert,
  CircularProgress,
  Snackbar,
  InputAdornment,
  IconButton
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../../utils/constants';
import { MemoryType } from './MemoryList';

interface CreateMemoryFormProps {
  onMemoryCreated?: () => void;
}

const CreateMemoryForm: React.FC<CreateMemoryFormProps> = ({ onMemoryCreated }) => {
  // 상태 관리
  const [content, setContent] = useState<string>('');
  const [memoryType, setMemoryType] = useState<MemoryType>(MemoryType.NOTE);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  // 메모리 생성 처리
  const handleCreateMemory = async () => {
    if (!content.trim()) {
      setError('메모리 내용을 입력해주세요.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const memory = {
        content: content.trim(),
        type: memoryType,
        metadata: {
          tags: tags,
          created_manually: true
        }
      };

      await axios.post(`${API_BASE_URL}/memory/add`, memory, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });
      
      // 성공 후 폼 초기화
      setContent('');
      setMemoryType(MemoryType.NOTE);
      setTags([]);
      setSuccess(true);
      
      // 부모 컴포넌트에 알림
      if (onMemoryCreated) {
        onMemoryCreated();
      }
    } catch (err) {
      console.error('메모리 생성 실패:', err);
      setError('메모리 생성 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 태그 추가
  const handleAddTag = () => {
    if (!newTag.trim()) return;
    
    // 중복 태그 방지
    if (!tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
    }
    
    setNewTag('');
  };

  // 엔터 키로 태그 추가
  const handleTagKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  // 태그 삭제
  const handleDeleteTag = (tagToDelete: string) => {
    setTags(tags.filter(tag => tag !== tagToDelete));
  };

  // 성공 알림 닫기
  const handleCloseSuccess = () => {
    setSuccess(false);
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        새 메모리 생성
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel id="memory-type-label">메모리 유형</InputLabel>
            <Select
              labelId="memory-type-label"
              value={memoryType}
              label="메모리 유형"
              onChange={(e) => setMemoryType(e.target.value as MemoryType)}
            >
              {Object.values(MemoryType).map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            minRows={4}
            maxRows={8}
            label="메모리 내용"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="LLM이 나중에 참조할 수 있는 내용을 입력하세요."
          />
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="태그 추가"
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyPress={handleTagKeyPress}
            placeholder="태그를 입력하고 엔터를 누르세요"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleAddTag}
                    edge="end"
                    disabled={!newTag.trim()}
                  >
                    <AddIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Grid>
        
        {/* 
          태그 목록 표시 영역 
          - Box에 component="div"를 명시적으로 지정하여 DOM 중첩 경고 방지
          - Chip 컴포넌트는 내부적으로 div 요소를 사용하므로, 상위 요소가 span이면 경고 발생
        */}
        {tags.length > 0 && (
          <Grid item xs={12}>
            <Box component="div" sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {tags.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  onDelete={() => handleDeleteTag(tag)}
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          </Grid>
        )}
        
        <Grid item xs={12}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleCreateMemory}
            disabled={loading || !content.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
            fullWidth
          >
            {loading ? '저장 중...' : '메모리 저장'}
          </Button>
        </Grid>
      </Grid>
      
      <Snackbar
        open={success}
        autoHideDuration={6000}
        onClose={handleCloseSuccess}
        message="메모리가 성공적으로 생성되었습니다."
      />
    </Paper>
  );
};

export default CreateMemoryForm;