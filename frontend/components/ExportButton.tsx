import React, { useState } from 'react';
import {
  Button,
  Menu,
  MenuItem,
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
  Alert
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { ExportFormat, ExportOptions } from '../types';
import { exportQuestion, exportCodeSnippet, exportAgentLogs } from '../utils/api';

interface ExportButtonProps {
  type: 'question' | 'code_snippet' | 'agent_logs';
  id: number | string;
  fileName?: string;
  buttonText?: string;
  variant?: 'text' | 'outlined' | 'contained';
  color?: 'primary' | 'secondary' | 'inherit' | 'success' | 'error' | 'info' | 'warning';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  disabled?: boolean;
  tooltip?: string;
}

const ExportButton: React.FC<ExportButtonProps> = ({
  type,
  id,
  fileName,
  buttonText = '내보내기',
  variant = 'outlined',
  color = 'primary',
  size = 'medium',
  fullWidth = false,
  disabled = false,
  tooltip
}) => {
  // 메뉴 상태
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  
  // 다이얼로그 상태
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>(ExportFormat.MARKDOWN);
  
  // 내보내기 옵션
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    includeMetadata: true,
    includeTags: true,
    includeTimestamps: true,
    includeLlmInfo: true,
    codeHighlighting: true
  });
  
  // 로딩 및 알림 상태
  const [loading, setLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  
  // 메뉴 열기 처리
  const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setMenuAnchorEl(event.currentTarget);
  };
  
  // 메뉴 닫기 처리
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };
  
  // 내보내기 형식 선택 처리
  const handleFormatSelect = (format: ExportFormat) => {
    handleMenuClose();
    setSelectedFormat(format);
    setDialogOpen(true);
  };
  
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
  
  // 내보내기 실행 처리
  const handleExport = async () => {
    setLoading(true);
    try {
      let data: Blob;
      
      // 타입에 따라 다른 API 호출
      if (type === 'question') {
        data = await exportQuestion(Number(id), selectedFormat, exportOptions);
      } else if (type === 'code_snippet') {
        data = await exportCodeSnippet(Number(id), selectedFormat, exportOptions);
      } else { // agent_logs
        data = await exportAgentLogs(id.toString(), selectedFormat, exportOptions);
      }
      
      // 파일명 생성
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
      let defaultFileName = `${type}_${id}_${timestamp}`;
      
      // 확장자 결정
      let extension = '.txt';
      switch (selectedFormat) {
        case ExportFormat.MARKDOWN:
          extension = '.md';
          break;
        case ExportFormat.JSON:
          extension = '.json';
          break;
        case ExportFormat.HTML:
          extension = '.html';
          break;
        case ExportFormat.PDF:
          extension = '.pdf';
          break;
        case ExportFormat.CODE_PACKAGE:
          extension = '.zip';
          break;
      }
      
      // 다운로드 링크 생성 및 클릭
      const url = window.URL.createObjectURL(data);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName || `${defaultFileName}${extension}`);
      document.body.appendChild(link);
      link.click();
      
      // 정리
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
      
      // 성공 메시지 표시
      setSnackbarMessage('파일이 성공적으로 내보내졌습니다');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      
      // 다이얼로그 닫기
      setDialogOpen(false);
    } catch (error) {
      console.error('내보내기 오류:', error);
      setSnackbarMessage(`내보내기 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant={variant}
        color={color}
        size={size}
        fullWidth={fullWidth}
        disabled={disabled}
        onClick={handleMenuClick}
        title={tooltip}
        startIcon={<DownloadIcon />}
      >
        {buttonText}
      </Button>
      
      {/* 내보내기 형식 선택 메뉴 */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleFormatSelect(ExportFormat.MARKDOWN)}>Markdown (.md)</MenuItem>
        <MenuItem onClick={() => handleFormatSelect(ExportFormat.JSON)}>JSON (.json)</MenuItem>
        <MenuItem onClick={() => handleFormatSelect(ExportFormat.HTML)}>HTML (.html)</MenuItem>
        <MenuItem onClick={() => handleFormatSelect(ExportFormat.PDF)}>PDF (.pdf)</MenuItem>
        {(type === 'question' || type === 'code_snippet') && (
          <MenuItem onClick={() => handleFormatSelect(ExportFormat.CODE_PACKAGE)}>코드 패키지 (.zip)</MenuItem>
        )}
      </Menu>
      
      {/* 내보내기 옵션 다이얼로그 */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>내보내기 옵션</DialogTitle>
        <DialogContent>
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
              {(type === 'question' || type === 'code_snippet') && (
                <FormControlLabel
                  value={ExportFormat.CODE_PACKAGE}
                  control={<Radio />}
                  label="코드 패키지 (.zip)"
                />
              )}
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
          <Button onClick={() => setDialogOpen(false)} color="inherit">
            취소
          </Button>
          <Button
            onClick={handleExport}
            color="primary"
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FileDownloadIcon />}
            disabled={loading}
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

export default ExportButton;