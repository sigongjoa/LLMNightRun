import React, { ReactNode, useEffect, useState, useRef, useMemo } from 'react';
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
  useTheme,
  Collapse,
  Menu,
  MenuItem,
  Tooltip
} from '@mui/material';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import {
  Dashboard as DashboardIcon,
  QuestionAnswer as QuestionIcon,
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
  Psychology as PsychologyIcon,
  CompareArrows as CompareArrowsIcon,
  AutoFixHigh as AutoFixHighIcon
} from '@mui/icons-material';
import { useRouter } from 'next/router';
import Head from 'next/head';

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
  
  // 현재 페이지가 GitHub AI 설정 페이지인지 확인
  const isGitHubAISetupPage = router.pathname === '/github-ai-setup';

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

  // 메뉴 데이터 정의 - 코드 스니펫 관련 메뉴 제거됨
  const menuGroups = useMemo(() => [
    {
      groupName: '개발 및 관리',
      items: [
        { text: '대시보드', icon: <DashboardIcon />, href: '/' },
        { text: 'GitHub 연동', icon: <GitHubIcon />, href: '/github-upload' },
        { text: '문서 관리', icon: <DescriptionIcon />, href: '/docs-manager' },
      ]
    },
    {
      groupName: 'LLM 및 AI',
      items: [
        { text: '질문 제출', icon: <QuestionIcon />, href: '/submit' },
        { text: '로컬 LLM', icon: <MemoryIcon />, href: '/local-llm' },
        { text: '프롬프트 엔지니어링', icon: <EngineeringIcon />, href: '/prompt-engineering' },
        { text: 'AI 환경설정', icon: <SmartToyIcon />, href: '/ai-environment' },
        { text: 'GitHub AI 환경설정', icon: <AutoFixHighIcon />, href: '/github-ai-setup' },
        { text: 'A/B 테스트', icon: <CompareArrowsIcon />, href: '/ab-testing' },
        { text: '메모리 관리', icon: <PsychologyIcon />, href: '/memory-manager' },
      ]
    },
    {
      groupName: 'MCP',
      items: [
        { text: 'MCP 채팅', icon: <SmartToyIcon />, href: '/mcp-chat/new' },
        { text: 'MCP 서버 관리', icon: <CloudIcon />, href: '/mcp' },
      ]
    },
    {
      groupName: '시스템',
      items: [
        { text: '내보내기', icon: <FileDownloadIcon />, href: '/export' },
        { text: '설정', icon: <SettingsIcon />, href: '/settings' },
        { text: 'GitHub 설정', icon: <GitHubIcon />, href: '/github-settings' },
      ]
    }
  ], []);
  
  // 메뉴 그룹화 및 고유성 보장 로직
  const menuItems = useMemo(() => {
    // 모든 메뉴 항목을 플랫하게 만듦
    const baseMenuItems = menuGroups.flatMap(group => {
      return group.items.map(item => ({
        ...item,
        groupName: group.groupName // 그룹 정보 추가
      }));
    });
    
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
  }, [menuGroups, router.pathname]);

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
      
      {/* GitHub AI 설정 페이지에 대한 특수 스크립트 */}
      {isGitHubAISetupPage && (
        <Head>
          <script src="/fix-github-button.js" />
        </Head>
      )}
      
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
            alignItems: 'center',
            overflowX: 'auto',
            msOverflowStyle: 'none',  /* IE, Edge */
            scrollbarWidth: 'none',   /* Firefox */
            '&::-webkit-scrollbar': { /* Chrome, Safari */
              display: 'none'
            }
          }}>
            {/* 그룹별로 메뉴 구성 */}
            {(() => {
              // 그룹 이름으로 메뉴 아이템 그룹화
              const groups = {};
              menuItems.forEach(item => {
                if (!groups[item.groupName]) {
                  groups[item.groupName] = [];
                }
                groups[item.groupName].push(item);
              });

              // 각 그룹별 드롭다운 메뉴 렌더링
              return Object.entries(groups).map(([groupName, items]: [string, any]) => (
                <NavMenuGroup 
                  key={groupName} 
                  groupName={groupName} 
                  items={items} 
                  isActive={isActive} 
                  onNavigate={handleNavigation} 
                />
              ));
            })()}
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
            {/* 그룹별로 메뉴 구성 */}
            {(() => {
              // 그룹 이름으로 메뉴 아이템 그룹화
              const groups = {};
              menuItems.forEach(item => {
                if (!groups[item.groupName]) {
                  groups[item.groupName] = [];
                }
                groups[item.groupName].push(item);
              });

              // 각 그룹별 아코디언 메뉴 렌더링
              return Object.entries(groups).map(([groupName, items]: [string, any]) => (
                <MobileNavGroup 
                  key={groupName} 
                  groupName={groupName} 
                  items={items} 
                  isActive={isActive} 
                  onNavigate={handleNavigation} 
                />
              ));
            })()}
          </List>
        </Box>
      </Drawer>
      
      {/* 메인 컨텐츠 */}
      <Container component="main" className="main-container" sx={{ flexGrow: 1, py: 2 }}>
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

// NavMenuGroup 컴포넌트 - 데스크탑용 드롭다운 메뉴
interface NavMenuGroupProps {
  groupName: string;
  items: any[];
  isActive: (href: string) => boolean;
  onNavigate: (href: string) => void;
}

const NavMenuGroup: React.FC<NavMenuGroupProps> = ({ groupName, items, isActive, onNavigate }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleMenuItemClick = (href: string) => {
    handleClose();
    onNavigate(href);
  };

  return (
    <Box sx={{ position: 'relative', mx: 1 }}>
      <Button
        color="inherit"
        onClick={handleClick}
        endIcon={open ? <ExpandLess /> : <ExpandMore />}
        sx={{ 
          whiteSpace: 'nowrap',
          bgcolor: open ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
          '&:hover': {
            bgcolor: 'rgba(255, 255, 255, 0.1)'
          }
        }}
      >
        {groupName}
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        MenuListProps={{
          'aria-labelledby': 'basic-button',
        }}
      >
        {items.map((item: any) => (
          <MenuItem
            key={item.text}
            onClick={() => handleMenuItemClick(item.href)}
            selected={isActive(item.href)}
          >
            <ListItemIcon sx={{ minWidth: '40px' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText>
              {item.text}
            </ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

// MobileNavGroup 컴포넌트 - 모바일용 아코디언 메뉴
interface MobileNavGroupProps {
  groupName: string;
  items: any[];
  isActive: (href: string) => boolean;
  onNavigate: (href: string) => void;
}

const MobileNavGroup: React.FC<MobileNavGroupProps> = ({ groupName, items, isActive, onNavigate }) => {
  const [open, setOpen] = useState(false);
  
  const handleToggle = () => {
    setOpen(!open);
  };

  return (
    <React.Fragment>
      <ListItem button onClick={handleToggle}>
        <ListItemText primary={<Typography variant="subtitle1" fontWeight="bold">{groupName}</Typography>} />
        {open ? <ExpandLess /> : <ExpandMore />}
      </ListItem>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <List component="div" disablePadding>
          {items.map((item: any) => (
            <ListItem 
              button 
              key={item.text} 
              onClick={() => onNavigate(item.href)}
              sx={{ 
                pl: 4,
                bgcolor: isActive(item.href) ? 'rgba(63, 81, 181, 0.1)' : 'transparent',
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Collapse>
      <Divider />
    </React.Fragment>
  );
};

export default Layout;