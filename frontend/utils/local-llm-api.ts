import api from './api';
import { 
  LocalLLMStatus, 
  LocalLLMConfig, 
  LocalLLMConfigUpdate,
  LocalLLMChatRequest,
  LocalLLMChatResponse
} from '../types/local-llm';

const LOCAL_LLM_API_BASE = '/api/local-llm';

/**
 * 프론트와 백엔드의 통신 테스트
 * @returns 통신 테스트 결과
 */
export const pingLocalLLM = async (): Promise<{status: string, message: string}> => {
  const response = await api.get<{status: string, message: string}>(`${LOCAL_LLM_API_BASE}/ping`);
  return response.data;
};

/**
 * 로컬 LLM 상태 조회
 * @returns 로컬 LLM 상태 정보
 */
export const getLocalLLMStatus = async (): Promise<LocalLLMStatus> => {
  const response = await api.get<LocalLLMStatus>(`${LOCAL_LLM_API_BASE}/status`);
  return response.data;
};

/**
 * 로컬 LLM 설정 업데이트
 * @param config 업데이트할 설정 정보
 * @returns 업데이트된 전체 설정
 */
export const updateLocalLLMConfig = async (config: LocalLLMConfigUpdate): Promise<LocalLLMConfig> => {
  const response = await api.put<LocalLLMConfig>(`${LOCAL_LLM_API_BASE}/config`, config);
  return response.data;
};

/**
 * 로컬 LLM 채팅
 * @param request 채팅 요청 데이터
 * @returns LLM 응답
 */
export const chatWithLocalLLM = async (request: LocalLLMChatRequest): Promise<LocalLLMChatResponse> => {
  const response = await api.post<LocalLLMChatResponse>(`${LOCAL_LLM_API_BASE}/chat`, request);
  return response.data;
};

/**
 * 로컬 LLM을 통해 질문에 대한 답변 요청
 * @param question 질문 내용
 * @param systemMessage 시스템 메시지 (선택 사항)
 * @returns LLM 응답
 */
export const askLocalLLM = async (
  question: string, 
  systemMessage?: string
): Promise<LocalLLMChatResponse> => {
  console.log('askLocalLLM 호출:', question);
  const request: LocalLLMChatRequest = {
    messages: [
      {
        role: 'user',
        content: question
      }
    ]
  };
  
  if (systemMessage) {
    request.system_message = systemMessage;
  }
  
  const result = await chatWithLocalLLM(request);
  console.log('askLocalLLM 응답:', result);
  return result;
};