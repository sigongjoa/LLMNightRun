import axios from 'axios';
import { Question, Response, CodeSnippet, CodeTemplate, Settings, LLMType, ApiError } from '../types';

// API 기본 URL 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (예: 인증 토큰 추가)
api.interceptors.request.use(
  (config) => {
    // 필요시 여기에 인증 토큰 추가
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (오류 처리 등)
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // API 오류 처리
    const apiError: ApiError = error.response?.data || { detail: '알 수 없는 오류가 발생했습니다.' };
    console.error('API 오류:', apiError);
    return Promise.reject(apiError);
  }
);

// 질문 관련 API 함수
export const fetchQuestions = async (skip = 0, limit = 100): Promise<Question[]> => {
  const response = await api.get<Question[]>('/questions/', { params: { skip, limit } });
  return response.data;
};

export const fetchQuestion = async (id: number): Promise<Question> => {
  const response = await api.get<Question>(`/questions/${id}`);
  return response.data;
};

export const createQuestion = async (question: Question): Promise<Question> => {
  const response = await api.post<Question>('/questions/', question);
  return response.data;
};

// 응답 관련 API 함수
export const fetchResponses = async (
  questionId?: number,
  llmType?: LLMType,
  skip = 0,
  limit = 100
): Promise<Response[]> => {
  const params: any = { skip, limit };
  if (questionId) params.question_id = questionId;
  if (llmType) params.llm_type = llmType;
  
  const response = await api.get<Response[]>('/responses/', { params });
  return response.data;
};

export const createResponse = async (response: Response): Promise<Response> => {
  const apiResponse = await api.post<Response>('/responses/', response);
  return apiResponse.data;
};

// LLM API 요청
export const askLLM = async (llmType: LLMType, question: Question): Promise<{question: Question, response: Response}> => {
  const response = await api.post(`/ask/${llmType}`, question);
  return response.data;
};

// GitHub 업로드
export const uploadToGitHub = async (questionId: number): Promise<{message: string, url: string}> => {
  const response = await api.post('/github/upload', { question_id: questionId });
  return response.data;
};

// 코드 스니펫 관련 API 함수
export const fetchCodeSnippets = async (
  language?: string,
  tag?: string,
  skip = 0,
  limit = 100
): Promise<CodeSnippet[]> => {
  const params: any = { skip, limit };
  if (language) params.language = language;
  if (tag) params.tag = tag;
  
  const response = await api.get<CodeSnippet[]>('/code-snippets/', { params });
  return response.data;
};

export const createCodeSnippet = async (snippet: CodeSnippet): Promise<CodeSnippet> => {
  const response = await api.post<CodeSnippet>('/code-snippets/', snippet);
  return response.data;
};

export const updateCodeSnippet = async (id: number, snippet: Partial<CodeSnippet>): Promise<CodeSnippet> => {
  const response = await api.put<CodeSnippet>(`/code-snippets/${id}`, snippet);
  return response.data;
};

// 코드 템플릿 관련 API 함수
export const fetchCodeTemplates = async (
  language?: string,
  tag?: string,
  skip = 0,
  limit = 100
): Promise<CodeTemplate[]> => {
  const params: any = { skip, limit };
  if (language) params.language = language;
  if (tag) params.tag = tag;
  
  const response = await api.get<CodeTemplate[]>('/code-templates/', { params });
  return response.data;
};

export const createCodeTemplate = async (template: CodeTemplate): Promise<CodeTemplate> => {
  const response = await api.post<CodeTemplate>('/code-templates/', template);
  return response.data;
};

// 설정 관련 API 함수
export const fetchSettings = async (): Promise<Settings> => {
  const response = await api.get<Settings>('/settings/');
  return response.data;
};

export const updateSettings = async (settings: Partial<Settings>): Promise<Settings> => {
  const response = await api.post<Settings>('/settings/', settings);
  return response.data;
};

export default api;