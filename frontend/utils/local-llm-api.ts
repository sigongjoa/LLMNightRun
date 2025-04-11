import axios from 'axios';
import api from './api';
import { 
  LocalLLMStatus, 
  LocalLLMConfig, 
  LocalLLMConfigUpdate,
  LocalLLMChatRequest,
  LocalLLMChatResponse
} from '../types/local-llm';

// API 기본 경로 (원래 경로로 복원)
const LOCAL_LLM_API_BASE = '/api/local-llm';

// 디버그 메시지
console.log('로컬 LLM API 초기화 - 경로:', LOCAL_LLM_API_BASE);

/**
 * 프론트와 백엔드의 통신 테스트
 * @returns 통신 테스트 결과
 */
export const pingLocalLLM = async (): Promise<{status: string, message: string}> => {
  try {
    console.log('로컬 LLM 핑 요청 중...');
    const response = await api.get<{status: string, message: string}>(`${LOCAL_LLM_API_BASE}/ping`);
    console.log('핑 응답:', response.data);
    return response.data;
  } catch (error) {
    console.error('LLM 핑 오류:', error);
    return {
      status: "error",
      message: "LLM 서버에 연결할 수 없습니다"
    };
  }
};

/**
 * 로컬 LLM 상태 조회
 * @returns 로컬 LLM 상태 정보
 */
export const getLocalLLMStatus = async (): Promise<LocalLLMStatus> => {
  try {
    console.log('로컬 LLM 상태 요청 중...');
    const response = await api.get<LocalLLMStatus>(`${LOCAL_LLM_API_BASE}/status`);
    console.log('로컬 LLM 상태 응답:', response.data);
    return response.data;
  } catch (error) {
    console.error('LLM 상태 확인 중 오류:', error);
    // 기본 오류 응답
    return {
      enabled: true,
      connected: false,
      base_url: "http://127.0.0.1:1234",
      error: "LM Studio에 연결할 수 없습니다. LM Studio가 실행 중인지 확인해주세요."
    };
  }
};

/**
 * 로컬 LLM 설정 업데이트
 * @param config 업데이트할 설정 정보
 * @returns 업데이트된 전체 설정
 */
export const updateLocalLLMConfig = async (config: LocalLLMConfigUpdate): Promise<LocalLLMConfig> => {
  try {
    const response = await api.put<LocalLLMConfig>(`${LOCAL_LLM_API_BASE}/config`, config);
    return response.data;
  } catch (error) {
    console.error('설정 업데이트 오류:', error);
    // 임시 응답
    return {
      enabled: config.enabled ?? true,
      base_url: config.base_url ?? "http://127.0.0.1:1234",
      name: "LM Studio",
      model_id: config.model_id ?? "deepseek-r1-distill-qwen-7b",
      max_tokens: config.max_tokens ?? 1000,
      temperature: config.temperature ?? 0.7,
      top_p: config.top_p ?? 1.0,
      timeout: 30
    };
  }
};

/**
 * 로컬 LLM 채팅
 * @param request 채팅 요청 데이터
 * @returns LLM 응답
 */
export const chatWithLocalLLM = async (request: LocalLLMChatRequest): Promise<LocalLLMChatResponse> => {
  try {
    console.log('LLM 채팅 요청 전송:', request);
    const response = await api.post<LocalLLMChatResponse>(`${LOCAL_LLM_API_BASE}/chat`, request);
    console.log('LLM 채팅 응답:', response.data);
    return response.data;
  } catch (error) {
    console.error('채팅 요청 중 오류:', error);
    return {
      content: "LM Studio에 연결할 수 없거나 응답 처리 중 오류가 발생했습니다.",
      model_id: "deepseek-r1-distill-qwen-7b"
    };
  }
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
  
  try {
    const result = await chatWithLocalLLM(request);
    console.log('askLocalLLM 응답:', result);
    return result;
  } catch (error) {
    console.error('askLocalLLM 오류:', error);
    return {
      content: "오류가 발생했습니다. LM Studio가 실행 중인지 확인하고 다시 시도해주세요.",
      model_id: "deepseek-r1-distill-qwen-7b"
    };
  }
};