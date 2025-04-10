import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Box, 
  Paper, 
  TextField, 
  Button, 
  Typography, 
  CircularProgress,
  Divider, 
  IconButton,
  Card,
  CardContent,
  Tooltip,
  Chip,
  Grid
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import ToolsPanel from './ToolsPanel';
import { ExportToMemoryButton } from '../Memory';

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
  icon?: React.ReactNode;
  parameters?: Record<string, any>;
  examples?: string[];
}

interface ChatInterfaceProps {
  initialMessages?: ChatMessage[];
  onReset?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  initialMessages = [], 
  onReset 
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agentId, setAgentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [showTools, setShowTools] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const lastMessageTimestamp = useRef<number>(Date.now());

  // 사용 가능한 도구 설정
  useEffect(() => {
    // 도구 목록 - 실제 백엔드 API에서 가져올 수 있음
    const availableTools: Tool[] = [
      {
        id: 'file_search',
        name: '파일 검색',
        description: '시스템에서 파일을 검색합니다.',
        examples: ['프로젝트에서 Python 파일을 찾아줘', '데이터 폴더에서 CSV 파일 검색']
      },
      {
        id: 'python_execute',
        name: 'Python 코드 실행',
        description: 'Python 코드를 실행하고 결과를 반환합니다.',
        examples: ['이 데이터를 분석해줘', 'pandas로 CSV 파일 처리']
      },
      {
        id: 'github_tool',
        name: 'GitHub 통합',
        description: 'GitHub 저장소를 조회하고 관리합니다.',
        examples: ['내 저장소 목록 보여줘', 'PR 상태 확인']
      },
      {
        id: 'str_replace_editor',
        name: '텍스트 편집',
        description: '파일 내용을 편집합니다.',
        examples: ['이 파일의 첫 줄을 수정해줘', '모든 print 문을 로그로 변경']
      },
      {
        id: 'terminate',
        name: '대화 종료',
        description: '현재 에이전트 세션을 종료합니다.',
        examples: ['대화를 끝내줘', '작업 종료']
      }
    ];
    
    setTools(availableTools);
  }, []);

  // 자동 스크롤
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 에이전트 생성
  const createAgent = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await axios.post('/api/agent/create');
      const newAgentId = response.data.agent_id;
      setAgentId(newAgentId);
      console.log('에이전트 생성됨:', newAgentId);
      
      // 서버에서 초기 메시지가 있다면 추가
      if (response.data.messages && response.data.messages.length > 0) {
        const formattedMessages = response.data.messages.map((msg: any) => ({
          id: msg.id || uuidv4(),
          role: msg.role,
          content: msg.content || '',
          timestamp: new Date()
        }));
        setMessages(formattedMessages);
      }
      
