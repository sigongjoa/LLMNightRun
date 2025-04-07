// 로컬 LLM 관련 타입 정의

// 로컬 LLM 상태 응답
export interface LocalLLMStatus {
  enabled: boolean;
  connected: boolean;
  base_url: string;
  model_id?: string;
  error?: string;
}

// 로컬 LLM 설정
export interface LocalLLMConfig {
  enabled: boolean;
  base_url: string;
  name: string;
  model_id: string;
  max_tokens: number;
  temperature: number;
  top_p: number;
  timeout: number;
}

// 로컬 LLM 설정 업데이트 요청
export interface LocalLLMConfigUpdate {
  enabled?: boolean;
  base_url?: string;
  model_id?: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
}

// 로컬 LLM 채팅 메시지
export interface LocalLLMMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  name?: string;
  tool_calls?: any[];
  tool_call_id?: string;
  base64_image?: string;
}

// 로컬 LLM 채팅 요청
export interface LocalLLMChatRequest {
  messages: LocalLLMMessage[];
  system_message?: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
}

// 로컬 LLM 채팅 응답
export interface LocalLLMChatResponse {
  content: string;
  model_id: string;
}