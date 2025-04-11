import axios from 'axios';
import { Question, Response, CodeSnippet, CodeTemplate, Settings, LLMType, ApiError, ExportFormat, ExportOptions } from '../types';

// API 기본 URL 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 서버 상태 확인 함수
export const checkServerAvailability = async (url: string): Promise<boolean> => {
  try {
    // 루트 경로만 확인 (다른 엔드포인트는 존재하지 않을 수 있음)
    try {
      const rootResponse = await axios.get(`${url}/`, { timeout: 3000 });
      if (rootResponse.status === 200) {
        console.log(`서버 연결 성공 (/):`, url);
        return true;
      }
    } catch (rootError) {
      // 응답은 있지만 에러 코드를 반환하는 경우
      if (rootError.response) {
        console.log(`서버는 응답하고 있습니다. 상태 코드: ${rootError.response.status}`);
        return true; // 서버가 응답하면 연결된 것으로 간주
      }
      
      // 아예 응답이 없는 경우
      console.warn(`서버 연결 실패: ${url} - ${rootError.message}`);
      return false;
    }
    
    return false;
  } catch (error) {
    console.warn(`서버 연결 실패: ${url}`, error);
    return false;
  }
};

// 현재 사용 중인 API URL
let currentApiUrl = API_BASE_URL;

// 서버 연결 상태
export const updateApiBaseUrl = async (): Promise<string> => {
  // 서버 확인
  const isServerAvailable = await checkServerAvailability(API_BASE_URL);
  
  if (isServerAvailable) {
    currentApiUrl = API_BASE_URL;
    console.log('서버에 연결됨:', API_BASE_URL);
  } else {
    console.error('서버에 연결할 수 없습니다:', API_BASE_URL);
  }
  
  return currentApiUrl;
};

// 서버 연결 상태 초기 확인
updateApiBaseUrl().then((url) => {
  console.log('사용 중인 API URL:', url);
});

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: currentApiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 20000,  // 20초 타임아웃 (기존 180초에서 축소)
});

// URL 업데이트 함수
export const updateApiBaseURLIfNeeded = async () => {
  await updateApiBaseUrl();
};

// 요청 인터셉터 (인증 토큰 추가 및 API URL 확인)
api.interceptors.request.use(
  async (config) => {
    // API URL 확인 및 업데이트
    if (config.baseURL !== currentApiUrl) {
      config.baseURL = currentApiUrl;
    }
    
    // 브라우저 환경에서만 로컬 스토리지 접근
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (오류 처리 및 인증 관련 처리)
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // 401 오류 처리 - 로그인 페이지로 이동하지 않음
    if (error.response && error.response.status === 401) {
      console.warn('인증 오류가 발생했지만 무시합니다. 자동 로그인 모드 활성화됨.');
      // 401 오류를 무시하고 계속 진행
    }
    
    // API 오류 처리
    const apiError: ApiError = error.response?.data || { 
      detail: error.code === 'ERR_NETWORK' ? 
        '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.' : 
        '알 수 없는 오류가 발생했습니다.' 
    };
    console.error('API 오류:', apiError);
    return Promise.reject(apiError);
  }
);

// 서버 상태 확인 주기적 실행 (5분마다)
if (typeof window !== 'undefined') {
  // 백그라운드에서 5분마다 서버 상태 확인
  setInterval(updateApiBaseUrl, 300000); // 5분 = 300,000ms
}

// 질문 관련 API 함수
export const fetchQuestions = async (skip = 0, limit = 100): Promise<Question[]> => {
  await updateApiBaseUrl(); // 요청 전 서버 상태 확인
  try {
    const response = await api.get<Question[]>('/questions/', { params: { skip, limit } });
    return response.data;
  } catch (error) {
    console.error('질문 목록 가져오기 실패:', error);
    return []; // 오류 발생 시 빈 배열 반환
  }
};

export const fetchQuestion = async (id: number): Promise<Question> => {
  await updateApiBaseUrl();
  const response = await api.get<Question>(`/questions/${id}`);
  return response.data;
};

