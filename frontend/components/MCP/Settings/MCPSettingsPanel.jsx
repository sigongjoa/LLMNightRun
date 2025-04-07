import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  Grid, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem,
  Divider,
  Snackbar,
  Alert,
  IconButton,
  Card,
  CardContent,
  CardActions,
  Switch,
  FormControlLabel,
  Chip
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Save as SaveIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import axios from 'axios';

const MCPSettingsPanel = () => {
  // State for MCP settings
  const [settings, setSettings] = useState({
    contexts: [],
    functionGroups: [],
    currentContext: null,
    currentFunctionGroup: null
  });

  // State for form inputs
  const [newContext, setNewContext] = useState({ 
    name: '', 
    data: '',
    llmConfig: {
      provider: 'local',
      baseUrl: 'http://localhost:1234/v1',
      apiKey: '',
      model: 'local-model'
    }
  });

  // 컨텍스트 생성 폼이 유효한지 검증
  const isFormValid = Boolean(newContext.name.trim());

  // Alert state
  const [alert, setAlert] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

  // Load contexts and function groups on component mount
  useEffect(() => {
    fetchMCPData();
  }, []);

  // Fetch MCP data from backend
  const fetchMCPData = async () => {
    try {
      // Fetch contexts
      const contextsResponse = await axios.get('/mcp/v1/contexts');
      
      // Fetch function groups
      const functionGroupsResponse = await axios.get('/mcp/v1/function-groups');
      
      setSettings({
        contexts: contextsResponse.data.contexts || [],
        functionGroups: functionGroupsResponse.data.function_groups || [],
        currentContext: null,
        currentFunctionGroup: null
      });
      
      showAlert('MCP 데이터를 성공적으로 로드했습니다.', 'success');
    } catch (error) {
      console.error('MCP 데이터 로드 실패:', error);
      showAlert('MCP 데이터 로드 실패: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  // Show alert helper
  const showAlert = (message, severity = 'info') => {
    setAlert({
      open: true,
      message,
      severity
    });
  };

  // Close alert helper
  const handleAlertClose = () => {
    setAlert(prev => ({ ...prev, open: false }));
  };

  // Handle context selection
  const handleContextSelect = async (contextId) => {
    try {
      const response = await axios.get(`/mcp/v1/contexts/${contextId}`);
      setSettings(prev => ({
        ...prev,
        currentContext: response.data
      }));
    } catch (error) {
      console.error('컨텍스트 로드 실패:', error);
      showAlert('컨텍스트 로드 실패: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  // Handle function group selection
  const handleFunctionGroupSelect = async (groupName) => {
    try {
      const response = await axios.get(`/mcp/v1/function-groups/${groupName}`);
      setSettings(prev => ({
        ...prev,
        currentFunctionGroup: response.data
      }));
    } catch (error) {
      console.error('함수 그룹 로드 실패:', error);
      showAlert('함수 그룹 로드 실패: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  // Create new context
  const handleCreateContext = async () => {
    try {
      // 컨텍스트 이름 검증
      if (!newContext.name.trim()) {
        showAlert('컨텍스트 이름을 입력해주세요.', 'error');
        return;
      }

      // Format context data as JSON if it's a string
      let contextData = {};
      
      if (typeof newContext.data === 'string' && newContext.data.trim()) {
        try {
          contextData = JSON.parse(newContext.data);
        } catch (e) {
          showAlert('컨텍스트 데이터는 유효한 JSON 형식이어야 합니다.', 'error');
          return;
        }
      }

      // Add context name and LLM configuration
      contextData.name = newContext.name;
      contextData.llm_config = newContext.llmConfig;
      
      console.log('컨텍스트 생성 데이터:', contextData);
      
      // Create context
      const response = await axios.post('/mcp/v1/contexts', contextData);
      
      showAlert(`컨텍스트 "${newContext.name}" 생성 성공!`, 'success');
      
      // Reset form and refresh data
      setNewContext({ 
        name: '', 
        data: '',
        llmConfig: {
          provider: 'local',
          baseUrl: 'http://localhost:1234/v1',
          apiKey: '',
          model: 'local-model'
        }
      });
      
      fetchMCPData();
    } catch (error) {
      console.error('컨텍스트 생성 실패:', error);
      showAlert('컨텍스트 생성 실패: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  // Delete context
  const handleDeleteContext = async (contextId) => {
    if (!confirm(`컨텍스트 ${contextId}를 삭제하시겠습니까?`)) {
      return;
    }
    
    try {
      await axios.delete(`/mcp/v1/contexts/${contextId}`);
      showAlert(`컨텍스트 "${contextId}" 삭제 성공!`, 'success');
      
      // Clear current context if it's the one being deleted
      if (settings.currentContext && settings.currentContext.context_id === contextId) {
        setSettings(prev => ({
          ...prev,
          currentContext: null
        }));
      }
      
      fetchMCPData();
    } catch (error) {
      console.error('컨텍스트 삭제 실패:', error);
      showAlert('컨텍스트 삭제 실패: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  // Save updated context
  const handleSaveContext = async () => {
    if (!settings.currentContext) return;
    
    try {
      const response = await axios.post(
        `/mcp/v1/contexts/${settings.currentContext.context_id}`,
        settings.currentContext.data
      );
      
      showAlert('컨텍스트 업데이트 성공!', 'success');
      fetchMCPData();
    } catch (error) {
      console.error('컨텍스트 업데이트 실패:', error);
      showAlert('컨텍스트 업데이트 실패: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  // Test MCP connection with local LLM
  const handleTestConnection = async () => {
    if (!settings.currentContext) {
      showAlert('테스트할 컨텍스트를 선택해주세요.', 'warning');
      return;
    }
    
    try {
      // Create a simple test message to the MCP
      const testMessage = {
        type: "mcp_test",
        content: {
          message: "Hello from LLMNightRun!",
          context_id: settings.currentContext.context_id
        },
        request_id: `test-${Date.now()}`
      };
      
      console.log('Sending MCP test message:', testMessage);
      
      const response = await axios.post('/mcp/v1/process', testMessage);
      
      console.log('MCP test response:', response.data);
      
      if (response.data.success) {
        showAlert(`MCP 연결 테스트 성공! 로컬 LLM과 연결되었습니다.\n${response.data.llm_response ? '응답 받음' : ''}`, 'success');
        // 응답 데이터를 콘솔에 기록
        if (response.data.llm_response) {
          console.log('LLM 응답:', response.data.llm_response);
        }
      } else {
        showAlert('MCP 연결 실패: ' + (response.data.content?.message || response.data.error || '알 수 없는 오류'), 'error');
      }
    } catch (error) {
      console.error('MCP 연결 테스트 실패:', error);
      showAlert('MCP 연결 테스트 실패: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  // Update LLM config fields
  const handleLLMConfigChange = (field, value) => {
    setNewContext(prev => ({
      ...prev,
      llmConfig: {
        ...prev.llmConfig,
        [field]: value
      }
    }));
  };

  // Parse and format JSON for display
  const formatJSON = (jsonData) => {
    if (!jsonData) return '';
    try {
      return typeof jsonData === 'string' 
        ? jsonData 
        : JSON.stringify(jsonData, null, 2);
    } catch (e) {
      return String(jsonData);
    }
  };

  // 컨텍스트 생성 버튼 스타일 - 더 높은 높이와 더 강조된 색상 사용
  const createButtonStyle = {
    mt: 4, // 더 넓은 상단 여백
    mb: 2, // 하단 여백 추가
    py: 2, // 높이 증가
    fontSize: '1.2rem', // 글자 크기 증가
    fontWeight: 'bold',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#2196f3', // 더 밝은 프라이머리 커스텀 색상
    '&:hover': {
      backgroundColor: '#1976d2', // 호버 색상
    },
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', // 그림자 추가
    borderRadius: '8px', // 모서리 더 둥글게
  };
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        MCP 설정 관리
      </Typography>
      
      <Grid container spacing={3}>
        {/* Left panel: Create new context */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 'auto', minHeight: '600px', overflow: 'auto', maxHeight: 'calc(100vh - 250px)', boxShadow: 3 }}>
            <Typography variant="h6" gutterBottom>
              새 MCP 컨텍스트 생성
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="컨텍스트 이름 *"
                  value={newContext.name}
                  onChange={(e) => setNewContext(prev => ({ ...prev, name: e.target.value }))}
                  margin="normal"
                  required
                  helperText="컨텍스트 이름을 반드시 입력해주세요."
                  variant="outlined"
                  InputProps={{
                    sx: { fontSize: '1.1rem', fontWeight: 500 },
                  }}
                  FormHelperTextProps={{
                    sx: { fontSize: '0.9rem' }
                  }}
                />
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  LLM 설정
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>LLM 제공자</InputLabel>
                  <Select
                    value={newContext.llmConfig.provider}
                    onChange={(e) => handleLLMConfigChange('provider', e.target.value)}
                    label="LLM 제공자"
                  >
                    <MenuItem value="local">로컬 LLM</MenuItem>
                    <MenuItem value="openai">OpenAI</MenuItem>
                    <MenuItem value="anthropic">Anthropic</MenuItem>
                    <MenuItem value="custom">커스텀</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="모델 이름"
                  value={newContext.llmConfig.model}
                  onChange={(e) => handleLLMConfigChange('model', e.target.value)}
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="베이스 URL"
                  value={newContext.llmConfig.baseUrl}
                  onChange={(e) => handleLLMConfigChange('baseUrl', e.target.value)}
                  margin="normal"
                  placeholder="http://localhost:1234/v1"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="API 키 (필요시)"
                  value={newContext.llmConfig.apiKey}
                  onChange={(e) => handleLLMConfigChange('apiKey', e.target.value)}
                  margin="normal"
                  type="password"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  추가 컨텍스트 데이터 (JSON)
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={5}
                  value={newContext.data}
                  onChange={(e) => setNewContext(prev => ({ ...prev, data: e.target.value }))}
                  margin="normal"
                  placeholder="{}"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Button 
                  variant="contained" 
                  startIcon={<AddIcon />}
                  onClick={handleCreateContext}
                  fullWidth
                  sx={createButtonStyle}
                  disabled={!isFormValid}
                  color="primary"
                >
                  컨텍스트 생성
                </Button>
                {!isFormValid && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
                    컨텍스트 이름을 입력해야 버튼이 활성화됩니다.
                  </Typography>
                )}
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        {/* Right panel: Manage existing contexts */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 'auto', minHeight: '600px', overflow: 'auto', maxHeight: 'calc(100vh - 250px)', boxShadow: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                기존 MCP 컨텍스트
              </Typography>
              
              <Button 
                startIcon={<RefreshIcon />}
                onClick={fetchMCPData}
                size="small"
              >
                새로고침
              </Button>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              {settings.contexts.length > 0 ? (
                settings.contexts.map((contextId) => (
                  <Card key={contextId} sx={{ mb: 2 }}>
                    <CardContent sx={{ py: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body1">{contextId}</Typography>
                        <Box>
                          <Button 
                            size="small" 
                            onClick={() => handleContextSelect(contextId)}
                          >
                            선택
                          </Button>
                          <IconButton 
                            color="error" 
                            size="small"
                            onClick={() => handleDeleteContext(contextId)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  생성된 컨텍스트가 없습니다.
                </Typography>
              )}
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="h6" gutterBottom>
              선택된 컨텍스트
            </Typography>
            
            {settings.currentContext ? (
              <>
                <Typography variant="subtitle1">
                  {settings.currentContext.context_id}
                </Typography>
                
                <TextField
                  fullWidth
                  multiline
                  rows={8}
                  value={formatJSON(settings.currentContext.data)}
                  onChange={(e) => {
                    try {
                      const newData = JSON.parse(e.target.value);
                      setSettings(prev => ({
                        ...prev,
                        currentContext: {
                          ...prev.currentContext,
                          data: newData
                        }
                      }));
                    } catch (error) {
                      // JSON 파싱 오류 시 텍스트 값 그대로 저장
                      setSettings(prev => ({
                        ...prev,
                        currentContext: {
                          ...prev.currentContext,
                          data: e.target.value
                        }
                      }));
                    }
                  }}
                  margin="normal"
                />
                
                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                  <Button 
                    variant="contained" 
                    startIcon={<SaveIcon />}
                    onClick={handleSaveContext}
                    color="primary"
                  >
                    변경사항 저장
                  </Button>
                  
                  <Button 
                    variant="outlined"
                    onClick={handleTestConnection}
                  >
                    LLM 연결 테스트
                  </Button>
                </Box>
              </>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                컨텍스트를 선택해주세요.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      {/* Alert snackbar */}
      <Snackbar
        open={alert.open}
        autoHideDuration={6000}
        onClose={handleAlertClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleAlertClose} 
          severity={alert.severity} 
          sx={{ width: '100%' }}
        >
          {alert.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MCPSettingsPanel;
