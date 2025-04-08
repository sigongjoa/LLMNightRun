import React from 'react';
import { 
  Box, 
  Typography, 
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Tooltip,
  Chip,
  Card,
  CardContent
} from '@mui/material';
import { Tool } from './ChatInterface';

// 아이콘 import
import SearchIcon from '@mui/icons-material/Search';
import CodeIcon from '@mui/icons-material/Code';
import GitHubIcon from '@mui/icons-material/GitHub';
import EditIcon from '@mui/icons-material/Edit';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import BuildIcon from '@mui/icons-material/Build';

interface ToolsPanelProps {
  tools: Tool[];
  onSelect: (tool: Tool) => void;
}

const ToolsPanel: React.FC<ToolsPanelProps> = ({ tools, onSelect }) => {
  // 도구 아이콘 매핑
  const getToolIcon = (toolId: string) => {
    switch (toolId) {
      case 'file_search':
        return <SearchIcon />;
      case 'python_execute':
        return <CodeIcon />;
      case 'github_tool':
        return <GitHubIcon />;
      case 'str_replace_editor':
        return <EditIcon />;
      case 'terminate':
        return <ExitToAppIcon />;
      default:
        return <BuildIcon />;
    }
  };
  
  return (
    <Paper 
      elevation={0}
      variant="outlined"
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        borderRadius: 1
      }}
    >
      <Box sx={{ 
        p: 2, 
        borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
        bgcolor: '#f8f9fa'
      }}>
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 600,
            fontSize: '1.1rem',
            color: '#333',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <BuildIcon sx={{ mr: 1, fontSize: '1.2rem' }} />
          사용 가능한 도구
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          MCP 에이전트가 다음 도구들을 사용할 수 있습니다. 도구를 클릭하여 사용해보세요.
        </Typography>
      </Box>
      
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List sx={{ px: 1 }}>
          {tools.map((tool) => (
            <React.Fragment key={tool.id}>
              <ListItem disablePadding>
                <ListItemButton 
                  onClick={() => onSelect(tool)}
                  sx={{ 
                    borderRadius: 1,
                    '&:hover': {
                      bgcolor: 'rgba(0, 0, 0, 0.04)'
                    }
                  }}
                >
                  <ListItemIcon>
                    {getToolIcon(tool.id)}
                  </ListItemIcon>
                  <ListItemText 
                    primary={tool.name} 
                    secondary={tool.description}
                    primaryTypographyProps={{
                      fontWeight: 500,
                      fontSize: '0.95rem'
                    }}
                    secondaryTypographyProps={{
                      fontSize: '0.85rem'
                    }}
                  />
                </ListItemButton>
              </ListItem>
              <Divider component="li" />
            </React.Fragment>
          ))}
        </List>
      </Box>

      <Box sx={{ p: 2, borderTop: '1px solid rgba(0, 0, 0, 0.1)', bgcolor: '#f8f9fa' }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          도구 사용 예시
        </Typography>
        <Card variant="outlined" sx={{ mb: 1 }}>
          <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
              "프로젝트에서 Python 파일을 모두 찾아줘"
            </Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ mb: 1 }}>
          <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
              "이 코드를 최적화해서 실행해줘: import pandas as pd"
            </Typography>
          </CardContent>
        </Card>
        <Card variant="outlined">
          <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
              "main.py 파일의 모든 print문을 로깅으로 변경해줘"
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Paper>
  );
};

export default ToolsPanel;