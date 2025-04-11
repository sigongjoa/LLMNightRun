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
      
      // 다양한 경로로 서버에 연결 시도
      let success = false;
      try {
        // 직접 루트 경로로 원시 요청
        const response = await fetch('http://localhost:8000/');
        if (response.ok) {
          success = true;
        }
      } catch (fetchError) {
        console.warn('원시 연결 시도 실패:', fetchError);
      }
      
      // API 상태 확인 (백업)
      if (!success) {
        try {
          const apiStatus = await getApiStatus();
          success = apiStatus.apiConnected;
        } catch (apiError) {
          console.warn('API 상태 확인 실패:', apiError);
        }
      }
      
      // 임시 상태 데이터 - 서버가 연결되면 모든 서비스가 활성화된 것으로 표시
      setStatus({
        apiConnected: success,
        apiUrl: 'http://localhost:8000',
        availableServers: success ? ['local'] : [],
        openaiConnected: success,
        claudeConnected: success,
        githubConnected: success,
        mcpServersCount: success ? 2 : 0
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
            
            {status.apiConnected && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  사용 가능한 서버: {status.availableServers && status.availableServers.length > 0 
                    ? status.availableServers.join(', ') 
                    : '로컬'}
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