export const createQuestion = async (question: Question): Promise<Question> => {
  await updateApiBaseUrl();
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
  await updateApiBaseUrl();
  try {
    const params: any = { skip, limit };
    if (questionId) params.question_id = questionId;
    if (llmType) params.llm_type = llmType;
    
    const response = await api.get<Response[]>('/responses/', { params });
    return response.data;
  } catch (error) {
    console.error('응답 목록 가져오기 실패:', error);
    return []; // 오류 발생 시 빈 배열 반환
  }
};

export const createResponse = async (response: Response): Promise<Response> => {
  await updateApiBaseUrl();
  const apiResponse = await api.post<Response>('/responses/', response);
  return apiResponse.data;
};

// LLM API 요청
export const askLLM = async (llmType: LLMType, question: Question): Promise<{question: Question, response: Response}> => {
  await updateApiBaseUrl();
  
  // 로컬 LLM인 경우 다른 API 엔드포인트 사용
  if (llmType === LLMType.LOCAL_LLM) {
    try {
      console.log('로컬 LLM API 호출 시작');
      const localResponse = await api.post('/api/local-llm/chat', {
        messages: [{ role: 'user', content: question.content }]
      });
      console.log('로컬 LLM API 응답:', localResponse.data);
      
      // 질문 ID가 없는 경우 질문 먼저 생성
      let questionObj = question;
      if (!question.id) {
        const createdQuestion = await createQuestion(question);
        questionObj = createdQuestion;
      }
      
      // 응답 저장 - 필요한 필드만 포함
      const responseData: Partial<Response> = {
        question_id: questionObj.id || 0,
        llm_type: LLMType.LOCAL_LLM,
        content: localResponse.data.content
      };
      
      const savedResponse = await createResponse(responseData);
      console.log('저장된 응답:', savedResponse);
      
      // 응답 형식 변환
      return {
        question: questionObj,
        response: savedResponse
      };
    } catch (error) {
      console.error('로컬 LLM 호출 오류:', error);
      throw error;
    }
  }
  
  // 기존 다른 LLM 유형들은 원래 API 사용
  try {
    console.log(`/ask/${llmType} 호출 시작`);
    const response = await api.post(`/ask/${llmType}`, question);
    console.log(`/ask/${llmType} 응답 받음:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`/ask/${llmType} 호출 오류:`, error);
    throw error;
  }
};

// GitHub 관련 API 함수
export const uploadToGitHub = async (
  questionId: number,
  folderPath?: string,
  repoId?: number
): Promise<{success: boolean, message: string, repo_url: string, folder_path: string, commit_message: string, files?: string[]}> => {
  await updateApiBaseUrl();
  try {
    const response = await api.post('/github/upload', {
      question_id: questionId,
      folder_path: folderPath,
      repo_id: repoId
    });
    return response.data;
  } catch (error) {
    console.error('GitHub 업로드 오류:', error);
    throw error;
  }
};

export const generateCommitMessage = async (
  questionId: number,
  repoId?: number
): Promise<{commit_message: string}> => {
  await updateApiBaseUrl();
  try {
    const params = repoId ? { repo_id: repoId } : {};
    const response = await api.get(`/github/generate-commit-message/${questionId}`, { params });
    // API 응답에 message 또는 commit_message 모두 지원
    if (response.data.commit_message) {
      return response.data;
    } else if (response.data.message) {
      return { commit_message: response.data.message };
    }
    return response.data;
  } catch (error) {
    console.error('커밋 메시지 생성 오류:', error);
    throw error;
  }
};

export const generateReadme = async (
  questionId: number,
  repoId?: number
): Promise<{readme_content: string}> => {
  await updateApiBaseUrl();
  try {
    const params = repoId ? { repo_id: repoId } : {};
    const response = await api.get(`/github/generate-readme/${questionId}`, { params });
    // API 응답에 content 또는 readme_content 모두 지원
    if (response.data.readme_content) {
      return response.data;
    } else if (response.data.content) {
      return { readme_content: response.data.content };
    }
    return response.data;
  } catch (error) {
    console.error('README 생성 오류:', error);
    throw error;
  }
};

// 코드 스니펫 관련 API 함수
export const fetchCodeSnippets = async (
  language?: string,
  tag?: string,
  skip = 0,
  limit = 100,
  questionId?: number,
  responseId?: number
): Promise<CodeSnippet[]> => {
  await updateApiBaseUrl();
  try {
    const params: any = { skip, limit };
    if (language) params.language = language;
    if (tag) params.tag = tag;
    if (questionId) params.question_id = questionId;
    if (responseId) params.response_id = responseId;
    
    const response = await api.get<CodeSnippet[]>('/code-snippets/', { params });
    return response.data;
  } catch (error) {
    console.error('코드 스니펫 목록 가져오기 실패:', error);
    return [];
  }
};

export const createCodeSnippet = async (snippet: CodeSnippet): Promise<CodeSnippet> => {
  await updateApiBaseUrl();
  const response = await api.post<CodeSnippet>('/code-snippets/', snippet);
  return response.data;
};

export const updateCodeSnippet = async (id: number, snippet: Partial<CodeSnippet>): Promise<CodeSnippet> => {
  await updateApiBaseUrl();
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
  await updateApiBaseUrl();
  try {
    const params: any = { skip, limit };
    if (language) params.language = language;
    if (tag) params.tag = tag;
    
    const response = await api.get<CodeTemplate[]>('/code-templates/', { params });
    return response.data;
  } catch (error) {
    console.error('코드 템플릿 목록 가져오기 실패:', error);
    return [];
  }
};

export const createCodeTemplate = async (template: CodeTemplate): Promise<CodeTemplate> => {
  await updateApiBaseUrl();
  const response = await api.post<CodeTemplate>('/code-templates/', template);
  return response.data;
};

// 설정 관련 API 함수
export const fetchSettings = async (): Promise<Settings> => {
  await updateApiBaseUrl();
  try {
    const response = await api.get<Settings>('/settings');
    return response.data;
  } catch (error) {
    console.error('설정 가져오기 오류:', error);
    throw error;
  }
};

export const updateSettings = async (settings: Partial<Settings>): Promise<Settings> => {
  await updateApiBaseUrl();
  try {
    const response = await api.post<Settings>('/settings', settings);
    return response.data;
  } catch (error) {
    console.error('설정 업데이트 오류:', error);
    throw error;
  }
};

// 내보내기 관련 API 함수
export const exportQuestion = async (
  questionId: number, 
  format: ExportFormat, 
  options: ExportOptions
): Promise<Blob> => {
  await updateApiBaseUrl();
  const params = {
    format,
    include_metadata: options.includeMetadata,
    include_tags: options.includeTags,
    include_timestamps: options.includeTimestamps,
    include_llm_info: options.includeLlmInfo,
    code_highlighting: options.codeHighlighting
  };
  
  const response = await api.get(`/export/question/${questionId}`, {
    params,
    responseType: 'blob'
  });
  
  return response.data;
};

export const exportCodeSnippet = async (
  snippetId: number, 
  format: ExportFormat, 
  options: ExportOptions
): Promise<Blob> => {
  await updateApiBaseUrl();
  const params = {
    format,
    include_metadata: options.includeMetadata,
    include_tags: options.includeTags,
    include_timestamps: options.includeTimestamps,
    include_llm_info: options.includeLlmInfo
  };
  
  const response = await api.get(`/export/code-snippet/${snippetId}`, {
    params,
    responseType: 'blob'
  });
  
  return response.data;
};

export const exportAgentLogs = async (
  sessionId: string, 
  format: ExportFormat, 
  options: ExportOptions
): Promise<Blob> => {
  await updateApiBaseUrl();
  const params = {
    format,
    include_timestamps: options.includeTimestamps
  };
  
  const response = await api.get(`/export/agent-logs/${sessionId}`, {
    params,
    responseType: 'blob'
  });
  
  return response.data;
};

export const exportBatch = async (
  items: Array<{type: 'question' | 'code_snippet' | 'agent_logs', id: number | string}>,
  format: ExportFormat, 
  options: ExportOptions
): Promise<Blob> => {
  await updateApiBaseUrl();
  const params = {
    format,
    include_metadata: options.includeMetadata,
    include_tags: options.includeTags,
    include_timestamps: options.includeTimestamps,
    include_llm_info: options.includeLlmInfo
  };
  
  const response = await api.post('/export/batch', items, {
    params,
    responseType: 'blob'
  });
  
  return response.data;
};

// 서버 상태 확인 함수
export const getApiStatus = async (): Promise<{
  apiConnected: boolean,
  apiUrl: string,
  availableServers: string[],
  openaiConnected: boolean,
  claudeConnected: boolean,
  githubConnected: boolean,
  mcpServersCount: number
}> => {
  const mainAvailable = await checkServerAvailability(API_BASE_URL);
  
  // 서버 연결 가능 여부만 확인 - 추가 정보는 사용하지 않음
  return {
    apiConnected: mainAvailable,
    apiUrl: currentApiUrl,
    availableServers: mainAvailable ? ['local'] : [],
    openaiConnected: mainAvailable, // 서버가 연결되어 있으면 서비스도 연결된 것으로 간주
    claudeConnected: mainAvailable,
    githubConnected: mainAvailable,
    mcpServersCount: mainAvailable ? 2 : 0
  };
};

// 타입 정의 - 기본적인 프롬프트 템플릿 타입
interface PromptTemplate {
  id?: number;
  title: string;
  template: string;
  category?: string;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
  user_id?: number;
}

// 프롬프트 템플릿 관련 API 함수
export const fetchPromptTemplates = async (
  category?: string,
  tag?: string,
  skip = 0,
  limit = 100
): Promise<PromptTemplate[]> => {
  await updateApiBaseUrl();
  try {
    const params: any = { skip, limit };
    if (category) params.category = category;
    if (tag) params.tag = tag;
    
    const response = await api.get<PromptTemplate[]>('/prompt-templates/', { params });
    return response.data;
  } catch (error) {
    console.error('프롬프트 템플릿 목록 가져오기 실패:', error);
    return [];
  }
};

export const fetchPromptTemplate = async (id: number): Promise<PromptTemplate> => {
  await updateApiBaseUrl();
  const response = await api.get<PromptTemplate>(`/prompt-templates/${id}`);
  return response.data;
};

export const createPromptTemplate = async (template: PromptTemplate): Promise<PromptTemplate> => {
  await updateApiBaseUrl();
  const response = await api.post<PromptTemplate>('/prompt-templates/', template);
  return response.data;
};

export const updatePromptTemplate = async (id: number, template: Partial<PromptTemplate>): Promise<PromptTemplate> => {
  await updateApiBaseUrl();
  const response = await api.put<PromptTemplate>(`/prompt-templates/${id}`, template);
  return response.data;
};

export const deletePromptTemplate = async (id: number): Promise<void> => {
  await updateApiBaseUrl();
  await api.delete(`/prompt-templates/${id}`);
};

// 프롬프트 미리보기 및 실행
export const previewPrompt = async (
  template: string,
  variables: Record<string, string>
): Promise<string> => {
  await updateApiBaseUrl();
  const response = await api.post<{result: string}>('/prompt-engineering/preview', {
    template,
    variables
  });
  return response.data.result;
};

export const executePrompt = async (
  templateId: number,
  variables: Record<string, string>,
  llmType: LLMType
): Promise<{question: Question, response: Response}> => {
  await updateApiBaseUrl();
  const response = await api.post(`/prompt-engineering/execute`, {
    template_id: templateId,
    variables,
    llm_type: llmType
  });
  return response.data;
};

export default api;