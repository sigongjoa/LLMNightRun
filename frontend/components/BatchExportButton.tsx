import React, { useState } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  CircularProgress,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Chip,
  Box,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  List
} from '@mui/material';
import {
  GetApp as DownloadIcon,
  Settings as SettingsIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { ExportFormat, ExportOptions, ExportType } from './ExportButton';
import api from '../utils/api';

// 내보내기 항목 정의
interface ExportItem {
  type: ExportType;
  id: number | string;
  label: string;
}

// 컴포넌트 props
interface BatchExportButtonProps {
  items?: ExportItem[];
  buttonText?: string;
  buttonVariant?: 'text' | 'outlined' | 'contained';
  buttonColor?: 'primary' | 'secondary' | 'info' | 'success' | 'warning' | 'error';
  buttonSize?: 'small' | 'medium' | 'large';
  icon?: boolean;
  tooltip?: string;
  disabled?: boolean;
  onExportStart?: () => void;
  onExportComplete?: () => void;
  onExportError?: (error: any) => void;
}

const BatchExportButton: React.FC<BatchExportButtonProps> = ({
  items = [],
  buttonText = '일괄 내보내기',
  buttonVariant = 'outlined',
  buttonColor = 'primary',
  buttonSize = 'medium',
  icon = true,
  tooltip = '여러 항목을 한 번에 내보내기',
  disabled = false,
  onExportStart,
  onExportComplete,
  onExportError
}) => {
  // 상태 관리
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedItems, setSelectedItems] = useState<ExportItem[]>(items);
  const [exportFormat, setExportFormat] = useState<ExportFormat>(ExportFormat.MARKDOWN);
  const [options, setOptions] = useState<ExportOptions>({
    includeMetadata: true,
    includeTags: true,
    includeTimestamps: true,
    includeLlmInfo: true,
    codeHighlighting: true
  });

  // 다이얼로그 열기 핸들러
  const handleOpenDialog = () => {
    setDialogOpen(true);
  };

  // 다이얼로그 닫기 핸들러
  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  // 옵션 변경 핸들러
  const handleOptionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setOptions({
      ...options,
      [event.target.name]: event.target.checked
    });
  };

  // 포맷 변경 핸들러
  const handleFormatChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setExportFormat(event.target.value as ExportFormat);
  };

  // 항목 제거 핸들러
  const handleRemoveItem = (index: number) => {
    setSelectedItems(selectedItems.filter((_, i) => i !== index));
  };

  // 내보내기 실행 함수
  const handleExport = async () => {
    try {
      setLoading(true);
      
      if (onExportStart) {
        onExportStart();
      }
      
      if (selectedItems.length === 0) {
        throw new Error('내보낼 항목이 없습니다.');
      }
      
      // API 엔드포인트 URL 생성
      const url = `${api.defaults.baseURL}/export/batch`;
      
      // 쿼리 파라미터
      const queryParams = new URLSearchParams({
        format: exportFormat,
        include_metadata: options.includeMetadata.toString(),
        include_tags: options.includeTags.toString(),
        include_timestamps: options.includeTimestamps.toString(),
        include_llm_info: options.includeLlmInfo.toString(),
        code_highlighting: options.codeHighlighting.toString()
      });
      
      // 요청 데이터 준비
      const exportData = selectedItems.map(item => ({
        type: item.type,
        id: item.id
      }));
      
      // POST 요청 생성
      const response = await fetch(`${url}?${queryParams.toString()}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(exportData)
      });
      
      if (!response.ok) {
        throw new Error('내보내기 요청 실패');
      }
      
      // Blob으로 응답 받기
      const blob = await response.blob();
      
      // 파일 다운로드
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      // 파일명 추출
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'batch_export.zip';
      
      if (contentDisposition) {
        const matches = /filename="([^"]*)"/.exec(contentDisposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }
      
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      // 성공 후 다이얼로그 닫기
      handleCloseDialog();
      
      if (onExportComplete) {
        onExportComplete();
      }
    } catch (error) {
      console.error('일괄 내보내기 오류:', error);
      
      if (onExportError) {
        onExportError(error);
      }
    } finally {
      setLoading(false);
    }
  };

  // 내보내기 형식 옵션
  const formatOptions = [
    { value: ExportFormat.MARKDOWN, label: 'Markdown (.md)' },
    { value: ExportFormat.JSON, label: 'JSON (.json)' },
    { value: ExportFormat.HTML, label: 'HTML (.html)' },
    { value: ExportFormat.PDF, label: 'PDF (.pdf)' }
  ];

  return (
    <>
      <Tooltip title={tooltip}>
        <span>
          <Button
            variant={buttonVariant}
            color={buttonColor}
            size={buttonSize}
            onClick={handleOpenDialog}
            startIcon={icon ? loading ? <CircularProgress size={20} /> : <DownloadIcon /> : undefined}
            disabled={disabled || loading || selectedItems.length === 0}
          >
            {buttonText}
          </Button>
        </span>
      </Tooltip>
      
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>일괄 내보내기</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            선택한 항목을 일괄적으로 내보냅니다. 모든 항목은 하나의 Zip 파일로 압축됩니다.
          </Typography>
          
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              내보낼 항목 ({selectedItems.length})
            </Typography>
            
            {selectedItems.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                내보낼 항목이 없습니다.
              </Typography>
            ) : (
              <List dense>
                {selectedItems.map((item, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={item.label}
                      secondary={`유형: ${item.type}, ID: ${item.id}`}
                    />
                    <ListItemSecondaryAction>
                      <IconButton edge="end" onClick={() => handleRemoveItem(index)}>
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
          
          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth variant="outlined">
              <InputLabel>내보내기 형식</InputLabel>
              <Select
                value={exportFormat}
                onChange={handleFormatChange}
                label="내보내기 형식"
              >
                {formatOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
          
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              내보내기 옵션
            </Typography>
            
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={options.includeMetadata}
                    onChange={handleOptionChange}
                    name="includeMetadata"
                  />
                }
                label="메타데이터 포함"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={options.includeTags}
                    onChange={handleOptionChange}
                    name="includeTags"
                  />
                }
                label="태그 포함"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={options.includeTimestamps}
                    onChange={handleOptionChange}
                    name="includeTimestamps"
                  />
                }
                label="타임스탬프 포함"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={options.includeLlmInfo}
                    onChange={handleOptionChange}
                    name="includeLlmInfo"
                  />
                }
                label="LLM 정보 포함"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={options.codeHighlighting}
                    onChange={handleOptionChange}
                    name="codeHighlighting"
                  />
                }
                label="코드 하이라이팅"
              />
            </FormGroup>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>취소</Button>
          <Button
            onClick={handleExport}
            color="primary"
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <DownloadIcon />}
            disabled={loading || selectedItems.length === 0}
          >
            {loading ? '내보내는 중...' : '내보내기'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
export default BatchExportButton;