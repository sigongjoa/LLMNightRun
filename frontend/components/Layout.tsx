import React, { ReactNode, useEffect, useState, useRef } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Container, 
  Box, 
  Button,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  CssBaseline,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  QuestionAnswer as QuestionIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  SmartToy as SmartToyIcon,
  Memory as MemoryIcon,
  Terminal as TerminalIcon,
  Cloud as CloudIcon,
  FileDownload as FileDownloadIcon,
  Engineering as EngineeringIcon,
  GitHub as GitHubIcon,
  Book as BookIcon,
  Description as DescriptionIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';
import { useRouter } from 'next/router';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const router = useRouter();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const renderCountRef = useRef(0);

  // hydration 문제를 방지하기 위해 마운트 상태 확인
  useEffect(() => {
    setMounted(true);
    renderCountRef.current += 1;
    
    return () => {
      // cleanup
    };
  }, []);

  const toggleDrawer = (open: boolean) => (event: React.KeyboardEvent | React.MouseEvent) => {
    if (
      event.type === 'keydown' &&
      ((event as React.KeyboardEvent).key === 'Tab' ||
        (event as React.KeyboardEvent).key === 'Shift')
    ) {
      return;
    }

    setDrawerOpen(open);
  };

  // 메뉴 고유성 보장을 위한 로직
  const getUniqueMenuItems = () => {
    // 기본 메뉴 항목
    const baseMenuItems = [
      { text: '대시보드', icon: <DashboardIcon />, href: '/' },
      { text: '질문 제출', icon: <QuestionIcon />, href: '/submit' },
      { text: '코드 관리', icon: <CodeIcon />, href: '/code-manager' },
      { text: 'MCP 채팅', icon: <SmartToyIcon />, href: '/mcp-chat/new' },
      { text: '프롬프트 엔지니어링', icon: <EngineeringIcon />, href: '/prompt-engineering' },
      { text: '내보내기', icon: <FileDownloadIcon />, href: '/export' },
      { text: 'GitHub 업로드', icon: <GitHubIcon />, href: '/github-upload' },
      { text: '문서 관리', icon: <DescriptionIcon />, href: '/docs-manager' },
      { text: '로컬 LLM', icon: <MemoryIcon />, href: '/local-llm' },
      { text: 'MCP 서버 관리', icon: <CloudIcon />, href: '/mcp' },
      { text: '메모리 관리', icon: <PsychologyIcon />, href: '/memory-manager' },
      { text: '설정', icon: <SettingsIcon />, href: '/settings' }
    ];
    
    // URL 기반 메뉴 필터링 (필요한 경우)
    if (typeof window !== 'undefined') {
      // 현재 경로가 /mcp-admin 경로인 경우만 필터링
      const currentPath = router.pathname;
      if (currentPath === '/mcp-admin') {
        // MCP 관리자 페이지인 경우 관련 메뉴만 표시
        return baseMenuItems.filter(item => 
          item.href === '/' || 
          item.href === '/mcp-chat' || 
          item.href === '/mcp' || 
          item.href === '/settings'
        );
      }
    }
    
    return baseMenuItems;
  };
  
  const menuItems = getUniqueMenuItems();

  const isActive = (href: string) => {
    // pathname이 href로 시작하는지 확인
    if (!router.pathname) return false;
    return router.pathname === href || router.pathname.startsWith(`${href}/`);
  };

  const handleNavigation = (href: string) => {
    router.push(href);
  };

  // 첫 마운트 전에는 content를 숨김으로 표시
  if (!mounted) {
    return (
      <Box sx={{ visibility: 'hidden', height: '100vh', width: '100vw' }}>
        <div style={{ display: 'none' }}>{children}</div>
      </Box>
    );
  }

  // 중복 렌더링 방지
  if (renderCountRef.current > 1 && typeof window !== 'undefined') {
    renderCountRef.current = 1;
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <CssBaseline />
      
      {/* 메인 앱바 */}
      <AppBar position="static" component="header">
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 1, display: { sm: 'none' }, flexShrink: 0 }}
            onClick={toggleDrawer(true)}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ mr: 4, cursor: 'pointer', flexShrink: 0 }}
            onClick={() => handleNavigation('/')}
          >
            LLMNightRun
          </Typography>
          
          <Box sx={{ 
            display: { xs: 'none', sm: 'flex' }, 
            flexGrow: 1, 
            overflowX: 'auto',
            msOverflowStyle: 'none',  /* IE, Edge */
            scrollbarWidth: 'none',   /* Firefox */
            '&::-webkit-scrollbar': { /* Chrome, Safari */
              display: 'none'
            }
          }}>
            {menuItems.map((item) => (
              <Button 
              key={item.text}
              color="inherit"
              onClick={() => handleNavigation(item.href)}
              data-href={item.href}
              sx={{ 
              mx: 0.5,
              px: 1.5,
              whiteSpace: 'nowrap',
              bgcolor: isActive(item.href) ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
              '&:hover': {
                bgcolor: 'rgba(255, 255, 255, 0.1)'
                }
                }}
              >
                {item.text}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </AppBar>
      
      {/* 모바일 드로어 메뉴 */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer(false)}
      >
        <Box
          sx={{ width: 250 }}
          role="presentation"
          onClick={toggleDrawer(false)}
          onKeyDown={toggleDrawer(false)}
        >
          <List>
            <ListItem>
              <Typography variant="h6" sx={{ py: 1 }}>
                LLMNightRun
              </Typography>
            </ListItem>
            <Divider />
            {menuItems.map((item) => (
              <ListItem 
                button 
                key={item.text} 
                onClick={() => handleNavigation(item.href)}
                sx={{ 
                  bgcolor: isActive(item.href) ? 'rgba(63, 81, 181, 0.1)' : 'transparent',
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
      
      {/* 메인 컨텐츠 */}
      <Container component="main" sx={{ flexGrow: 1, py: 4 }}>
        {children}
      </Container>
      
      {/* 푸터 */}
      <Box component="footer" sx={{ py: 3, bgcolor: 'background.paper', textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          © {new Date().getFullYear()} LLMNightRun - 멀티 LLM 통합 자동화 플랫폼
        </Typography>
      </Box>
    </Box>
  );
};

export default Layout;