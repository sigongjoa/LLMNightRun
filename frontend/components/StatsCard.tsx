import React from 'react';
import { Card, CardContent, Typography, Box, CircularProgress } from '@mui/material';
import Icon from '@mui/material/Icon';

interface StatsCardProps {
  title: string;
  value: number | string;
  loading?: boolean;
  icon: string;
  color?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, loading = false, icon, color = '#000' }) => {
  return (
    <Card elevation={3}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            
            {loading ? (
              <CircularProgress size={24} />
            ) : (
              <Typography variant="h4" component="div" fontWeight="bold">
                {value}
              </Typography>
            )}
          </Box>
          
          <Box 
            sx={{ 
              backgroundColor: `${color}20`,  // 20% 투명도
              width: 50, 
              height: 50, 
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Icon sx={{ color: color, fontSize: 28 }}>
              {icon}
            </Icon>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default StatsCard;