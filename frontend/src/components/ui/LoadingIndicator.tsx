import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingIndicatorProps {
  message?: string;
  fullScreen?: boolean;
  size?: number;
}

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  message = '로딩 중...',
  fullScreen = false,
  size = 40,
}) => {
  const content = (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        p: 3,
      }}
    >
      <CircularProgress size={size} thickness={4} />
      {message && (
        <Typography variant="body1" sx={{ mt: 2 }}>
          {message}
        </Typography>
      )}
    </Box>
  );

  if (fullScreen) {
    return (
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: (theme) => theme.palette.background.default,
          zIndex: (theme) => theme.zIndex.modal + 1,
        }}
      >
        {content}
      </Box>
    );
  }

  return content;
};

export default LoadingIndicator;
