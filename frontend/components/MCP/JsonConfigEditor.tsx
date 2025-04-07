import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  CircularProgress,
  Alert
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useMcp } from '../../contexts/McpContext';
import { MCPConfig } from '../../utils/mcp/api';

interface JsonConfigEditorProps {
  open: boolean;
  onClose: () => void;
}

export const JsonConfigEditor: React.FC<JsonConfigEditorProps> = ({ open, onClose }) => {
  const { getConfig, updateConfig, refreshServers } = useMcp();
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [jsonValue, setJsonValue] = useState<string>('');
  const [syntaxError, setSyntaxError] = useState<string | null>(null);

  // 에디터 스타일
  const editorStyle: React.CSSProperties = {
    width: '100%',
    height: '400px',
    fontFamily: 'monospace',
    fontSize: '14px',
    padding: '10px',
    border: syntaxError ? '1px solid red' : '1px solid #ccc',
    borderRadius: '4px',
    resize: 'none',
    overflowY: 'auto',
    backgroundColor: '#f5f5f5',
    lineHeight: '1.5'
  };

  // 초기 설정 로드
  useEffect(() => {
    const loadConfig = async () => {
      if (!open) return;
      
      setLoading(true);
      setError(null);
      setSyntaxError(null);
      
      try {
        const config = await getConfig();
        setJsonValue(JSON.stringify(config, null, 2));
      } catch (err) {
        console.error('Error loading config:', err);
        setError('설정을 불러오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    loadConfig();
  }, [open, getConfig]);

  // JSON 유효성 검사
  const validateJson = (json: string): boolean => {
    try {
      JSON.parse(json);
      setSyntaxError(null);
      return true;
    } catch (err: any) {
      setSyntaxError(err.message || '유효하지 않은 JSON입니다.');
      return false;
    }
  };

  // 텍스트 변경 핸들러
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setJsonValue(value);
    validateJson(value);
  };

  // 저장 핸들러
  const handleSave = async () => {
    if (!validateJson(jsonValue)) {
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const parsedConfig = JSON.parse(jsonValue) as MCPConfig;
      await updateConfig(parsedConfig);
      await refreshServers();
      onClose();
    } catch (err) {
      console.error('Error saving config:', err);
      setError('설정을 저장하는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">MCP 설정 JSON 직접 편집</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {loading && (
          <Box display="flex" justifyContent="center" my={3}>
            <CircularProgress />
          </Box>
        )}
        
        {!loading && (
          <>
            <Alert severity="info" sx={{ mb: 2 }}>
              JSON 형식으로 MCP 서버 설정을 직접 편집하세요. 외부 MCP 서버를 추가하거나 기존 서버를 수정할 수 있습니다.
            </Alert>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {syntaxError && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                JSON 구문 오류: {syntaxError}
              </Alert>
            )}
            
            <textarea
              value={jsonValue}
              onChange={handleChange}
              style={editorStyle}
              spellCheck={false}
            />
            
            <Box mt={2}>
              <Typography variant="subtitle2" gutterBottom>
                JSON 예시:
              </Typography>
              <pre style={{ 
                backgroundColor: '#f0f0f0', 
                padding: '10px', 
                borderRadius: '4px',
                fontSize: '12px',
                overflow: 'auto'
              }}>
{`{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here"
      }
    },
    "custom-server": {
      "command": "/path/to/your/custom-server",
      "args": ["--option", "value"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}`}
              </pre>
            </Box>
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          취소
        </Button>
        <Button 
          onClick={handleSave} 
          variant="contained" 
          color="primary" 
          disabled={loading || !!syntaxError}
        >
          {loading ? <CircularProgress size={24} /> : '저장'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
