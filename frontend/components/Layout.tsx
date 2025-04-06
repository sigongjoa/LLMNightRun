import React, { ReactNode } from 'react';
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
  IconButton
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  QuestionAnswer as QuestionIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  SmartToy as SmartToyIcon // 추가된 import
} from '@mui/icons-material';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = React.useState(false);

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

  const menuItems = [
    { text: '대시보드', icon: <DashboardIcon />, href: '/' },
    { text: '질문 제출', icon: <QuestionIcon />, href: '/submit' },
    { text: '코드 관리', icon: <CodeIcon />, href: '/code-manager' },
    { text: 'Manus 에이전트', icon: <SmartToyIcon />, href: '/agent' },
    { text: '설정', icon: <SettingsIcon />, href: '/settings' }
  ];

  const isActive = (href: string) => router.pathname === href;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2, display: { sm: 'none' } }}
            onClick={toggleDrawer(true)}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Link href="/">
              LLMNightRun
            </Link>
          </Typography>
          
          <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
            {menuItems.map((item) => (
              <Button 
                key={item.text}
                color="inherit"
                component={Link}
                href={item.href}
                sx={{ 
                  mx: 1,
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
                component={Link}
                href={item.href}
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
      
      <Container component="main" sx={{ flexGrow: 1, py: 4 }}>
        {children}
      </Container>
      
      <Box component="footer" sx={{ py: 3, bgcolor: 'background.paper', textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          © {new Date().getFullYear()} LLMNightRun - 멀티 LLM 통합 자동화 플랫폼
        </Typography>
      </Box>
    </Box>
  );
};

export default Layout;