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
  Typography,
  CircularProgress,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  GetApp as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import api from '../utils/api';

// 내보내기 형식 정의
export enum ExportFormat {
  MARKDOWN = 'markdown',
  JSON = 'json',
  HTML = 'html',
  PDF = 'pdf',
  CODE_PACKAGE = 'code_package'
}

// 내보내기 대상 유형
export enum ExportType {
  QUESTION = 'question',
  CODE_SNIPPET = 'code_snippet',
  AGENT_LOGS = 'agent_logs'
}

// 내보내기 옵션
export interface ExportOptions {
  includeMetadata: boolean;
  includeTags: boolean;
  includeTimestamps: boolean;
  includeLlmInfo: boolean;
  codeHighlighting: boolean;
}

// 컴포넌트 props
interface ExportButtonProps {
  type: ExportType;
  id: number | string;
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

const ExportButton: React.FC<ExportButtonProps> = ({
  type,
  id,
  buttonText = '내보내기',
  buttonVariant = 'outlined',
  buttonColor = 'primary',
  buttonSize = 'medium',
  icon = true,
  tooltip = '내보내기 옵션',
  disabled = false,
  onExportStart,
  onExportComplete,
  onExportError
}) => {
  // 상태 관리
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [optionsOpen, setOptionsOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [options, setOptions] = useState<ExportOptions>({
    includeMetadata: true,
    includeTags: true,
    includeTimestamps: true,
    includeLlmInfo: true,
    codeHighlighting: true
  });

  const open = Boolean(anchorEl);

  // 메뉴 열기 핸들러
  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  // 메뉴 닫기 핸들러
  const handleClose = () => {
    setAnchorEl(null);
  };

  // 내보내기 옵션 다이얼로그 열기
  const handleOpenOptions = () => {
    handleClose();
    setOptionsOpen(true);
  };

  // 내보내기 옵션 다이얼로그 닫기
  const handleCloseOptions = () => {
    setOptionsOpen(false);
  };

  // 옵션 변경 핸들러
  const handleOptionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setOptions({
      ...options,
      [event.target.name]: event.target.checked
    });
  };

  // 내보내기 실행 함수
  const handleExport = async (format: ExportFormat) => {
    try {
      handleClose();
      setLoading(true);
      
      if (onExportStart) {
        onExportStart();
      }
      
      // API 엔드포인트 URL 생성
      const baseUrl = `${api.defaults.baseURL}/export/${type}/${id}`;
      const queryParams = new URLSearchParams({
        format,
        include_metadata: options.includeMetadata.toString(),
        include_tags: options.includeTags.toString(),
        include_timestamps: options.includeTimestamps.toString(),
        include_llm_info: options.includeLlmInfo.toString(),
        code_highlighting: options.codeHighlighting.toString()
      });
      
      const url = `${baseUrl}?${queryParams.toString()}`;
      
      // 파일 다운로드 처리
      const link = document.createElement('a');
      link.href = url;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      if (onExportComplete) {
        onExportComplete();
      }
    } catch (error) {
      console.error('내보내기 오류:', error);
      
      if (onExportError) {
        onExportError(error);
      }
    } finally {
      setLoading(false);
    }
  };

  // 내보내기 형식 목록 (유형별로 다른 옵션 제공)
  const getFormatOptions = () => {
    switch (type) {
      case ExportType.QUESTION:
        return [
          { value: ExportFormat.MARKDOWN, label: 'Markdown (.md)' },
          { value: ExportFormat.JSON, label: 'JSON (.json)' },
          { value: ExportFormat.HTML, label: 'HTML (.html)' },
          { value: ExportFormat.PDF, label: 'PDF (.pdf)' },
          { value: ExportFormat.CODE_PACKAGE, label: '코드 패키지 (.zip)' }
        ];
      case ExportType.CODE_SNIPPET:
        return [
          { value: ExportFormat.MARKDOWN, label: 'Markdown (.md)' },
          { value: ExportFormat.JSON, label: 'JSON (.json)' },
          { value: ExportFormat.CODE_PACKAGE, label: '코드 패키지 (.zip)' }
        ];
      case ExportType.AGENT_LOGS:
        return [
          { value: ExportFormat.JSON, label: 'JSON (.json)' },
          { value: ExportFormat.MARKDOWN, label: 'Markdown (.md)' },
          { value: ExportFormat.HTML, label: 'HTML (.html)' }
        ];
      default:
        return [
          { value: ExportFormat.MARKDOWN, label: 'Markdown (.md)' },
          { value: ExportFormat.JSON, label: 'JSON (.json)' }
        ];
    }
  };

  return (
    <>
      <Tooltip title={tooltip}>
        <span>
          <Button
            variant={buttonVariant}
            color={buttonColor}
            size={buttonSize}
            onClick={handleClick}
            startIcon={icon ? loading ? <CircularProgress size={20} /> : <DownloadIcon /> : undefined}
            endIcon={<ExpandMoreIcon />}
            disabled={disabled || loading}
          >
            {buttonText}
          </Button>
        </span>
      </Tooltip>
      
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
      >
        {getFormatOptions().map((format) => (
          <MenuItem 
            key={format.value} 
            onClick={() => handleExport(format.value)}
          >
            {format.label}
          </MenuItem>
        ))}
        <MenuItem onClick={handleOpenOptions}>
          <SettingsIcon fontSize="small" sx={{ mr: 1 }} />
          내보내기 옵션
        </MenuItem>
      </Menu>
      
      <Dialog open={optionsOpen} onClose={handleCloseOptions}>
        <DialogTitle>내보내기 옵션</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            내보내기에 포함할 정보를 선택하세요.
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
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseOptions}>닫기</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ExportButton;