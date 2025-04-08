import axiosInstance from '../axiosInstance';

/**
 * 로컬 LLM 관련 API 함수
 */
export const LocalLlmApi = {
  /**
   * 로컬 LLM 채팅
   */
  chatWithLocalLLM: async (
    messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>
  ): Promise<{
    content: string;
    model: string;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
  }> => {
    const response = await axiosInstance.post<{
      content: string;
      model: string;
      usage: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
      };
    }>('/api/local-llm/chat', { messages });
    return response.data;
  },

  /**
   * 로컬 LLM 상태 조회
   */
  getLocalLLMStatus: async (): Promise<{
    status: 'running' | 'loading' | 'stopped';
    model: string;
    memory_usage: number;
    startup_time?: number;
    max_tokens: number;
    temperature?: number;
  }> => {
    const response = await axiosInstance.get<{
      status: 'running' | 'loading' | 'stopped';
      model: string;
      memory_usage: number;
      startup_time?: number;
      max_tokens: number;
      temperature?: number;
    }>('/api/local-llm/status');
    return response.data;
  },

  /**
   * 로컬 LLM 설정 조회
   */
  getLocalLLMSettings: async (): Promise<{
    model_path: string;
    model_name: string;
    quantization: string;
    context_size: number;
    temperature: number;
    top_p: number;
    max_tokens: number;
    autoload: boolean;
  }> => {
    const response = await axiosInstance.get<{
      model_path: string;
      model_name: string;
      quantization: string;
      context_size: number;
      temperature: number;
      top_p: number;
      max_tokens: number;
      autoload: boolean;
    }>('/api/local-llm/settings');
    return response.data;
  },

  /**
   * 로컬 LLM 설정 업데이트
   */
  updateLocalLLMSettings: async (
    settings: Partial<{
      model_path: string;
      model_name: string;
      quantization: string;
      context_size: number;
      temperature: number;
      top_p: number;
      max_tokens: number;
      autoload: boolean;
    }>
  ): Promise<{
    success: boolean;
    message: string;
    requires_restart: boolean;
  }> => {
    const response = await axiosInstance.post<{
      success: boolean;
      message: string;
      requires_restart: boolean;
    }>('/api/local-llm/settings', settings);
    return response.data;
  },

  /**
   * 로컬 LLM 시작
   */
  startLocalLLM: async (): Promise<{
    success: boolean;
    message: string;
    estimated_time: number;
  }> => {
    const response = await axiosInstance.post<{
      success: boolean;
      message: string;
      estimated_time: number;
    }>('/api/local-llm/start');
    return response.data;
  },

  /**
   * 로컬 LLM 중지
   */
  stopLocalLLM: async (): Promise<{
    success: boolean;
    message: string;
  }> => {
    const response = await axiosInstance.post<{
      success: boolean;
      message: string;
    }>('/api/local-llm/stop');
    return response.data;
  }
};

export default LocalLlmApi;
