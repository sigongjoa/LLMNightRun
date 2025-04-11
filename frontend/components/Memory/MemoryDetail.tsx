import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Divider,
  Chip,
  Button,
  IconButton,
  TextField,
  Grid,
  Alert,
  Card,
  CardContent,
  CardActions,
  List,
  ListItem,
  ListItemText,
  useTheme,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  AccessTime as TimeIcon,
  Label as TagIcon,
  Category as CategoryIcon,
  IntegrationInstructions as PromptIcon,
  Psychology as LLMIcon
} from '@mui/icons-material';
import { Memory, MemoryType } from './MemoryList';
import axios from 'axios';
import { API_BASE_URL } from '../../utils/constants';

interface MemoryDetailProps {
  memory: Memory | null;
  onRefresh?: () => void;
}

const MemoryDetail: React.FC<MemoryDetailProps> = ({ memory, onRefresh }) => {
  const theme = useTheme();
  const [editing, setEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  // 메모리가 없는 경우 안내 표시
  if (!memory) {
    return (
      <Paper sx={{ p: 3, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          왼쪽에서 메모리를 선택하여 상세 정보를 확인하세요.
        </Typography>
      </Paper>
    );
  }

  // 수정 모드 시작
  const handleStartEdit = () => {
    setEditedContent(memory.content);
    setEditing(true);
    setError(null);
    setSuccess(null);
  };

  // 수정 취소
  const handleCancelEdit = () => {
    setEditing(false);
    setError(null);
  };

  // 수정 저장
  const handleSaveEdit = async () => {
    try {
      // 현재는 전체 메모리를 다시 저장하는 방식 (API가 부분 업데이트를 지원하면 수정 필요)
      const updatedMemory = {
        ...memory,
        content: editedContent
      };
      
      await axios.post(`${API_BASE_URL}/memory/add`, updatedMemory, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });
      
      setSuccess('메모리가 성공적으로 업데이트되었습니다.');
      setEditing(false);
      
      // 메모리 목록 새로고침
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      console.error('메모리 업데이트 실패:', err);
      setError('메모리 업데이트 중 오류가 발생했습니다.');
    }
  };

  // 클립보드에 복사
  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(memory.content);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  // 날짜 포맷팅
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  // 메모리 타입에 따른 배경색
  const getBackgroundColorByType = (type: MemoryType) => {
    switch (type) {
      case MemoryType.CONVERSATION:
        return theme.palette.primary.light;
      case MemoryType.EXPERIMENT:
        return theme.palette.secondary.light;
      case MemoryType.CODE:
        return theme.palette.success.light;
      case MemoryType.RESULT:
        return theme.palette.warning.light;
      case MemoryType.NOTE:
        return theme.palette.info.light;
      default:
        return theme.palette.grey[200];
    }
  };

  // 메타데이터 렌더링
  const renderMetadata = () => {
    if (!memory.metadata || Object.keys(memory.metadata).length === 0) {
      return (
        <Typography variant="body2" color="text.secondary">
          메타데이터가 없습니다.
        </Typography>
      );
    }

    const filteredMetadata = { ...memory.metadata };
    // tags는 별도로 표시하므로 제외
    delete filteredMetadata.tags;

    return (
      <List dense disablePadding>
        {Object.entries(filteredMetadata).map(([key, value]) => (
          <ListItem key={key} disablePadding sx={{ py: 0.5 }}>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" fontWeight="bold" color="text.secondary">
                    {key}
                  </Typography>
                  <Typography variant="body2">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </Typography>
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
    );
  };

  // 특별 메타데이터 렌더링 (실험 메모리용)
  const renderExperimentDetails = () => {
    if (memory.type !== MemoryType.EXPERIMENT) return null;

    const { experiment_id, model_name, prompt, response, metrics } = memory.metadata;
    
    return (
      <Box sx={{ mt: 2 }}>
        {experiment_id && (
          <Typography variant="subtitle2" gutterBottom>
            <strong>실험 ID:</strong> {experiment_id}
          </Typography>
        )}
        
        {model_name && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <LLMIcon fontSize="small" sx={{ mr: 1 }} />
            <Typography variant="body2">
              <strong>모델:</strong> {model_name}
            </Typography>
          </Box>
        )}
        
        {metrics && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>측정 지표</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List dense disablePadding>
                {Object.entries(metrics).map(([key, value]) => (
                  <ListItem key={key} disablePadding>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" fontWeight="bold">
                            {key}
                          </Typography>
                          <Typography variant="body2">
                            {typeof value === 'number' ? value.toFixed(4) : String(value)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
        )}
        
        {prompt && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <PromptIcon fontSize="small" sx={{ mr: 1 }} />
                <Typography>프롬프트</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {prompt}
                </Typography>
              </Paper>
            </AccordionDetails>
          </Accordion>
        )}
        
        {response && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>응답</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {response}
                </Typography>
              </Paper>
            </AccordionDetails>
          </Accordion>
        )}
      </Box>
    );
  };

  return (
    <Box>
      {/* 메모리 헤더 */}
      <Card 
        sx={{ 
          mb: 3, 
          borderTop: 4, 
          borderColor: getBackgroundColorByType(memory.type),
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Chip
                label={memory.type}
                size="small"
                color="primary"
                sx={{ mb: 1 }}
              />
              
              {/* 
                타임스탬프 표시 영역 
                - Box component="div"와 Typography component="span"을 사용하여 DOM 중첩 경고 방지
                - MUI에서 Typography는 기본적으로 p 태그로 렌더링되는데, 이 내부에 div가 들어가면 경고 발생
              */}
              <Box component="div" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TimeIcon fontSize="small" sx={{ mr: 0.5 }} />
                <Typography variant="body2" component="span" color="text.secondary">
                  {formatDate(memory.timestamp)}
                </Typography>
              </Box>
              
              {memory.id && (
                <Typography variant="caption" color="text.secondary">
                  ID: {memory.id}
                </Typography>
              )}
            </Box>
            
            <Box>
              <Tooltip title="복사">
                <IconButton onClick={handleCopyToClipboard}>
                  <CopyIcon color={copySuccess ? "success" : "inherit"} />
                </IconButton>
              </Tooltip>
              
              {!editing ? (
                <Tooltip title="수정">
                  <IconButton onClick={handleStartEdit}>
                    <EditIcon />
                  </IconButton>
                </Tooltip>
              ) : (
                <>
                  <Tooltip title="저장">
                    <IconButton onClick={handleSaveEdit} color="primary">
                      <SaveIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="취소">
                    <IconButton onClick={handleCancelEdit} color="error">
                      <CancelIcon />
                    </IconButton>
                  </Tooltip>
                </>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* 오류/성공 메시지 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* 메모리 내용 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          메모리 내용
        </Typography>
        
        <Divider sx={{ mb: 2 }} />
        
        {editing ? (
          <TextField
            fullWidth
            multiline
            minRows={4}
            maxRows={12}
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            variant="outlined"
            sx={{ mb: 2 }}
          />
        ) : (
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {memory.content}
          </Typography>
        )}
        
        {/* 태그 */}
        {/* 
          태그 표시 영역 
          - 중첩된 Box 컴포넌트에 모두 component="div"를 명시하여 DOM 중첩 경고 방지
          - Chip 컴포넌트는 내부적으로 div를 사용하므로 Box에서 div로 명시적 선언 필요
        */}
        {memory.metadata && memory.metadata.tags && memory.metadata.tags.length > 0 && (
          <Box component="div" sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
            <TagIcon fontSize="small" sx={{ mr: 1 }} color="action" />
            <Box component="div">
              {memory.metadata.tags.map((tag: string) => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ mr: 0.5, mb: 0.5 }}
                />
              ))}
            </Box>
          </Box>
        )}
      </Paper>

      {/* 실험 세부 정보 (실험 메모리인 경우) */}
      {renderExperimentDetails()}

      {/* 메타데이터 */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          메타데이터
        </Typography>
        
        <Divider sx={{ mb: 2 }} />
        
        {renderMetadata()}
      </Paper>
    </Box>
  );
};

export default MemoryDetail;