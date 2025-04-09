import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Grid,
  Box,
  Card,
  CardContent,
  CardHeader,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Tooltip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';
import SaveIcon from '@mui/icons-material/Save';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import axios from 'axios';

// TabPanel Component
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
      id={`ai-environment-tabpanel-${index}`}
      aria-labelledby={`ai-environment-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `ai-environment-tab-${index}`,
    'aria-controls': `ai-environment-tabpanel-${index}`,
  };
}

const AIEnvironment = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // LLM 모델 설정
  const [llmModels, setLlmModels] = useState<any[]>([]);
  const [selectedLLM, setSelectedLLM] = useState('');
  const [llmConfig, setLlmConfig] = useState({
    maxTokens: 2048,
    temperature: 0.7,
    promptTemplate: '',
    useStreaming: true,
    contextWindow: 4096,
    apiEndpoint: ''
  });

  // 벡터 스토어 설정
  const [vectorStoreType, setVectorStoreType] = useState('chroma');
  const [vectorStoreConfig, setVectorStoreConfig] = useState({
    collectionName: 'default_collection',
    embeddingModel: 'text-embedding-ada-002',
    chunkSize: 1000,
    chunkOverlap: 200
  });

  // API 키 설정
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    anthropic: '',
    cohere: '',
    huggingface: ''
  });

  // 자동화 설정
  const [automationConfig, setAutomationConfig] = useState({
    autoEmbedding: true,
    autoReindex: false,
    scheduledMaintenance: false,
    maintenanceInterval: 'daily'
  });

  // 기능 활성화/비활성화 토글
  const [featureFlags, setFeatureFlags] = useState({
    localLLM: true,
    cloudLLM: true,
    vectorStore: true,
    documentProcessing: true,
    agentMode: true,
    mcpIntegration: true
  });

  // 데이터 로딩
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // 실제로는 API 요청을 해야 하지만 지금은 더미 데이터로 대체
        // const response = await axios.get('/api/ai-environment/config');
        // 더미 데이터로 모델 목록 설정
        setLlmModels([
          { id: 'gpt-4', name: 'GPT-4 (OpenAI)', type: 'cloud' },
          { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo (OpenAI)', type: 'cloud' },
          { id: 'claude-3-opus', name: 'Claude 3 Opus (Anthropic)', type: 'cloud' },
          { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet (Anthropic)', type: 'cloud' },
          { id: 'llama-3-70b', name: 'Llama 3 70B (Local)', type: 'local' },
          { id: 'llama-3-8b', name: 'Llama 3 8B (Local)', type: 'local' },
          { id: 'mistral-7b', name: 'Mistral 7B (Local)', type: 'local' },
        ]);
        setSelectedLLM('gpt-3.5-turbo');

        // 나머지 설정들도 데모 데이터로 로드할 수 있음
        setLoading(false);
      } catch (err) {
        setError('설정을 로드하는 중 오류가 발생했습니다.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 설정 저장 핸들러
  const handleSaveConfig = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // 실제로는 API 요청을 해야 함
      // await axios.post('/api/ai-environment/config', {
      //   llm: { model: selectedLLM, ...llmConfig },
      //   vectorStore: { type: vectorStoreType, ...vectorStoreConfig },
      //   apiKeys,
      //   automation: automationConfig,
      //   featureFlags
      // });

      // 지금은 저장 성공으로 가정
      setSuccess('설정이 성공적으로 저장되었습니다.');
      setLoading(false);
    } catch (err) {
      setError('설정을 저장하는 중 오류가 발생했습니다.');
      setLoading(false);
    }
  };

  // LLM 모델 변경 핸들러
  const handleModelChange = (event: any) => {
    const modelId = event.target.value;
    setSelectedLLM(modelId);

    // 모델에 따라 기본 설정 변경
    if (modelId.includes('gpt')) {
      setLlmConfig({
        ...llmConfig,
        maxTokens: 2048,
        contextWindow: 8192,
        apiEndpoint: 'https://api.openai.com/v1'
      });
    } else if (modelId.includes('claude')) {
      setLlmConfig({
        ...llmConfig,
        maxTokens: 4096,
        contextWindow: 100000,
        apiEndpoint: 'https://api.anthropic.com/v1'
      });
    } else if (modelId.includes('llama')) {
      setLlmConfig({
        ...llmConfig,
        maxTokens: 2048,
        contextWindow: 4096,
        apiEndpoint: 'http://localhost:8080/v1'
      });
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI 환경설정
      </Typography>
      <Typography variant="body1" paragraph>
        LLM 모델, 벡터 스토어, API 키 및 자동화 설정을 구성하여 AI 환경을 최적화하세요.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
          aria-label="AI 환경설정 탭"
        >
          <Tab label="LLM 모델" {...a11yProps(0)} />
          <Tab label="벡터 스토어" {...a11yProps(1)} />
          <Tab label="API 키" {...a11yProps(2)} />
          <Tab label="자동화" {...a11yProps(3)} />
          <Tab label="기능 토글" {...a11yProps(4)} />
        </Tabs>

        {/* LLM 모델 탭 */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardHeader title="LLM 모델 설정" />
                <CardContent>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel id="llm-model-select-label">LLM 모델</InputLabel>
                        <Select
                          labelId="llm-model-select-label"
                          id="llm-model-select"
                          value={selectedLLM}
                          label="LLM 모델"
                          onChange={handleModelChange}
                        >
                          <MenuItem value="" disabled>
                            <em>모델을 선택하세요</em>
                          </MenuItem>
                          <MenuItem value="divider" disabled>
                            <Divider textAlign="left"><Chip label="클라우드 모델" /></Divider>
                          </MenuItem>
                          {llmModels
                            .filter(model => model.type === 'cloud')
                            .map(model => (
                              <MenuItem key={model.id} value={model.id}>
                                {model.name}
                              </MenuItem>
                            ))}
                          <MenuItem value="divider2" disabled>
                            <Divider textAlign="left"><Chip label="로컬 모델" /></Divider>
                          </MenuItem>
                          {llmModels
                            .filter(model => model.type === 'local')
                            .map(model => (
                              <MenuItem key={model.id} value={model.id}>
                                {model.name}
                              </MenuItem>
                            ))}
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="API 엔드포인트"
                        value={llmConfig.apiEndpoint}
                        onChange={(e) => setLlmConfig({ ...llmConfig, apiEndpoint: e.target.value })}
                        helperText="모델 API의 엔드포인트 URL"
                      />
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        type="number"
                        label="최대 토큰"
                        value={llmConfig.maxTokens}
                        onChange={(e) => setLlmConfig({ ...llmConfig, maxTokens: parseInt(e.target.value) })}
                        InputProps={{ inputProps: { min: 1 } }}
                      />
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        type="number"
                        label="온도"
                        value={llmConfig.temperature}
                        onChange={(e) => setLlmConfig({ ...llmConfig, temperature: parseFloat(e.target.value) })}
                        InputProps={{ inputProps: { min: 0, max: 2, step: 0.1 } }}
                        helperText="0(결정적)에서 2(창의적) 사이의 값"
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        multiline
                        rows={4}
                        label="프롬프트 템플릿"
                        value={llmConfig.promptTemplate}
                        onChange={(e) => setLlmConfig({ ...llmConfig, promptTemplate: e.target.value })}
                        helperText="기본 프롬프트 템플릿을 설정합니다. {input}, {context} 등의 변수를 사용할 수 있습니다."
                      />
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={llmConfig.useStreaming}
                            onChange={(e) => setLlmConfig({ ...llmConfig, useStreaming: e.target.checked })}
                          />
                        }
                        label="스트리밍 응답 사용"
                      />
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        type="number"
                        label="컨텍스트 윈도우"
                        value={llmConfig.contextWindow}
                        onChange={(e) => setLlmConfig({ ...llmConfig, contextWindow: parseInt(e.target.value) })}
                        InputProps={{ inputProps: { min: 1 } }}
                        helperText="모델의 최대 컨텍스트 길이 (토큰)"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* 벡터 스토어 탭 */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardHeader title="벡터 스토어 설정" />
                <CardContent>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel id="vector-store-select-label">벡터 스토어 타입</InputLabel>
                        <Select
                          labelId="vector-store-select-label"
                          id="vector-store-select"
                          value={vectorStoreType}
                          label="벡터 스토어 타입"
                          onChange={(e) => setVectorStoreType(e.target.value)}
                        >
                          <MenuItem value="chroma">Chroma</MenuItem>
                          <MenuItem value="faiss">FAISS</MenuItem>
                          <MenuItem value="pinecone">Pinecone</MenuItem>
                          <MenuItem value="weaviate">Weaviate</MenuItem>
                          <MenuItem value="milvus">Milvus</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="컬렉션 이름"
                        value={vectorStoreConfig.collectionName}
                        onChange={(e) => setVectorStoreConfig({ ...vectorStoreConfig, collectionName: e.target.value })}
                      />
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel id="embedding-model-select-label">임베딩 모델</InputLabel>
                        <Select
                          labelId="embedding-model-select-label"
                          id="embedding-model-select"
                          value={vectorStoreConfig.embeddingModel}
                          label="임베딩 모델"
                          onChange={(e) => setVectorStoreConfig({ ...vectorStoreConfig, embeddingModel: e.target.value })}
                        >
                          <MenuItem value="text-embedding-ada-002">OpenAI Text Embedding Ada 002</MenuItem>
                          <MenuItem value="text-embedding-3-small">OpenAI Text Embedding 3 Small</MenuItem>
                          <MenuItem value="text-embedding-3-large">OpenAI Text Embedding 3 Large</MenuItem>
                          <MenuItem value="all-MiniLM-L6-v2">Sentence Transformers (all-MiniLM-L6-v2)</MenuItem>
                          <MenuItem value="bge-large-en-v1.5">BGE Large English v1.5</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        type="number"
                        label="청크 크기"
                        value={vectorStoreConfig.chunkSize}
                        onChange={(e) => setVectorStoreConfig({ ...vectorStoreConfig, chunkSize: parseInt(e.target.value) })}
                        InputProps={{ inputProps: { min: 100 } }}
                        helperText="각 텍스트 청크의 최대 크기 (토큰)"
                      />
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        type="number"
                        label="청크 오버랩"
                        value={vectorStoreConfig.chunkOverlap}
                        onChange={(e) => setVectorStoreConfig({ ...vectorStoreConfig, chunkOverlap: parseInt(e.target.value) })}
                        InputProps={{ inputProps: { min: 0 } }}
                        helperText="각 청크 간 오버랩되는 토큰 수"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* API 키 탭 */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardHeader 
                  title="API 키 설정" 
                  subheader="API 키는 안전하게 저장됩니다."
                  action={
                    <Tooltip title="API 키는 암호화되어 저장됩니다.">
                      <InfoIcon color="primary" />
                    </Tooltip>
                  }
                />
                <CardContent>
                  <Grid container spacing={3}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="OpenAI API 키"
                        type="password"
                        value={apiKeys.openai}
                        onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
                        placeholder="sk-..."
                        helperText="OpenAI API 키 (GPT 모델 및 임베딩에 필요)"
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Anthropic API 키"
                        type="password"
                        value={apiKeys.anthropic}
                        onChange={(e) => setApiKeys({ ...apiKeys, anthropic: e.target.value })}
                        placeholder="sk-ant-..."
                        helperText="Anthropic API 키 (Claude 모델에 필요)"
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Cohere API 키"
                        type="password"
                        value={apiKeys.cohere}
                        onChange={(e) => setApiKeys({ ...apiKeys, cohere: e.target.value })}
                        helperText="Cohere API 키 (선택 사항)"
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="HuggingFace API 키"
                        type="password"
                        value={apiKeys.huggingface}
                        onChange={(e) => setApiKeys({ ...apiKeys, huggingface: e.target.value })}
                        helperText="HuggingFace API 키 (선택 사항)"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* 자동화 탭 */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardHeader title="자동화 설정" />
                <CardContent>
                  <Grid container spacing={3}>
                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={automationConfig.autoEmbedding}
                            onChange={(e) => setAutomationConfig({ ...automationConfig, autoEmbedding: e.target.checked })}
                          />
                        }
                        label="자동 임베딩"
                      />
                      <Typography variant="body2" color="text.secondary">
                        새 문서가 추가될 때 자동으로 임베딩을 생성합니다.
                      </Typography>
                    </Grid>

                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={automationConfig.autoReindex}
                            onChange={(e) => setAutomationConfig({ ...automationConfig, autoReindex: e.target.checked })}
                          />
                        }
                        label="자동 재인덱싱"
                      />
                      <Typography variant="body2" color="text.secondary">
                        문서가 변경될 때 자동으로 재인덱싱합니다.
                      </Typography>
                    </Grid>

                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={automationConfig.scheduledMaintenance}
                            onChange={(e) => setAutomationConfig({ ...automationConfig, scheduledMaintenance: e.target.checked })}
                          />
                        }
                        label="예약된 유지보수"
                      />
                      <Typography variant="body2" color="text.secondary">
                        벡터 스토어와 데이터베이스의 예약된 유지 보수를 활성화합니다.
                      </Typography>
                    </Grid>

                    {automationConfig.scheduledMaintenance && (
                      <Grid item xs={12} md={6}>
                        <FormControl fullWidth>
                          <InputLabel id="maintenance-interval-select-label">유지보수 간격</InputLabel>
                          <Select
                            labelId="maintenance-interval-select-label"
                            id="maintenance-interval-select"
                            value={automationConfig.maintenanceInterval}
                            label="유지보수 간격"
                            onChange={(e) => setAutomationConfig({ ...automationConfig, maintenanceInterval: e.target.value })}
                          >
                            <MenuItem value="daily">매일</MenuItem>
                            <MenuItem value="weekly">매주</MenuItem>
                            <MenuItem value="biweekly">격주</MenuItem>
                            <MenuItem value="monthly">매월</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* 기능 토글 탭 */}
        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardHeader title="기능 토글" />
                <CardContent>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={featureFlags.localLLM}
                            onChange={(e) => setFeatureFlags({ ...featureFlags, localLLM: e.target.checked })}
                          />
                        }
                        label="로컬 LLM"
                      />
                      <Typography variant="body2" color="text.secondary">
                        로컬에서 실행되는 LLM 모델 활성화
                      </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={featureFlags.cloudLLM}
                            onChange={(e) => setFeatureFlags({ ...featureFlags, cloudLLM: e.target.checked })}
                          />
                        }
                        label="클라우드 LLM"
                      />
                      <Typography variant="body2" color="text.secondary">
                        OpenAI, Anthropic 등의 클라우드 LLM 활성화
                      </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={featureFlags.vectorStore}
                            onChange={(e) => setFeatureFlags({ ...featureFlags, vectorStore: e.target.checked })}
                          />
                        }
                        label="벡터 스토어"
                      />
                      <Typography variant="body2" color="text.secondary">
                        문서 검색을 위한 벡터 스토어 기능 활성화
                      </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={featureFlags.documentProcessing}
                            onChange={(e) => setFeatureFlags({ ...featureFlags, documentProcessing: e.target.checked })}
                          />
                        }
                        label="문서 처리"
                      />
                      <Typography variant="body2" color="text.secondary">
                        문서 파싱 및 처리 파이프라인 활성화
                      </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={featureFlags.agentMode}
                            onChange={(e) => setFeatureFlags({ ...featureFlags, agentMode: e.target.checked })}
                          />
                        }
                        label="에이전트 모드"
                      />
                      <Typography variant="body2" color="text.secondary">
                        ReAct 및 기타 에이전트 기반 추론 활성화
                      </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={featureFlags.mcpIntegration}
                            onChange={(e) => setFeatureFlags({ ...featureFlags, mcpIntegration: e.target.checked })}
                          />
                        }
                        label="MCP 통합"
                      />
                      <Typography variant="body2" color="text.secondary">
                        MCP(Model Control Panel) 기능 통합 활성화
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          sx={{ mr: 2 }}
          onClick={() => window.location.reload()}
        >
          재설정
        </Button>
        <Button
          variant="contained"
          color="primary"
          startIcon={loading ? <CircularProgress size={24} color="inherit" /> : <SaveIcon />}
          onClick={handleSaveConfig}
          disabled={loading}
        >
          설정 저장
        </Button>
      </Box>
    </Box>
  );
};

export default AIEnvironment;