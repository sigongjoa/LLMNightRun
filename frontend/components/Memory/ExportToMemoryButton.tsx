import React, { useState } from 'react';
import { 
  Button, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Box,
  Typography,
  Chip,
  IconButton,
  InputAdornment,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Save as SaveIcon,
  Memory as MemoryIcon,
  Add as AddIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../../utils/constants';
import { MemoryType } from './MemoryList';
import { ChatMessage } from '../Chat/ChatInterface';

interface ExportToMemoryButtonProps {
  messages: ChatMessage[];
  buttonText?: string;
  buttonVariant?: 'text' | 'outlined' | 'contained';
  buttonSize?: 'small' | 'medium' | 'large';
  buttonColor?: 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
  onMemoryExported?: () => void;
  sx?: any; // MUI SX Props
}

const ExportToMemoryButton: React.FC<ExportToMemoryButtonProps> = ({
  messages,
  buttonText = '대화 내보내기',
  buttonVariant = 'contained',
  buttonSize = 'medium',
  buttonColor = 'primary',
  onMemoryExported,
  sx
}) => {
  // 상태 관리
  const [open, setOpen] = useState(false);
  const [memoryType, setMemoryType] = useState<MemoryType>(MemoryType.CONVERSATION);
  const [summaryText, setSummaryText] = useState('');
  const [tags, setTags] = useState<string[]>(['대화', '채팅']);
  const [newTag, setNewTag] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  // 메시지 생성
  const formatMessages = () => {
    return messages.map(msg => 
      `${msg.role.toUpperCase()}: ${msg.content}`
    ).join('\n\n');
  };
  
  // 대화 요약 생성 (첫 50자만 사용)
  const generateSummary = () => {
    if (messages.length === 0) return '';
    
    // 사용자 메시지 중 첫 번째 메시지 텍스트 사용
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length > 0) {
      const firstUserMsg = userMessages[0].content;
      // 첫 50자 추출 (또는 전체 메시지가 더 짧은 경우)
      return firstUserMsg.length > 50 
        ? `${firstUserMsg.substring(0, 50)}...` 
        : firstUserMsg;
    }
    
    return '대화 내보내기';
  };
  
  // 다이얼로그 열기
  const handleOpen = () => {
    setSummaryText(generateSummary());
    setOpen(true);
  };
  
  // 다이얼로그 닫기
  const handleClose = () => {
    setOpen(false);
    setError(null);
  };
  
  // 새 태그 추가
  const handleAddTag = () => {
    if (!newTag.trim()) return;
    
    // 중복 태그 방지
    if (!tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
    }
    
    setNewTag('');
  };
  
  // 태그 삭제
  const handleDeleteTag = (tagToDelete: string) => {
    setTags(tags.filter(tag => tag !== tagToDelete));
  };
  
  // 엔터키로 태그 추가
  const handleTagKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };
  
  // 내보내기 실행
  const handleExport = async () => {
    if (messages.length === 0) {
      setError('내보낼 대화가 없습니다.');
      return;
    }
    
    if (!summaryText.trim()) {
      setError('요약 텍스트를 입력해주세요.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // 메모리 생성
      const memory = {
        content: formatMessages(),
        type: memoryType,
        metadata: {
          tags: tags,
          summary: summaryText,
          message_count: messages.length,
          exported_at: new Date().toISOString(),
          from_chat: true
        }
      };
      
      // API 호출
      await axios.post(`${API_BASE_URL}/memory/add`, memory, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });
      
      // 성공 처리
      setSuccess(true);
      setOpen(false);
      
      // 콜백 호출
      if (onMemoryExported) {
        onMemoryExported();
      }
    } catch (err) {
      console.error('메모리 내보내기 실패:', err);
      setError('메모리로 내보내기에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  // 성공 알림 닫기
  const handleCloseSuccess = () => {
    setSuccess(false);
  };
  
  return (
    <>
      <Button
        variant={buttonVariant}
        color={buttonColor}
        size={buttonSize}
        startIcon={<MemoryIcon />}
        onClick={handleOpen}
        disabled={messages.length === 0}
        sx={sx}
      >
        {buttonText}
      </Button>
      
      {/* 내보내기 다이얼로그 */}
      <Dialog 
        open={open} 
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>대화를 메모리로 내보내기</DialogTitle>
        
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Typography variant="body2" color="text.secondary" paragraph>
            현재 대화를 벡터 메모리 시스템으로 내보내면 LLM이 나중에 관련 내용을 기억하고 참조할 수 있습니다.
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            <TextField
              label="요약 텍스트"
              fullWidth
              value={summaryText}
              onChange={(e) => setSummaryText(e.target.value)}
              placeholder="이 대화의 요약 또는 키워드"
              required
              margin="normal"
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel id="memory-type-label">메모리 유형</InputLabel>
              <Select
                labelId="memory-type-label"
                value={memoryType}
                label="메모리 유형"
                onChange={(e) => setMemoryType(e.target.value as MemoryType)}
              >
                <MenuItem value={MemoryType.CONVERSATION}>대화</MenuItem>
                <MenuItem value={MemoryType.NOTE}>노트</MenuItem>
                <MenuItem value={MemoryType.CODE}>코드</MenuItem>
                <MenuItem value={MemoryType.RESULT}>결과</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="태그 추가"
              fullWidth
              margin="normal"
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
            
            {/* 태그 목록 */}
            <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap' }}>
              {tags.map(tag => (
                <Chip
                  key={tag}
                  label={tag}
                  onDelete={() => handleDeleteTag(tag)}
                  color="primary"
                  variant="outlined"
                  size="small"
                  sx={{ mr: 0.5, mb: 0.5 }}
                />
              ))}
            </Box>
            
            {/* 미리보기 */}
            <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
              내보낼 대화 내용
            </Typography>
            
            <Box 
              sx={{ 
                p: 2, 
                bgcolor: 'background.default',
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
                maxHeight: '200px',
                overflow: 'auto',
                fontSize: '0.9rem',
                fontFamily: 'monospace'
              }}
            >
              <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', m: 0 }}>
                {formatMessages()}
              </Typography>
            </Box>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button 
            onClick={handleClose}
            startIcon={<CancelIcon />}
          >
            취소
          </Button>
          <Button 
            onClick={handleExport}
            color="primary" 
            variant="contained"
            startIcon={loading ? null : <SaveIcon />}
            disabled={loading || !summaryText.trim()}
          >
            {loading ? '처리 중...' : '메모리로 내보내기'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 성공 알림 */}
      <Snackbar
        open={success}
        autoHideDuration={6000}
        onClose={handleCloseSuccess}
        message="대화가 메모리로 성공적으로 내보내졌습니다."
      />
    </>
  );
};

export default ExportToMemoryButton;