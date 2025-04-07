import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';

/**
 * 비활성화된 MCP 터미널 컴포넌트
 * 
 * 이 컴포넌트는 터미널 기능이 비활성화되었음을 알려주는 플레이스홀더입니다.
 */
const MCPTerminal = () => {
  return (
    <Paper 
      elevation={3}
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#252525',
        color: '#f0f0f0',
        p: 3,
        borderRadius: 1
      }}
    >
      <WarningIcon sx={{ fontSize: 48, color: 'warning.main', mb: 2 }} />
      
      <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
        터미널 기능이 비활성화되었습니다
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 1, textAlign: 'center' }}>
        LLMNightRun에서 터미널 기능은 현재 지원되지 않습니다.
      </Typography>
      
      <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary' }}>
        다른 기능을 사용하시거나, LLMNightRun 설정을 확인해주세요.
      </Typography>
    </Paper>
  );
};

export default MCPTerminal;
