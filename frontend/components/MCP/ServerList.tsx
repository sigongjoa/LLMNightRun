import React from 'react';
import { 
  Box, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemSecondaryAction, 
  IconButton, 
  Typography, 
  Paper, 
  Tooltip, 
  Chip, 
  Button, 
  CircularProgress 
} from '@mui/material';
import { 
  PlayArrow as StartIcon, 
  Stop as StopIcon, 
  Refresh as RestartIcon, 
  Edit as EditIcon, 
  Delete as DeleteIcon, 
  Add as AddIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useMcp } from '../../contexts/McpContext';
import { ServerInfo } from '../../utils/mcp/api';

interface ServerListProps {
  onEdit: (serverId: string) => void;
  onAdd: () => void;
}

export const ServerList: React.FC<ServerListProps> = ({ onEdit, onAdd }) => {
  const { 
    servers, 
    isLoading, 
    error, 
    refreshServers, 
    startServer, 
    stopServer, 
    restartServer,
    deleteServer,
    startAllServers,
    stopAllServers
  } = useMcp();

  const handleDelete = async (serverId: string) => {
    if (window.confirm(`서버 "${serverId}"를 삭제하시겠습니까?`)) {
      try {
        await deleteServer(serverId);
      } catch (error) {
        console.error('Failed to delete server:', error);
      }
    }
  };

  const handleStartAll = async () => {
    try {
      await startAllServers();
    } catch (error) {
      console.error('Failed to start all servers:', error);
    }
  };

  const handleStopAll = async () => {
    try {
      await stopAllServers();
    } catch (error) {
      console.error('Failed to stop all servers:', error);
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" component="h2">
          MCP 서버 목록
        </Typography>
        <Box>
          <Tooltip title="새로고침">
            <IconButton onClick={refreshServers} disabled={isLoading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="서버 추가">
            <IconButton onClick={onAdd} color="primary">
              <AddIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Typography color="error" variant="body2" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      {isLoading ? (
        <Box display="flex" justifyContent="center" my={3}>
          <CircularProgress />
        </Box>
      ) : servers.length === 0 ? (
        <Typography variant="body1" sx={{ my: 2, textAlign: 'center' }}>
          등록된 MCP 서버가 없습니다. '서버 추가' 버튼을 클릭하여 서버를 추가하세요.
        </Typography>
      ) : (
        <>
          <List>
            {servers.map((server: ServerInfo) => (
              <ListItem key={server.id} divider>
                <ListItemText
                  primary={server.id}
                  secondary={
                    <>
                      <Typography component="span" variant="body2" color="text.primary">
                        {server.command} {server.args.join(' ')}
                      </Typography>
                      <Box mt={1}>
                        <Chip
                          label={server.running ? '실행 중' : '중지됨'}
                          color={server.running ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </>
                  }
                />
                <ListItemSecondaryAction>
                  <Tooltip title={server.running ? '중지' : '시작'}>
                    <IconButton
                      edge="end"
                      onClick={() => server.running ? stopServer(server.id) : startServer(server.id)}
                      color={server.running ? 'error' : 'success'}
                    >
                      {server.running ? <StopIcon /> : <StartIcon />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="재시작">
                    <IconButton
                      edge="end"
                      onClick={() => restartServer(server.id)}
                      disabled={!server.running}
                    >
                      <RestartIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="편집">
                    <IconButton edge="end" onClick={() => onEdit(server.id)}>
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="삭제">
                    <IconButton edge="end" onClick={() => handleDelete(server.id)} color="error">
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>

          <Box display="flex" justifyContent="flex-end" mt={2} gap={1}>
            <Button
              variant="outlined"
              startIcon={<StartIcon />}
              onClick={handleStartAll}
              disabled={servers.every(s => s.running)}
            >
              모든 서버 시작
            </Button>
            <Button
              variant="outlined"
              startIcon={<StopIcon />}
              onClick={handleStopAll}
              disabled={servers.every(s => !s.running)}
              color="error"
            >
              모든 서버 중지
            </Button>
          </Box>
        </>
      )}
    </Paper>
  );
};
