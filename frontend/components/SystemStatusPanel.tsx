import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, Typography, Box, Chip, CircularProgress, Button, Tooltip } from '@mui/material';
import { CheckCircle, Cancel, Warning, Sync } from '@mui/icons-material';
import { getApiStatus, updateApiBaseUrl } from '../utils/api';

interface SystemStatus {
  apiConnected: boolean;
  apiUrl: string;
  availableServers: string[];
  openaiConnected: boolean;
  claudeConnected: boolean;
  githubConnected: boolean;
  mcpServersCount: number;
}

const SystemStatusPanel: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus>({
    apiConnected: false,
    apiUrl: '',
    availableServers: [],
    openaiConnected: false,
    claudeConnected: false,
    githubConnected: false,
    mcpServersCount: 0
  });
  
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // 시스템 상태 확인
  const checkSystemStatus = async () => {
    try {
      setRefreshing(true);
      // API 상태 확인
      const apiStatus = await getApiStatus();
      
      // 여기서는 더미 데이터를 사용하지만, 실제로는 각 서비스 상태를 확인하는 API 호출이 필요합니다.
      // 실제 구현에서는 각각의 상태 확인 API를 호출해야 합니다.
      setStatus({
        apiConnected: apiStatus.apiConnected,
        apiUrl: apiStatus.apiUrl,
        availableServers: apiStatus.availableServers,
        openaiConnected: true, // 더미 데이터
        claudeConnected: true, // 더미 데이터
        githubConnected: true, // 더미 데이터
        mcpServersCount: 2 // 더미 데이터
      });
    } catch (error) {
      console.error('시스템 상태 확인 오류:', error);
      setStatus(prevStatus => ({
        ...prevStatus,
        apiConnected: false
      }));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // 컴포넌트 마운트 시 및 일정 간격으로 상태 확인
  useEffect(() => {
    checkSystemStatus();
    
    // 30초마다 상태 확인
    const intervalId = setInterval(checkSystemStatus, 30000);
    
    return () => {
      clearInterval(intervalId);
    };
  }, []);
  
  // 서버 연결 재시도
  const retryConnection = async () => {
    setRefreshing(true);
    try {
      const newUrl = await updateApiBaseUrl();
      console.log('API URL 업데이트됨:', newUrl);
    } catch (error) {
      console.error('서버 연결 재시도 실패:', error);
    }
    await checkSystemStatus();
    setRefreshing(false);
  };

  // 상태 표시 아이콘 및 색상
  const getStatusIcon = (isConnected: boolean) => {
    if (isConnected) {
      return <CheckCircle fontSize="small" sx={{ color: 'success.main', mr: 1 }} />;
    }
    return <Cancel fontSize="small" sx={{ color: 'error.main', mr: 1 }} />;
  };

  return (
    <Card>
      <CardHeader 
        title="시스템 상태" 
        action={
          <Button 
            startIcon={refreshing ? <CircularProgress size={20} /> : <Sync />}
            onClick={retryConnection}
            disabled={refreshing}
            size="small"
          >
            새로고침
          </Button>
        }
      />
      <CardContent>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : (
          <>
            <Typography variant="body1" component="div" color="text.secondary" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
              {getStatusIcon(status.apiConnected)}
              API 상태: 
              <Box component="span" sx={{ ml: 1, fontWeight: 'bold', color: status.apiConnected ? 'success.main' : 'error.main' }}>
                {status.apiConnected ? '연결됨' : '연결 실패'}
              </Box>
              {status.apiConnected && (
                <Tooltip title={`현재 API URL: ${status.apiUrl}`}>
                  <Chip 
                    label={status.apiUrl.includes('8001') ? '백업 서버' : '기본 서버'} 
                    size="small" 
                    color={status.apiUrl.includes('8001') ? 'warning' : 'success'}
                    sx={{ ml: 1 }}
                  />
                </Tooltip>
              )}
            </Typography>

            <Typography variant="body1" component="div" color="text.secondary" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
              {getStatusIcon(status.openaiConnected)}
              OpenAI API: 
              <Box component="span" sx={{ ml: 1, fontWeight: 'bold', color: status.openaiConnected ? 'success.main' : 'error.main' }}>
                {status.openaiConnected ? '연결됨' : '연결 실패'}
              </Box>
            </Typography>

            <Typography variant="body1" component="div" color="text.secondary" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
              {getStatusIcon(status.claudeConnected)}
              Claude API: 
              <Box component="span" sx={{ ml: 1, fontWeight: 'bold', color: status.claudeConnected ? 'success.main' : 'error.main' }}>
                {status.claudeConnected ? '연결됨' : '연결 실패'}
              </Box>
            </Typography>

            <Typography variant="body1" component="div" color="text.secondary" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
              {getStatusIcon(status.githubConnected)}
              GitHub 연동: 
              <Box component="span" sx={{ ml: 1, fontWeight: 'bold', color: status.githubConnected ? 'success.main' : 'error.main' }}>
                {status.githubConnected ? '활성화' : '비활성화'}
              </Box>
            </Typography>

            <Typography variant="body1" component="div" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
              {status.mcpServersCount > 0 ? (
                <CheckCircle fontSize="small" sx={{ color: 'success.main', mr: 1 }} />
              ) : (
                <Warning fontSize="small" sx={{ color: 'warning.main', mr: 1 }} />
              )}
              MCP 서버: 
              <Box component="span" sx={{ 
                ml: 1, 
                fontWeight: 'bold', 
                color: status.mcpServersCount > 0 ? 'success.main' : 'warning.main' 
              }}>
                {status.mcpServersCount > 0 ? `실행 중 (${status.mcpServersCount})` : '없음'}
              </Box>
            </Typography>
            
            {status.availableServers.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  사용 가능한 서버: {status.availableServers.join(', ')}
                </Typography>
              </Box>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default SystemStatusPanel;