import React, { useState } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Checkbox,
  FormGroup,
  Radio,
  RadioGroup,
  FormControl,
  FormLabel,
  CircularProgress,
  Snackbar,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton
} from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DeleteIcon from '@mui/icons-material/Delete';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import CodeIcon from '@mui/icons-material/Code';
import SmartToyIcon from '@mui/icons-material/SmartToy';

import { ExportFormat, ExportOptions } from '../types';
import { exportBatch } from '../utils/api';

export interface BatchExportItem {
  type: 'question' | 'code_snippet' | 'agent_logs';
  id: number | string;
  title: string;
}

interface BatchExportDialogProps {
  open: boolean;
  items: BatchExportItem[];
  onClose: () => void;
  onSuccess?: () => void;
}

const BatchExportDialog: React.FC<BatchExportDialogProps> = ({
  open,
  items,
  onClose,
  onSuccess
}) => {
  // 다이얼로그 상태
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>(ExportFormat.MARKDOWN);
  
  // 내보내기 옵션
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    includeMetadata: true,
    includeTags: true,
    includeTimestamps: true,
    includeLlmInfo: true,
    codeHighlighting: true
  });
  
  // 선택된 항목
  const [selectedItems, setSelectedItems] = useState<BatchExportItem[]>(items);
  
  // 로딩 및 알림 상태
  const [loading, setLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  
  // 옵션 변경 처리
  const handleOptionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setExportOptions({
      ...exportOptions,
      [event.target.name]: event.target.checked
    });
  };
  
  // 형식 변경 처리
  const handleFormatChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFormat(event.target.value as ExportFormat);
  };

  // 항목 제거 처리
  const handleRemoveItem = (index: number) => {
    setSelectedItems(selectedItems.filter((_, i) => i !== index));
  };
  
  // 내보내기 실행 처리
  const handleExport = async () => {
    if (selectedItems.length === 0) {
      setSnackbarMessage('내보낼 항목이 없습니다.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }
    
    setLoading(true);
    try {
      // API 요청을 위한 형식으로 아이템 변환
      const itemsForApi = selectedItems.map(item => ({
        type: item.type,
        id: item.id
      }));
      
      // 일괄 내보내기 API 호출
      const data = await exportBatch(itemsForApi, selectedFormat, exportOptions);
      
      // 파일명 생성
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
      const filename = `batch_export_${timestamp}.zip`;
      
      // 다운로드 링크 생성 및 클릭
      const url = window.URL.createObjectURL(data);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      // 정리
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
      
      // 성공 메시지 표시
      setSnackbarMessage('파일이 성공적으로 내보내졌습니다');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      
      // 성공 콜백 호출
      if (onSuccess) onSuccess();
      
      // 다이얼로그 닫기
      onClose();
    } catch (error) {
      console.error('일괄 내보내기 오류:', error);
      setSnackbarMessage(`내보내기 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  // 항목 유형에 따른 아이콘 반환
  const getItemIcon = (type: string) => {
    switch (type) {
      case 'question':
        return <QuestionAnswerIcon />;
      case 'code_snippet':
        return <CodeIcon />;
      case 'agent_logs':
        return <SmartToyIcon />;
      default:
        return <QuestionAnswerIcon />;
    }
  };

  return (
    <>
      <Dialog 
        open={open} 
        onClose={onClose}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>일괄 내보내기</DialogTitle>
        <DialogContent>
          <List sx={{ bgcolor: 'background.paper', mb: 2 }}>
            {selectedItems.length > 0 ? (
              selectedItems.map((item, index) => (
                <ListItem
                  key={`${item.type}-${item.id}`}
                  secondaryAction={
                    <IconButton 
                      edge="end" 
                      aria-label="delete" 
                      onClick={() => handleRemoveItem(index)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  }
                >
                  <ListItemIcon>
                    {getItemIcon(item.type)}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.title}
                    secondary={`${item.type === 'question' ? '질문' : 
                               item.type === 'code_snippet' ? '코드 스니펫' : 
                               '에이전트 로그'} #${item.id}`}
                  />
                </ListItem>
              ))
            ) : (
              <ListItem>
                <ListItemText primary="내보낼 항목이 없습니다." />
              </ListItem>
            )}
          </List>
          
          <FormControl component="fieldset" sx={{ mt: 2 }}>
            <FormLabel component="legend">형식</FormLabel>
            <RadioGroup
              name="format"
              value={selectedFormat}
              onChange={handleFormatChange}
            >
              <FormControlLabel
                value={ExportFormat.MARKDOWN}
                control={<Radio />}
                label="Markdown (.md)"
              />
              <FormControlLabel
                value={ExportFormat.JSON}
                control={<Radio />}
                label="JSON (.json)"
              />
              <FormControlLabel
                value={ExportFormat.HTML}
                control={<Radio />}
                label="HTML (.html)"
              />
              <FormControlLabel
                value={ExportFormat.PDF}
                control={<Radio />}
                label="PDF (.pdf)"
              />
              <FormControlLabel
                value={ExportFormat.CODE_PACKAGE}
                control={<Radio />}
                label="코드 패키지 (.zip)"
              />
            </RadioGroup>
          </FormControl>
          
          <FormGroup sx={{ mt: 3 }}>
            <FormLabel component="legend">옵션</FormLabel>
            <FormControlLabel
              control={
                <Checkbox
                  checked={exportOptions.includeMetadata}
                  onChange={handleOptionChange}
                  name="includeMetadata"
                />
              }
              label="메타데이터 포함"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={exportOptions.includeTags}
                  onChange={handleOptionChange}
                  name="includeTags"
                />
              }
              label="태그 포함"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={exportOptions.includeTimestamps}
                  onChange={handleOptionChange}
                  name="includeTimestamps"
                />
              }
              label="타임스탬프 포함"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={exportOptions.includeLlmInfo}
                  onChange={handleOptionChange}
                  name="includeLlmInfo"
                />
              }
              label="LLM 정보 포함"
            />
            {(selectedFormat === ExportFormat.MARKDOWN || selectedFormat === ExportFormat.HTML) && (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={exportOptions.codeHighlighting}
                    onChange={handleOptionChange}
                    name="codeHighlighting"
                  />
                }
                label="코드 하이라이팅"
              />
            )}
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} color="inherit">
            취소
          </Button>
          <Button
            onClick={handleExport}
            color="primary"
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FileDownloadIcon />}
            disabled={loading || selectedItems.length === 0}
          >
            {loading ? '처리 중...' : '내보내기'}
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
    </>
  );
};

export default BatchExportDialog;