      return newAgentId;
    } catch (error) {
      console.error('에이전트 생성 오류:', error);
      setError('에이전트를 생성할 수 없습니다. 서버 연결을 확인하세요.');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 초기 에이전트 생성
  useEffect(() => {
    createAgent();
  }, [createAgent]);

  // 메시지 폴링 (websocket으로 대체 가능)
  useEffect(() => {
    if (!agentId) return;
    
    let pollingInterval: NodeJS.Timeout;
    
    const pollMessages = async () => {
      try {
        const response = await axios.get(`/api/agent/${agentId}/status`);
        
        if (response.data && Array.isArray(response.data.messages)) {
          const serverMessages = response.data.messages;
          
          // 새 메시지만 추가
          const currentTimestamp = Date.now();
          if (serverMessages.length > 0 && 
             (messages.length === 0 || currentTimestamp - lastMessageTimestamp.current > 1000)) {
            
            // 기존 메시지 ID 추적
            const existingIds = new Set(messages.map(m => m.id));
            
            // 새 메시지만 필터링
            const newMessages = serverMessages
              .filter((msg: any) => !existingIds.has(msg.id))
              .map((msg: any) => ({
                id: msg.id || uuidv4(),
                role: msg.role,
                content: msg.content || '',
                timestamp: new Date(),
                toolCall: msg.tool_calls ? msg.tool_calls[0] : null
              }));
              
            if (newMessages.length > 0) {
              // 시스템 메시지 필터링
              const filteredMessages = newMessages.filter(
                (msg: any) => msg.role !== 'system' && 
                !msg.content.includes('반복된 응답이 감지되었습니다')
              );
              
              if (filteredMessages.length > 0) {
                setMessages(prev => [...prev, ...filteredMessages]);
                lastMessageTimestamp.current = currentTimestamp;
              }
            }
          }
        }
      } catch (error) {
        console.error('메시지 폴링 오류:', error);
      }
    };
    
    // 즉시 한번 실행
    pollMessages();
    
    // 폴링 설정 (1초마다)
    pollingInterval = setInterval(pollMessages, 1000);
    
    return () => {
      clearInterval(pollingInterval);
    };
  }, [agentId, messages.length]);

  // 메시지 전송
  const handleSendMessage = async () => {
    if (!input.trim() || !agentId || isLoading) return;
    
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
      
      // 에이전트에 요청 전송
      await axios.post(`/api/agent/${agentId}/run`, {
        prompt: input,
        max_steps: 3
      });
      
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      setError('메시지를 전송할 수 없습니다. 다시 시도하세요.');
    } finally {
      setIsLoading(false);
      if (inputRef.current) {
        inputRef.current.focus();
      }
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
  const handleResetChat = async () => {
    if (!agentId) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      // 이전 에이전트 삭제
      await axios.delete(`/api/agent/${agentId}`);
      
      // 메시지 초기화
      setMessages([]);
      
      // 새 에이전트 생성
      await createAgent();
      
      // 상위 컴포넌트 알림
      if (onReset) {
        onReset();
      }
      
    } catch (error) {
      console.error('대화 초기화 오류:', error);
      setError('대화를 초기화할 수 없습니다. 다시 시도하세요.');
    } finally {
      setIsLoading(false);
    }
  };

  // 도구 패널 토글
  const toggleToolsPanel = () => {
    setShowTools(prev => !prev);
  };

  // 도구 선택 처리
  const handleToolSelect = (tool: Tool) => {
    const toolPrompt = `${tool.name} 도구를 사용하여 작업하고 싶습니다. ${tool.examples?.[0] || ''}`;
    setInput(toolPrompt);
    if (inputRef.current) {
      inputRef.current.focus();
    }
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
          
          <Tooltip title="MCP 도구를 사용하여 지능적인 작업을 수행할 수 있습니다.">
            <IconButton size="small">
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Box>
          <Button 
            variant="outlined"
            color="secondary"
            onClick={toggleToolsPanel}
            sx={{ mr: 1 }}
          >
            도구 {showTools ? '숨기기' : '보기'}
          </Button>
          
          <ExportToMemoryButton 
            messages={messages}
            buttonVariant="outlined"
            buttonSize="medium"
            buttonColor="success"
            buttonText="메모리로 저장"
            sx={{ mr: 1 }}
          />
          
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
        <Typography 
          color="error" 
          sx={{ 
            mb: 2, 
            p: 1, 
            bgcolor: '#ffebee', 
            borderRadius: 1,
            fontSize: '0.9rem'
          }}
        >
          {error}
        </Typography>
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
              overflow: 'hidden'
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
                    예시: "프로젝트에서 중요한 파일을 찾아줘", "서버 상태를 확인해줘"
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
                          maxWidth: '85%'
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
                            {msg.role === 'user' ? '사용자' : 'MCP 에이전트'}
                          </Typography>
                        )}
                        
                        {/* 메시지 카드 */}
                        <Card 
                          variant={msg.role === 'user' ? 'outlined' : 'elevation'}
                          sx={{ 
                            bgcolor: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5',
                            boxShadow: msg.role === 'user' ? 'none' : '0 1px 3px rgba(0,0,0,0.1)',
                            borderRadius: 2,
                            overflow: 'hidden'
                          }}
                        >
                          <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                            {/* 메시지 내용 */}
                            <Typography 
                              variant="body1" 
                              component="div" 
                              sx={{ 
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                fontFamily: '"Noto Sans KR", "Roboto", sans-serif',
                                lineHeight: 1.6,
                                fontSize: '0.95rem'
                              }}
                            >
                              {msg.content}
                            </Typography>
                            
                            {/* 도구 호출 정보 */}
                            {msg.toolCall && (
                              <Box mt={1} p={1} bgcolor="rgba(0,0,0,0.04)" borderRadius={1}>
                                <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block' }}>
                                  도구 호출: {msg.toolCall.function?.name}
                                </Typography>
                                <Typography variant="caption" component="div" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                                  {msg.toolCall.function?.arguments || '{}'}
                                </Typography>
                              </Box>
                            )}
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
          disabled={isLoading || !agentId}
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
          disabled={isLoading || !input.trim() || !agentId}
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
    </Box>
  );
};

export default ChatInterface;