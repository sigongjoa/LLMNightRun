import React, { ReactNode, useState } from 'react';
import {
  AppBar,
  Box,
  Container,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import CodeIcon from '@mui/icons-material/Code';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import StorageIcon from '@mui/icons-material/Storage';
import SettingsIcon from '@mui/icons-material/Settings';
import GitHubIcon from '@mui/icons-material/GitHub';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useMCPStatus } from '../../hooks';

// 드로어 너비
const drawerWidth = 240;

// 네비게이션 항목 정의
const navigationItems = [
  { text: '질문 & 응답', href: '/', icon: <QuestionAnswerIcon /> },
  { text: '코드 관리', href: '/code', icon: <CodeIcon /> },
  { text: '에이전트', href: '/agent', icon: <SmartToyIcon /> },
  { text: '데이터 관리', href: '/data', icon: <StorageIcon /> },
  { text: 'GitHub 연동', href: '/github', icon: <GitHubIcon /> },
  { text: '설정', href: '/settings', icon: <SettingsIcon /> },
];

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title = 'LLMNightRun' }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(!isMobile);
  const router = useRouter();
  
  // MCP 상태 조회
  const { data: mcpStatus, isLoading: mcpStatusLoading } = useMCPStatus();

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* 앱바 */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ...(drawerOpen && {
            marginLeft: drawerWidth,
            width: `calc(100% - ${drawerWidth}px)`,
            transition: theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          }),
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerToggle}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {title}
          </Typography>
          
          {/* MCP 상태 표시 */}
          {!mcpStatusLoading && (
            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center',
                backgroundColor: mcpStatus?.status === 'online' ? 'success.main' : 'error.main',
                borderRadius: '16px',
                padding: '4px 12px',
                color: 'white',
              }}
            >
              <Typography variant="body2" sx={{ mr: 1 }}>
                MCP: {mcpStatus?.status === 'online' ? '온라인' : '오프라인'}
              </Typography>
            </Box>
          )}
        </Toolbar>
      </AppBar>
      
      {/* 사이드 드로어 */}
      <Drawer
        variant={isMobile ? 'temporary' : 'persistent'}
        open={drawerOpen}
        onClose={isMobile ? handleDrawerToggle : undefined}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto', mt: 2 }}>
          {!isMobile && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
              <IconButton onClick={handleDrawerToggle}>
                <ChevronLeftIcon />
              </IconButton>
            </Box>
          )}
          
          <List>
            {navigationItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <Link href={item.href} passHref style={{ textDecoration: 'none', width: '100%', color: 'inherit' }}>
                  <ListItemButton selected={router.pathname === item.href}>
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.text} />
                  </ListItemButton>
                </Link>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
      
      {/* 메인 콘텐츠 */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar /> {/* 앱바 높이만큼 상단 여백 */}
        <Container maxWidth="xl">
          {children}
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;
