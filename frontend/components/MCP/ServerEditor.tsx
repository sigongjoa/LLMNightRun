import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  IconButton,
  Typography,
  Box,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Paper,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useMcp } from '../../contexts/McpContext';
import { ServerConfig } from '../../utils/mcp/api';

interface ServerEditorProps {
  open: boolean;
  serverId?: string;
  onClose: () => void;
}

const COMMON_MCP_SERVERS = [
  {
    name: 'Memory Server',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-memory'],
    env: {}
  },
  {
    name: 'Filesystem Server',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/directory'],
    env: {}
  },
  {
    name: 'GitHub Server',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-github'],
    env: { 'GITHUB_PERSONAL_ACCESS_TOKEN': '<YOUR_TOKEN>' }
  },
  {
    name: 'PostgreSQL Server',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-postgres', 'postgres://username:password@localhost:5432/database'],
    env: {}
  },
  {
    name: 'Fetch Server',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-fetch'],
    env: {}
  },
  {
    name: 'Git Server',
    command: 'npx', 
    args: ['-y', '@modelcontextprotocol/server-git', '/path/to/repo'],
    env: {}
  }
];

export const ServerEditor: React.FC<ServerEditorProps> = ({ open, serverId, onClose }) => {
  const { getServerStatus, updateServer } = useMcp();
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const [id, setId] = useState<string>('');
  const [command, setCommand] = useState<string>('npx');
  const [args, setArgs] = useState<string[]>(['-y', '']);
  const [env, setEnv] = useState<Record<string, string>>({});
  
  const [newArgValue, setNewArgValue] = useState<string>('');
  const [newEnvKey, setNewEnvKey] = useState<string>('');
  const [newEnvValue, setNewEnvValue] = useState<string>('');
  
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  // Load server data if editing
  useEffect(() => {
    const loadServerData = async () => {
      if (!serverId) {
        setId('');
        setCommand('npx');
        setArgs(['-y', '']);
        setEnv({});
        return;
      }
      
      setLoading(true);
      setError(null);
      
      try {
        const serverStatus = await getServerStatus(serverId);
        if (serverStatus.exists && serverStatus.config) {
          setId(serverId);
          setCommand(serverStatus.config.command || 'npx');
          setArgs(serverStatus.config.args || ['-y', '']);
          setEnv(serverStatus.config.env || {});
        }
      } catch (err) {
        console.error('Error loading server data:', err);
        setError('서버 정보를 불러오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    if (open) {
      loadServerData();
    }
  }, [serverId, open, getServerStatus]);
  
  const handleSave = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (!id.trim()) {
        setError('서버 ID는 필수입니다.');
        setLoading(false);
        return;
      }
      
      const config: ServerConfig = {
        command,
        args,
        env
      };
      
      await updateServer(id, config);
      onClose();
    } catch (err) {
      console.error('Error saving server:', err);
      setError('서버 저장 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleAddArg = () => {
    if (newArgValue.trim()) {
      setArgs([...args, newArgValue.trim()]);
      setNewArgValue('');
    }
  };
  
  const handleRemoveArg = (index: number) => {
    setArgs(args.filter((_, i) => i !== index));
  };
  
  const handleAddEnv = () => {
    if (newEnvKey.trim() && newEnvValue.trim()) {
      setEnv({
        ...env,
        [newEnvKey.trim()]: newEnvValue.trim()
      });
      setNewEnvKey('');
      setNewEnvValue('');
    }
  };
  
  const handleRemoveEnv = (key: string) => {
    const newEnv = { ...env };
    delete newEnv[key];
    setEnv(newEnv);
  };
  
  const applyTemplate = (templateIndex: number) => {
    const template = COMMON_MCP_SERVERS[templateIndex];
    setCommand(template.command);
    setArgs(template.args);
    setEnv(template.env);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {serverId ? `MCP 서버 수정: ${serverId}` : 'MCP 서버 추가'}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {loading ? (
          <Box display="flex" justifyContent="center" my={3}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                <Typography variant="subtitle2" gutterBottom>
                  사전 정의된 템플릿
                </Typography>
                <FormControl fullWidth size="small">
                  <InputLabel id="template-select-label">템플릿 선택</InputLabel>
                  <Select
                    labelId="template-select-label"
                    value={selectedTemplate}
                    label="템플릿 선택"
                    onChange={(e) => {
                      setSelectedTemplate(e.target.value);
                      if (e.target.value !== '') {
                        applyTemplate(parseInt(e.target.value));
                      }
                    }}
                  >
                    <MenuItem value="">
                      <em>선택 안함</em>
                    </MenuItem>
                    {COMMON_MCP_SERVERS.map((server, index) => (
                      <MenuItem key={index} value={index.toString()}>
                        {server.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Paper>
            </Grid>
          
            <Grid item xs={12}>
              <TextField
                label="서버 ID"
                fullWidth
                value={id}
                onChange={(e) => setId(e.target.value)}
                disabled={!!serverId}
                helperText={serverId ? "기존 서버의 ID는 변경할 수 없습니다." : "고유한 서버 식별자 (예: github, filesystem, memory)"}
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="명령어"
                fullWidth
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                helperText="실행할 명령어 (대부분 'npx')"
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                인자 목록
              </Typography>
              <Box sx={{ mb: 2 }}>
                {args.map((arg, index) => (
                  <Chip
                    key={index}
                    label={arg}
                    onDelete={() => handleRemoveArg(index)}
                    sx={{ m: 0.5 }}
                  />
                ))}
              </Box>
              <Box display="flex" gap={1}>
                <TextField
                  label="새 인자"
                  value={newArgValue}
                  onChange={(e) => setNewArgValue(e.target.value)}
                  size="small"
                  fullWidth
                />
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={handleAddArg}
                  disabled={!newArgValue.trim()}
                >
                  추가
                </Button>
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                환경 변수
              </Typography>
              <Box sx={{ mb: 2 }}>
                {Object.entries(env).map(([key, value]) => (
                  <Chip
                    key={key}
                    label={`${key}=${value}`}
                    onDelete={() => handleRemoveEnv(key)}
                    sx={{ m: 0.5 }}
                  />
                ))}
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={5}>
                  <TextField
                    label="변수명"
                    value={newEnvKey}
                    onChange={(e) => setNewEnvKey(e.target.value)}
                    size="small"
                    fullWidth
                  />
                </Grid>
                <Grid item xs={5}>
                  <TextField
                    label="값"
                    value={newEnvValue}
                    onChange={(e) => setNewEnvValue(e.target.value)}
                    size="small"
                    fullWidth
                  />
                </Grid>
                <Grid item xs={2}>
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    onClick={handleAddEnv}
                    disabled={!newEnvKey.trim() || !newEnvValue.trim()}
                    fullWidth
                    sx={{ height: '100%' }}
                  >
                    추가
                  </Button>
                </Grid>
              </Grid>
            </Grid>
            
            {error && (
              <Grid item xs={12}>
                <Typography color="error" variant="body2">
                  {error}
                </Typography>
              </Grid>
            )}
          </Grid>
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
          disabled={loading || !id.trim()}
        >
          {loading ? <CircularProgress size={24} /> : '저장'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
