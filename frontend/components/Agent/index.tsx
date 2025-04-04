import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  CircularProgress,
  Divider,
  IconButton,
  Alert,
  Card,
  CardContent,
  Chip,
  Tooltip
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import StopIcon from '@mui/icons-material/Stop';
import CodeIcon from '@mui/icons-material/Code';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import api from '../../utils/api';

// 메시지 유형 정의
interface Message {
  role: string;
  content: string;
  base64_image?: string;
  tool_calls?: any[];
  tool_call_id?: string;
  name?: string;
}

// 에이전트 상태 유형
type AgentState = 'idle' | 'running' | 'finished' | 'error';

// 에이전트 응답 유형
interface AgentResponse {
  agent_id: string;
  state: AgentState;
  messages: Message[];
  result: string;
}

const AgentConsole: React.FC = () => {
  // 상태 관리
  const [agentId, setAgentId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentState, setAgentState] = useState<AgentState>('idle');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // 화면 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // 에이전트 생성
  const createAgent = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await api.post<AgentResponse>('/agent/create');
      setAgentId(response.data.agent_id);
      setAgentState(response.data.state);
      
      // 초기 시스템 메시지 추가
      setMessages([
        {
          role: 'system',
          content: 'Manus 에이전트가 생성되었습니다. 어떤 작업을 도와드릴까요?'
        }
      ]);
    } catch (err: any) {
      setError(err.response?.data?.detail || '에이전트 생성 중 오류가 발생했습니다.');
      console.error('에이전트 생성 오류:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 컴포넌트 마운트 시 에이전트 생성
  useEffect(() => {
    createAgent();
    
    // 컴포넌트 언마운트 시 에이전트 정리
    return () => {
      if (agentId) {
        api.delete(`/agent/${agentId}`).catch(err => {
          console.error('에이전트 정리 오류:', err);
        });
      }
    };
  }, []);
  
  // 메시지 전송
  const sendMessage = async () => {
    if (!input.trim() || !agentId || isLoading) return;
    
    // 사용자 메시지 추가
    const userMessage: Message = {
      role: 'user',
      content: input.trim()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);
    
    try {
      // 에이전트 실행
      const response = await api.post<AgentResponse>(`/agent/${agentId}/run`, {
        prompt: userMessage.content
      });
      
      // 응답 처리
      setAgentState(response.data.state);
      setMessages(response.data.messages);
    } catch (err: any) {
      setError(err.response?.data?.detail || '에이전트 실행 중 오류가 발생했습니다.');
      console.error('에이전트 실행 오류:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 에이전트 재설정
  const resetAgent = async () => {
    if (!agentId || isLoading) return;
    
    try {
      // 기존 에이전트 삭제
      await api.delete(`/agent/${agentId}`);
      
      // 상태 초기화
      setAgentId(null);
      setMessages([]);
      setAgentState('idle');
      
      // 새 에이전트 생성
      await createAgent();
    } catch (err: any) {
      setError(err.response?.data?.detail || '에이전트 재설정 중 오류가 발생했습니다.');
      console.error('에이전트 재설정 오류:', err);
    }
  };
  
  // 메시지 렌더링
  const renderMessage = (message: Message, index: number) => {
    // 역할에 따른 스타일 설정
    const getRoleStyle = (role: string) => {
      switch (role) {
        case 'user':
          return {
            bgcolor: '#e3f2fd',
            alignSelf: 'flex-end',
            borderRadius: '16px 16px 0 16px'
          };
        case 'assistant':
          return {
            bgcolor: '#f1f8e9',
            alignSelf: 'flex-start',
            borderRadius: '16px 16px 16px 0'
          };
        case 'system':
          return {
            bgcolor: '#f5f5f5',
            alignSelf: 'center',
            borderRadius: '16px'
          };
        case 'tool':
          return {
            bgcolor: '#fff3e0',
            alignSelf: 'flex-start',
            borderRadius: '16px 16px 16px 0'
          };
        default:
          return {
            bgcolor: '#f5f5f5',
            alignSelf: 'flex-start',
            borderRadius: '16px'
          };
      }
    };
    
    return (
      <Box
        key={index}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          width: '100%',
          mb: 2
        }}
      >
        <Card
          sx={{
            maxWidth: message.role === 'user' ? '80%' : '90%',
            ...getRoleStyle(message.role)
          }}
        >
          <CardContent>
            {message.role !== 'user' && (
              <Typography 
                variant="caption" 
                color="text.secondary" 
                sx={{ display: 'block', mb: 0.5 }}
              >
                {message.role === 'assistant' ? 'Manus' : 
                 message.role === 'system' ? 'System' :
                 message.role === 'tool' ? `Tool: ${message.name || 'Unknown'}` : message.role}
              </Typography>
            )}
            
            <Typography variant="body1" component="div" sx={{ whiteSpace: 'pre-wrap' }}>
              {message.content}
            </Typography>
            
            {/* 이미지가 있는 경우 */}
            {message.base64_image && (
              <Box sx={{ mt: 1 }}>
                <img 
                  src={`data:image/png;base64,${message.base64_image}`}
                  alt="Generated image"
                  style={{ maxWidth: '100%', borderRadius: 4 }}
                />
              </Box>
            )}
            
            {/* 도구 호출이 있는 경우 */}
            {message.tool_calls && message.tool_calls.length > 0 && (
              <Box sx={{ mt: 1 }}>
                {message.tool_calls.map((tool, toolIndex) => (
                  <Box key={toolIndex} sx={{ mt: 1 }}>
                    <Chip 
                      label={`🔧 ${tool.function.name}`}
                      size="small"
                      variant="outlined"
                      color="primary"
                      icon={<CodeIcon />}
                      sx={{ mb: 0.5 }}
                    />
                    <Paper 
                      variant="outlined" 
                      sx={{ p: 1, bgcolor: '#f5f5f5', borderRadius: 1 }}
                    >
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          whiteSpace: 'pre-wrap', 
                          fontFamily: 'monospace',
                          fontSize: '0.85rem'
                        }}
                      >
                        {tool.function.arguments}
                      </Typography>
                    </Paper>
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };
  
  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Manus 에이전트</Typography>
        <Box>
          <Chip
            label={agentState}
            color={
              agentState === 'running' ? 'info' :
              agentState === 'finished' ? 'success' :
              agentState === 'error' ? 'error' : 'default'
            }
            size="small"
            sx={{ mr: 1 }}
          />
          <Tooltip title="에이전트 재설정">
            <IconButton 
              size="small" 
              onClick={resetAgent}
              disabled={isLoading}
            >
              <RestartAltIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {/* 메시지 목록 */}
      <Box
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          mb: 2,
          p: 1,
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {messages.map(renderMessage)}
        <div ref={messagesEndRef} />
      </Box>
      
      {/* 입력 영역 */}
      <Box
        component="form"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="메시지를 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading || !agentId || agentState === 'error'}
          multiline
          rows={2}
          sx={{ flexGrow: 1 }}
        />
        <Button
          variant="contained"
          color="primary"
          endIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          onClick={sendMessage}
          disabled={isLoading || !input.trim() || !agentId || agentState === 'error'}
          sx={{ height: 56 }}
        >
          전송
        </Button>
      </Box>
    </Paper>
  );
};