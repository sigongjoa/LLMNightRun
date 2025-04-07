import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  IconButton,
  CircularProgress,
  Alert,
  Divider,
  InputAdornment,
  Grid,
  FormControlLabel,
  Switch
} from '@mui/material';
import { 
  Close as CloseIcon, 
  Add as AddIcon,
  GitHub as GitHubIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Diversity1 as FetchIcon,
  DataObject as DatabaseIcon,
  Folder as FilesystemIcon
} from '@mui/icons-material';
import { useMcp } from '../../contexts/McpContext';
import { ServerConfig } from '../../utils/mcp/api';

interface ExternalServerAdderProps {
  open: boolean;
  onClose: () => void;
}

interface ServerTemplate {
  name: string;
  description: string;
  gitUrl: string;
  installCommand: string;
  icon: React.ReactNode;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
}

const POPULAR_MCP_SERVERS: ServerTemplate[] = [
  {
    name: 'GitHub API',
    description: '공식 GitHub MCP 서버. GitHub API와 연동하여 저장소, 이슈, PR 관리 기능 제공',
    gitUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/github',
    installCommand: 'npm install -g @modelcontextprotocol/server-github',
    icon: <GitHubIcon />,
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-github'],
    env: { 'GITHUB_PERSONAL_ACCESS_TOKEN': '' }
  },
  {
    name: 'PostgreSQL',
    description: '공식 PostgreSQL MCP 서버. 데이터베이스 조회 및 분석 기능 제공',
    gitUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/postgres',
    installCommand: 'npm install -g @modelcontextprotocol/server-postgres',
    icon: <DatabaseIcon />,
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-postgres', 'postgres://username:password@localhost:5432/database']
  },
  {
    name: 'Fetch',
    description: '공식 Fetch MCP 서버. 웹 컨텐츠 수집 및 변환 기능 제공',
    gitUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/fetch',
    installCommand: 'npm install -g @modelcontextprotocol/server-fetch',
    icon: <FetchIcon />,
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-fetch']
  },
  {
    name: 'Git',
    description: '공식 Git MCP 서버. Git 저장소 읽기, 검색 및 조작 기능 제공',
    gitUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/git',
    installCommand: 'npm install -g @modelcontextprotocol/server-git',
    icon: <CodeIcon />,
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-git', '/path/to/your/repo']
  },
  {
    name: 'Memory',
    description: '공식 Memory MCP 서버. 지식 그래프 기반 영구 메모리 시스템 제공',
    gitUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/memory',
    installCommand: 'npm install -g @modelcontextprotocol/server-memory',
    icon: <StorageIcon />,
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-memory']
  },
  {
    name: 'Filesystem',
    description: '공식 Filesystem MCP 서버. 파일 시스템 접근 기능 제공',
    gitUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem',
    installCommand: 'npm install -g @modelcontextprotocol/server-filesystem',
    icon: <FilesystemIcon />,
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/directory']
  }
];

