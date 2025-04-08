import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Box, 
  Paper, 
  TextField, 
  Button, 
  Typography, 
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  Tooltip,
  Chip,
  Grid,
  Alert,
  Snackbar
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';
import BuildIcon from '@mui/icons-material/Build';
import CodeIcon from '@mui/icons-material/Code';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import ToolsPanel from './ToolsPanel';
import { WebSocketManager } from './CustomWebSocketManager';

// 메시지 타입 정의
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: Date;
  toolCall?: any;
  toolResult?: any;
}

// 도구 정의
export interface Tool {
  id: string;
  name: string;
  description: string;
  parameters?: Record<string, any>;
  examples?: string[];
}

interface MCPChatInterfaceProps {
  initialMessages?: ChatMessage[];
  onReset?: () => void;
}

const MCPChatInterface: React.FC<MCPChatInterfaceProps> = ({ 
  initialMessages = [], 
  onReset 
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [showTools, setShowTools] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [llmConnected, setLlmConnected] = useState(false);
  const [llmStatus, setLlmStatus] = useState<string>('연결 중...');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocketManager | null>(null);
  const messageStreamRef = useRef<{[key: string]: string}>({});
  
  // LLM 연결 상태 확인
  const checkLLMStatus = useCallback(async () => {
    try {
      setLlmStatus('연결 확인 중...');
      
      const response = await axios.get('/api/mcp/status');
      if (response.data.success) {
        setLlmConnected(response.data.llm_studio.connected);
        setLlmStatus(response.data.llm_studio.connected ? 'LM Studio 연결됨' : 
                      `LM Studio 연결 오류: ${response.data.llm_studio.message}`);
      } else {
        setLlmConnected(false);
        setLlmStatus('LM Studio 연결 상태 확인 오류');
      }
    } catch (error) {
      console.error('LLM 상태 확인 오류:', error);
      setLlmConnected(false);
      setLlmStatus('LM Studio 연결 오류');
    }
  }, []);
  
  // 초기 LLM 상태 확인
  useEffect(() => {
    checkLLMStatus();
    // 30초마다 상태 확인
    const intervalId = setInterval(checkLLMStatus, 30000);
    
    return () => {
      clearInterval(intervalId);
    };
  }, [checkLLMStatus]);
  
  // 웹소켓 연결 설정
  useEffect(() => {
    // API_BASE_URL에서 프로토콜과 호스트 추출
    const apiUrl = new URL(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
    const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${apiUrl.host}/ws/chat/stream`;
    
    // WebSocketManager가 없는 경우만 새로 생성
    if (!wsRef.current) {
      console.log(`WebSocketManager 초기화: ${wsUrl}`);
      const wsManager = new WebSocketManager(wsUrl);
      
      // 서버에서 수신한 데이터 처리
      wsManager.onMessage((data) => {
        handleWebSocketMessage(data);
      });
      
      // 연결 가능한 상태 변경 처리
      wsManager.onStatusChange((status) => {
        setLlmConnected(status.connected);
        setLlmStatus(status.message);
        
        if (status.connected) {
          setSnackbarMessage('서버에 연결되었습니다');
          setSnackbarOpen(true);
          setError(null);
        } else if (status.message.includes('최대 재시도')) {
          setError(`채팅 서버에 연결할 수 없습니다. 페이지를 새로고침해주세요.`);
        }
      });
      
      // 오류 처리
      wsManager.onError(() => {
        setError(`서버 연결 오류가 발생했습니다. URL: ${wsUrl} - 페이지를 새로고침해 보세요.`);
      });
      
      wsRef.current = wsManager;
    }
    
    // 연결 시작
    wsRef.current.connect();
    
    // 페이지 포커스 시 재연결
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && wsRef.current && !wsRef.current.isConnected()) {
        wsRef.current.connect();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // 정리
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, []);
  
  // WebSocket 메시지 처리
  const handleWebSocketMessage = (data: any) => {
    const messageType = data.type;
    
    switch (messageType) {
      case 'connection_established':
        console.log('WebSocket 연결 설정됨:', data);
        // 서버에서 제공한 도구 목록 설정
        if (data.available_tools) {
          fetchToolDefinitions(data.available_tools);
        }
        break;
        
      case 'llm_connection_status':
        setLlmConnected(data.success);
        if (data.success) {
          setLlmStatus('LM Studio 연결됨');
        } else {
          setLlmStatus(`LM Studio 연결 오류: ${data.message}`);
        }
        break;
        
      case 'chat_request_received':
        console.log('요청 접수됨:', data.message_id);
        break;
        
      case 'chat_response_chunk':
        // 스트리밍 청크 처리
        handleResponseChunk(data);
        break;
        
      case 'chat_response_complete':
        // 응답 완료 처리
        finalizeResponse(data);
        break;
        
      case 'tool_call_detected':
        // 도구 호출 감지
        handleToolCallDetected(data);
        break;
        
      case 'tool_call_result':
        // 도구 호출 결과
        handleToolCallResult(data);
        break;
        
      case 'error':
        console.error('서버 오류:', data.message);
        setError(data.message);
        setIsLoading(false);
        break;
        
      default:
        console.log('알 수 없는 메시지 타입:', messageType, data);
    }
  };
  
  // 도구 정의 가져오기
  const fetchToolDefinitions = async (availableTools: string[]) => {
    try {
      const response = await axios.get('/api/mcp/functions');
      
      if (response.data && response.data.functions) {
        const toolDefinitions: Tool[] = [];
        
        // 사용 가능한 도구만 필터링
        for (const funcName of availableTools) {
          if (response.data.functions[funcName]) {
            const funcDef = response.data.functions[funcName];
            
            toolDefinitions.push({
              id: funcName,
              name: funcDef.name || funcName,
              description: funcDef.description || '설명 없음',
              parameters: funcDef.parameters || {},
              examples: funcDef.examples || []
            });
          }
        }
        
        setTools(toolDefinitions);
      }
    } catch (error) {
      console.error('도구 정의 가져오기 실패:', error);
      // 폴백: 기본 도구 설정
      setTools([
        {
          id: 'read_file',
          name: '파일 읽기',
          description: '파일 내용을 읽습니다.',
          examples: ['config.py 파일을 읽어줘', '프로젝트 설정 파일을 확인해야 해']
        },
        {
          id: 'list_directory',
          name: '디렉토리 목록',
          description: '디렉토리 내용을 나열합니다.',
          examples: ['src 디렉토리 내용 보여줘', '현재 디렉토리의 파일 목록은?']
        },
        {
          id: 'write_file',
          name: '파일 쓰기',
          description: '파일에 내용을 씁니다.',
          examples: ['이 코드를 새 파일로 저장해줘', '설정 파일을 생성해야 해']
        },
        {
          id: 'terminal_execute',
          name: '명령어 실행',
          description: '터미널 명령어를 실행합니다.',
          examples: ['pip list 명령어 실행해줘', '파이썬 버전 확인해줘']
        }
      ]);
    }
  };
  
  // 응답 청크 처리
  const handleResponseChunk = (data: any) => {
    const { message_id, chunk } = data;
    
    // 메시지 맵에 청크 추가
    if (messageStreamRef.current[message_id]) {
      messageStreamRef.current[message_id] += chunk;
    } else {
      messageStreamRef.current[message_id] = chunk;
    }
    
    // 기존 assistant 메시지 찾기
    const msgIndex = messages.findIndex(
      msg => msg.role === 'assistant' && msg.id === message_id
    );
    
    if (msgIndex >= 0) {
      // 기존 메시지 업데이트
      const updatedMessages = [...messages];
      updatedMessages[msgIndex] = {
        ...updatedMessages[msgIndex],
        content: messageStreamRef.current[message_id]
      };
      setMessages(updatedMessages);
    } else {
      // 새 메시지 추가
      setMessages(prev => [
        ...prev,
        {
          id: message_id,
          role: 'assistant',
          content: messageStreamRef.current[message_id],
          timestamp: new Date()
        }
      ]);
    }
    
    // 자동 스크롤
    scrollToBottom();
  };
  
  // 응답 완료 처리
  const finalizeResponse = (data: any) => {
    const { message_id, content } = data;
    
    // 스트리밍 참조에서 제거
    delete messageStreamRef.current[message_id];
    
    // 로딩 상태 해제
    setIsLoading(false);
    
    // 입력창 포커스
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };
  
  // 도구 호출 감지 처리
  const handleToolCallDetected = (data: any) => {
    console.log('도구 호출 감지됨:', data);
    
    // UI에 알림 표시 등 추가 가능
  };
  
  // 도구 호출 결과 처리
  const handleToolCallResult = (data: any) => {
    const { tool_call_id, tool_name, result } = data;
    
    // 도구 결과 메시지 추가
    setMessages(prev => [
      ...prev,
      {
        id: tool_call_id,
        role: 'tool',
        content: JSON.stringify(result, null, 2),
        timestamp: new Date(),
        toolCall: {
          name: tool_name
        }
      }
    ]);
    
    scrollToBottom();
  };
  
  // 자동 스크롤
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 메시지 전송
  const handleSendMessage = async () => {
    if (!input.trim() || isLoading || !wsRef.current || !wsRef.current.isConnected()) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      // 사용자 메시지 생성
      const userMessage: ChatMessage = {
        id: uuidv4(),
        role: 'user',
        content: input,
        timestamp: new Date()
      };
      
      // 사용자 메시지 즉시 표시
      setMessages(prev => [...prev, userMessage]);
      setInput('');
      
      // 대화 기록 추출
      const history = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // WebSocket을 통해 요청 전송
      wsRef.current.send({
        type: 'chat_request',
        prompt: input,
        history: history,
        options: {
          temperature: 0.7,
          max_tokens: 2000
        }
      });
      
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      setError('메시지를 전송할 수 없습니다. 다시 시도하세요.');
      setIsLoading(false);
    }
  };

  // 엔터 키 처리
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 대화 초기화
  const handleResetChat = () => {
    setMessages([]);
    setError(null);
    
    if (onReset) {
      onReset();
    }
    
    setSnackbarMessage('대화가 초기화되었습니다');
    setSnackbarOpen(true);
  };

  // 도구 패널 토글
  const toggleToolsPanel = () => {
    setShowTools(prev => !prev);
  };

  // 도구 선택 처리
  const handleToolSelect = (tool: Tool) => {
    const toolPrompt = `${tool.name} 도구를 사용해서 ${tool.examples?.[0] || '작업해줘'}`;
    setInput(toolPrompt);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };
  
  // 스낵바 닫기
  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  // 마크다운 렌더러 컴포넌트 (임시 일반 텍스트로 바꾸기)
  const MarkdownRenderer = ({ content }: { content: string }) => {
    // 상용구문을 일반 텍스트로 바꿈
    // 나중에 react-markdown을 설치하면 지워도 됩니다.
    return (
      <Typography
        variant="body1"
        component="div"
        sx={{
          whiteSpace: 'pre-wrap',
          fontFamily: '"Noto Sans KR", "Roboto", sans-serif',
          fontSize: '0.95rem',
          lineHeight: 1.6
        }}
      >
        {content}
      </Typography>
    );
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
      {/* 헤더 */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 2,
        borderBottom: '1px solid #eaeaea',
        pb: 1
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="h5" component="h1" sx={{ 
            fontWeight: 600, 
            mr: 1,
            color: '#333',
            fontFamily: '"Noto Sans KR", sans-serif'
          }}>
            MCP 대화
          </Typography>
          
          <Chip 
            icon={<CodeIcon fontSize="small" />}
            label={llmStatus}
            color={llmConnected ? "success" : "warning"}
            size="small"
            sx={{ ml: 1 }}
          />
          
          <Tooltip title="MCP 도구를 사용하여 지능적인 작업을 수행할 수 있습니다.">
            <IconButton size="small" sx={{ ml: 1 }}>
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Box>
          <Button 
            variant="outlined"
            color="secondary"
            onClick={toggleToolsPanel}
            startIcon={<BuildIcon />}
            sx={{ mr: 1 }}
          >
            도구 {showTools ? '숨기기' : '보기'}
          </Button>
          
          <Button 
            startIcon={<RefreshIcon />}
            variant="outlined"
            onClick={handleResetChat}
            disabled={isLoading}
          >
            대화 초기화
          </Button>
        </Box>
      </Box>
      
      {/* 오류 표시 */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}
      
      {/* 메인 레이아웃 - 메시지 목록과 도구 패널 */}
      <Grid container spacing={2} sx={{ flexGrow: 1, overflow: 'hidden' }}>
        {/* 메시지 목록 */}
        <Grid item xs={showTools ? 8 : 12}>
          <Paper 
            elevation={0}
            variant="outlined" 
            sx={{ 
              p: 2, 
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              borderRadius: 2
            }}
          >
            {/* 메시지 스크롤 영역 */}
            <Box sx={{ 
              flexGrow: 1, 
              overflow: 'auto',
              display: 'flex',
              flexDirection: 'column',
              px: 1
            }}>
              {messages.length === 0 ? (
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column',
                    justifyContent: 'center', 
                    alignItems: 'center',
                    height: '100%',
                    color: 'text.secondary'
                  }}
                >
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 500, color: '#555' }}>
                    MCP 에이전트와 대화를 시작하세요
                  </Typography>
                  <Typography variant="body2" sx={{ textAlign: 'center', maxWidth: '80%' }}>
                    질문하거나 작업을 요청하세요. 도구 패널에서 사용 가능한 도구를 확인할 수 있습니다.
                    <br />
                    예시: "프로젝트 구조를 분석해줘", "백엔드 코드에서 중요한 파일을 찾아줘"
                  </Typography>
                </Box>
              ) : (
                <>
                  {messages.map((msg, index) => {
                    // 연속된 메시지 그룹화
                    const isConsecutive = index > 0 && messages[index - 1].role === msg.role;
                    
                    return (
                      <Box 
                        key={msg.id} 
                        sx={{ 
                          mb: isConsecutive ? 1 : 2,
                          mt: isConsecutive ? 0 : 1,
                          alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                          maxWidth: msg.role === 'tool' ? '100%' : '85%'
                        }}
                      >
                        {/* 발신자 표시 (연속되지 않은 경우만) */}
                        {!isConsecutive && (
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              ml: msg.role === 'user' ? 'auto' : 1,
                              mr: msg.role === 'user' ? 1 : 'auto',
                              mb: 0.5,
                              color: 'text.secondary',
                              display: 'block',
                              textAlign: msg.role === 'user' ? 'right' : 'left',
                              fontWeight: 500
                            }}
                          >
                            {msg.role === 'user' ? '사용자' : 
                             msg.role === 'assistant' ? 'MCP 에이전트' : 
                             `도구: ${msg.toolCall?.name || '실행 결과'}`}
                          </Typography>
                        )}
                        
                        {/* 메시지 카드 */}
                        <Card 
                          variant={msg.role === 'user' ? 'outlined' : 'elevation'}
                          sx={{ 
                            bgcolor: msg.role === 'user' ? '#e3f2fd' : 
                                     msg.role === 'tool' ? '#f5f5f5' : '#f8f9fa',
                            boxShadow: msg.role === 'user' ? 'none' : '0 1px 3px rgba(0,0,0,0.1)',
                            borderRadius: 2,
                            overflow: 'hidden',
                            width: msg.role === 'tool' ? '100%' : 'auto'
                          }}
                        >
                          <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                            {/* 메시지 내용 */}
                            <Box sx={{ 
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              fontFamily: '"Noto Sans KR", "Roboto", sans-serif',
                              lineHeight: 1.6,
                              fontSize: '0.95rem',
                              '& code': {
                                backgroundColor: 'rgba(0,0,0,0.05)',
                                padding: '2px 4px',
                                borderRadius: 1,
                                fontFamily: 'monospace'
                              }
                            }}>
                              {msg.role === 'assistant' ? (
                                <MarkdownRenderer content={msg.content} />
                              ) : msg.role === 'tool' ? (
                                <Box>
                                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                    {msg.toolCall?.name || '도구 실행 결과'}
                                  </Typography>
                                  <Box sx={{ 
                                    bgcolor: 'rgba(0,0,0,0.03)',
                                    p: 1.5,
                                    borderRadius: 1,
                                    fontFamily: 'monospace',
                                    fontSize: '0.85rem',
                                    overflow: 'auto',
                                    maxHeight: '300px'
                                  }}>
                                    <pre style={{ margin: 0 }}>{msg.content}</pre>
                                  </Box>
                                </Box>
                              ) : (
                                msg.content
                              )}
                            </Box>
                          </CardContent>
                        </Card>
                        
                        {/* 메시지 시간 */}
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            display: 'block',
                            color: 'text.disabled',
                            mt: 0.5,
                            textAlign: msg.role === 'user' ? 'right' : 'left',
                            fontSize: '0.7rem',
                            ml: msg.role === 'user' ? 'auto' : 1,
                            mr: msg.role === 'user' ? 1 : 'auto',
                          }}
                        >
                          {msg.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Box>
                    );
                  })}
                  
                  {/* 로딩 표시 */}
                  {isLoading && (
                    <Box sx={{ alignSelf: 'flex-start', ml: 2, mb: 2 }}>
                      <CircularProgress size={20} thickness={5} />
                    </Box>
                  )}
                  
                  <div ref={messagesEndRef} />
                </>
              )}
            </Box>
          </Paper>
        </Grid>
        
        {/* 도구 패널 */}
        {showTools && (
          <Grid item xs={4}>
            <ToolsPanel 
              tools={tools}
              onSelect={handleToolSelect}
            />
          </Grid>
        )}
      </Grid>
      
      {/* 입력 영역 */}
      <Paper 
        elevation={0}
        variant="outlined"
        sx={{ 
          p: 2, 
          mt: 2,
          display: 'flex', 
          alignItems: 'center',
          borderRadius: 2
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="MCP 에이전트에게 메시지 입력..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || !llmConnected}
          multiline
          maxRows={4}
          inputRef={inputRef}
          InputProps={{
            sx: { 
              borderRadius: 2,
              fontFamily: '"Noto Sans KR", "Roboto", sans-serif',
              fontSize: '0.95rem'
            }
          }}
        />
        <Button
          variant="contained"
          color="primary"
          endIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          onClick={handleSendMessage}
          disabled={isLoading || !input.trim() || !llmConnected}
          sx={{ 
            ml: 2, 
            height: 54,
            borderRadius: 2,
            px: 3
          }}
        >
          보내기
        </Button>
      </Paper>
      
      {/* 알림 스낵바 */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={handleSnackbarClose}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default MCPChatInterface;