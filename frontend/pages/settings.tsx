import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Grid, 
  TextField, 
  Button, 
  Alert, 
  CircularProgress,
  Tabs,
  Tab,
  Divider,
  IconButton,
  InputAdornment,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Save as SaveIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { Settings } from '../types';
import { fetchSettings, updateSettings } from '../utils/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SettingsPage: React.FC = () => {
  // 상태 관리
  const [settings, setSettings] = useState<Settings>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<number>(0);
  
  // 비밀번호 표시 상태
  const [showOpenAIKey, setShowOpenAIKey] = useState<boolean>(false);
  const [showClaudeKey, setShowClaudeKey] = useState<boolean>(false);
  const [showGitHubToken, setShowGitHubToken] = useState<boolean>(false);
  
  // 웹 크롤링 설정
  const [enableWebCrawling, setEnableWebCrawling] = useState<boolean>(false);
  const [openaiUsername, setOpenaiUsername] = useState<string>('');
  const [openaiPassword, setOpenaiPassword] = useState<string>('');
  const [claudeUsername, setClaudeUsername] = useState<string>('');
  const [claudePassword, setClaudePassword] = useState<string>('');
  
  // 데이터 로드
  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const settingsData = await fetchSettings();
        setSettings(settingsData);
        
        // 환경 변수에서 웹 크롤링 설정 로드 (실제로는 API를 통해 가져와야 함)
        setEnableWebCrawling(localStorage.getItem('enable_web_crawling') === 'true');
        setOpenaiUsername(localStorage.getItem('openai_username') || '');
        setOpenaiPassword(localStorage.getItem('openai_password') || '');
        setClaudeUsername(localStorage.getItem('claude_username') || '');
        setClaudePassword(localStorage.getItem('claude_password') || '');
      } catch (err: any) {
        console.error('설정 로딩 오류:', err);
        setError(err.detail || '설정을 불러오는 중에 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    loadSettings();
  }, []);
  
  // 탭 변경 핸들러
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  // 설정 저장 핸들러
  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);
      
      // API 설정 저장
      await updateSettings(settings);
      
      // 웹 크롤링 설정 저장 (로컬 스토리지에 임시 저장)
      localStorage.setItem('enable_web_crawling', enableWebCrawling.toString());
      localStorage.setItem('openai_username', openaiUsername);
      localStorage.setItem('openai_password', openaiPassword);
      localStorage.setItem('claude_username', claudeUsername);
      localStorage.setItem('claude_password', claudePassword);
      
      setSuccess(true);
      
      // 3초 후 성공 메시지 숨기기
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (err: any) {
      console.error('설정 저장 오류:', err);
      setError(err.detail || '설정을 저장하는 중에 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  };
  
  // 테스트 연결 핸들러
  const handleTestConnection = (service: string) => {
    // 실제로는 API를 통해 연결 테스트
    alert(`${service} 연결 테스트를 수행합니다.`);
  };
  
  // 로딩 화면
  if (loading) {
    return (
      <Container maxWidth="md">
        <Box sx={{ my: 4, textAlign: 'center' }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>설정을 불러오는 중...</Typography>
        </Box>
      </Container>
    );
  }
  
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          설정
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert 
            severity="success" 
            sx={{ mb: 3 }}
            icon={<CheckCircleIcon fontSize="inherit" />}
          >
            설정이 성공적으로 저장되었습니다.
          </Alert>
        )}
        
        <Paper elevation={3}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange}
              variant="fullWidth"
            >
              <Tab label="API 키" />
              <Tab label="GitHub 설정" />
              <Tab label="웹 크롤링" />
            </Tabs>
          </Box>
          
          {/* API 키 설정 */}
          <TabPanel value={activeTab} index={0}>
            <Typography variant="h6" gutterBottom>
              LLM API 키 설정
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              OpenAI와 Anthropic API 키를 설정하여 API를 통해 LLM에 액세스합니다.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  label="OpenAI API 키"
                  fullWidth
                  value={settings.openai_api_key || ''}
                  onChange={(e) => setSettings({...settings, openai_api_key: e.target.value})}
                  type={showOpenAIKey ? 'text' : 'password'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowOpenAIKey(!showOpenAIKey)}
                          edge="end"
                        >
                          {showOpenAIKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  label="Claude API 키"
                  fullWidth
                  value={settings.claude_api_key || ''}
                  onChange={(e) => setSettings({...settings, claude_api_key: e.target.value})}
                  type={showClaudeKey ? 'text' : 'password'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowClaudeKey(!showClaudeKey)}
                          edge="end"
                        >
                          {showClaudeKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="outlined" 
                  onClick={() => handleTestConnection('OpenAI')}
                  fullWidth
                >
                  OpenAI 연결 테스트
                </Button>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="outlined" 
                  onClick={() => handleTestConnection('Claude')}
                  fullWidth
                >
                  Claude 연결 테스트
                </Button>
              </Grid>
            </Grid>
          </TabPanel>
          
          {/* GitHub 설정 */}
          <TabPanel value={activeTab} index={1}>
            <Typography variant="h6" gutterBottom>
              GitHub 연동 설정
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              응답과 코드를 GitHub 저장소에 저장하기 위한 설정을 구성합니다.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  label="GitHub 토큰"
                  fullWidth
                  value={settings.github_token || ''}
                  onChange={(e) => setSettings({...settings, github_token: e.target.value})}
                  type={showGitHubToken ? 'text' : 'password'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowGitHubToken(!showGitHubToken)}
                          edge="end"
                        >
                          {showGitHubToken ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  label="GitHub 사용자명"
                  fullWidth
                  value={settings.github_username || ''}
                  onChange={(e) => setSettings({...settings, github_username: e.target.value})}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  label="저장소 이름"
                  fullWidth
                  value={settings.github_repo || ''}
                  onChange={(e) => setSettings({...settings, github_repo: e.target.value})}
                />
              </Grid>
              
              <Grid item xs={12}>
                <Button 
                  variant="outlined" 
                  onClick={() => handleTestConnection('GitHub')}
                  fullWidth
                >
                  GitHub 연결 테스트
                </Button>
              </Grid>
            </Grid>
          </TabPanel>
          
          {/* 웹 크롤링 설정 */}
          <TabPanel value={activeTab} index={2}>
            <Typography variant="h6" gutterBottom>
              웹 크롤링 설정
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              ChatGPT와 Claude 웹 인터페이스를 자동화하기 위한 설정을 구성합니다.
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={enableWebCrawling}
                  onChange={(e) => setEnableWebCrawling(e.target.checked)}
                />
              }
              label="웹 크롤링 활성화"
              sx={{ mb: 2 }}
            />
            
            {enableWebCrawling && (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }}>
                    <Typography variant="subtitle2">OpenAI 웹 계정</Typography>
                  </Divider>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="OpenAI 사용자명"
                    fullWidth
                    value={openaiUsername}
                    onChange={(e) => setOpenaiUsername(e.target.value)}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="OpenAI 비밀번호"
                    fullWidth
                    type="password"
                    value={openaiPassword}
                    onChange={(e) => setOpenaiPassword(e.target.value)}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }}>
                    <Typography variant="subtitle2">Claude 웹 계정</Typography>
                  </Divider>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Claude 사용자명"
                    fullWidth
                    value={claudeUsername}
                    onChange={(e) => setClaudeUsername(e.target.value)}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Claude 비밀번호"
                    fullWidth
                    type="password"
                    value={claudePassword}
                    onChange={(e) => setClaudePassword(e.target.value)}
                  />
                </Grid>
              </Grid>
            )}
          </TabPanel>
          
          <Box sx={{ p: 3, textAlign: 'right' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
              onClick={handleSaveSettings}
              disabled={saving}
            >
              {saving ? '저장 중...' : '설정 저장'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default SettingsPage;