export const ExternalServerAdder: React.FC<ExternalServerAdderProps> = ({ open, onClose }) => {
  const { updateServer } = useMcp();
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);
  const [useNpx, setUseNpx] = useState<boolean>(true);
  
  const [serverId, setServerId] = useState<string>('');
  const [command, setCommand] = useState<string>('npx');
  const [args, setArgs] = useState<string>('');
  const [envVars, setEnvVars] = useState<string>('');

  // 템플릿 선택 핸들러
  const handleSelectTemplate = (index: number) => {
    const template = POPULAR_MCP_SERVERS[index];
    setSelectedTemplate(index);
    
    // 기본 ID 설정 (중복 방지를 위해 아이디는 설정하지 않음)
    const defaultId = template.name.toLowerCase().replace(/\s+/g, '-');
    setServerId(defaultId);
    
    // 템플릿 설정 적용
    if (template.command) {
      setCommand(template.command);
      setUseNpx(template.command === 'npx');
    }
    
    if (template.args) {
      setArgs(template.args.join(' '));
    }
    
    if (template.env) {
      setEnvVars(Object.entries(template.env)
        .map(([key, value]) => `${key}=${value}`)
        .join('\n'));
    } else {
      setEnvVars('');
    }
  };

  // 저장 핸들러
  const handleSave = async () => {
    if (!serverId.trim()) {
      setError('서버 ID는 필수입니다.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // 입력값을 ServerConfig 형식으로 변환
      const argsList = args.split(/\s+/).filter(arg => arg.trim() !== '');
      
      // 환경 변수 파싱
      const envObject: Record<string, string> = {};
      envVars.split('\n').forEach(line => {
        const [key, ...valueParts] = line.split('=');
        const value = valueParts.join('=');
        if (key && key.trim()) {
          envObject[key.trim()] = value || '';
        }
      });
      
      const config: ServerConfig = {
        command,
        args: argsList,
        env: envObject
      };
      
      await updateServer(serverId.trim(), config);
      onClose();
    } catch (err) {
      console.error('Error saving server:', err);
      setError('서버 설정을 저장하는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 폼 초기화
  const resetForm = () => {
    setSelectedTemplate(null);
    setServerId('');
    setCommand('npx');
    setUseNpx(true);
    setArgs('');
    setEnvVars('');
    setError(null);
  };

  // 다이얼로그 닫기 핸들러
  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">외부 MCP 서버 추가</Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        <Alert severity="info" sx={{ mb: 3 }}>
          인기 있는 MCP 서버를 선택하거나 커스텀 서버를 직접 추가하세요.
        </Alert>
        
        <Typography variant="subtitle1" gutterBottom>
          인기 있는 MCP 서버
        </Typography>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
          {POPULAR_MCP_SERVERS.map((server, index) => (
            <Box 
              key={index}
              sx={{
                width: 'calc(50% - 8px)',
                border: '1px solid #ddd',
                borderRadius: 1,
                p: 2,
                cursor: 'pointer',
                bgcolor: selectedTemplate === index ? 'action.selected' : 'background.paper',
                '&:hover': {
                  bgcolor: 'action.hover'
                }
              }}
              onClick={() => handleSelectTemplate(index)}
            >
              <Box display="flex" alignItems="center" mb={1}>
                <Box mr={1} color="primary.main">
                  {server.icon}
                </Box>
                <Typography variant="subtitle2">{server.name}</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                {server.description}
              </Typography>
              <Box mt={1}>
                <Typography variant="caption" component="div" color="text.secondary">
                  설치: <code>{server.installCommand}</code>
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Typography variant="subtitle1" gutterBottom>
          서버 설정
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              label="서버 ID"
              value={serverId}
              onChange={(e) => setServerId(e.target.value)}
              fullWidth
              required
              helperText="고유한 식별자 (예: github, postgres, custom-fetch)"
            />
          </Grid>
          
          <Grid item xs={12}>
            <Box display="flex" alignItems="center" mb={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={useNpx}
                    onChange={(e) => {
                      setUseNpx(e.target.checked);
                      setCommand(e.target.checked ? 'npx' : '');
                    }}
                  />
                }
                label="NPX 사용 (권장)"
              />
            </Box>
            <TextField
              label="명령어"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              disabled={useNpx}
              fullWidth
              required
              helperText={useNpx ? "NPX를 사용하여 패키지를 실행합니다." : "서버 실행 명령어 (전체 경로)"}
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              label="인자"
              value={args}
              onChange={(e) => setArgs(e.target.value)}
              fullWidth
              multiline
              rows={2}
              helperText="공백으로 구분된 명령어 인자 (예: -y @modelcontextprotocol/server-github)"
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              label="환경 변수"
              value={envVars}
              onChange={(e) => setEnvVars(e.target.value)}
              fullWidth
              multiline
              rows={4}
              helperText="각 줄에 하나의 환경 변수 (형식: KEY=VALUE)"
              placeholder="GITHUB_TOKEN=your-token-here
API_KEY=your-api-key"
            />
          </Grid>
        </Grid>
        
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          취소
        </Button>
        <Button 
          onClick={handleSave} 
          variant="contained" 
          color="primary" 
          disabled={loading || !serverId.trim()}
          startIcon={loading ? <CircularProgress size={24} /> : <AddIcon />}
        >
          MCP 서버 추가
        </Button>
      </DialogActions>
    </Dialog>
  );
};
