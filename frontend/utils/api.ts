import axios from 'axios';
import { Question, Response, CodeSnippet, CodeTemplate, Settings, LLMType, ApiError, ExportFormat, ExportOptions } from '../types';

// API 기본 URL 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
// 백업 API URL
const BACKUP_API_URL = 'http://localhost:8001';

// 서버 상태 확인 함수
export const checkServerAvailability = async (url: string): Promise<boolean> => {
  try {
    await axios.get(`${url}/health-check`, { timeout: 3000 });
    return true;
  } catch (error) {
    console.warn(`서버 연결 실패: ${url}`, error);
    return false;
  }
};

// 현재 사용 중인 API URL (기본값은 기본 URL)
let currentApiUrl = API_BASE_URL;

// 서버 연결 상태
export const updateApiBaseUrl = async (): Promise<string> => {
  // 먼저 기본 서버 확인
  const isMainServerAvailable = await checkServerAvailability(API_BASE_URL);
  
  if (isMainServerAvailable) {
    currentApiUrl = API_BASE_URL;
    console.log('기본 서버에 연결됨:', API_BASE_URL);
    return currentApiUrl;
  }
  
  // 기본 서버에 연결할 수 없는 경우 백업 서버 확인
  const isBackupServerAvailable = await checkServerAvailability(BACKUP_API_URL);
  
  if (isBackupServerAvailable) {
    currentApiUrl = BACKUP_API_URL;
    console.log('백업 서버로 전환됨:', BACKUP_API_URL);
    return currentApiUrl;
  }
  
  console.error('모든 서버에 연결할 수 없습니다.');
  return currentApiUrl; // 기본값 유지
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
  const newApiUrl = await updateApiBaseUrl();
  if (newApiUrl !== api.defaults.baseURL) {
    api.defaults.baseURL = newApiUrl;
    console.log('API 기본 URL이 업데이트됨:', newApiUrl);
  }
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
    // 네트워크 오류나 서버 연결 실패 시 백업 서버로 전환 시도
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') {
      console.warn('서버 연결 오류 발생. 백업 서버로 전환 시도...');
      await updateApiBaseURLIfNeeded();
      
      // 원래 요청을 새 URL로 다시 시도
      const originalRequest = error.config;
      originalRequest.baseURL = currentApiUrl;
      
      // 재시도 횟수 제한
      if (!originalRequest._retry) {
        originalRequest._retry = true;
        return api(originalRequest);
      }
    }
    
    // 인증 오류 처리 (401 오류)
    if (error.response && error.response.status === 401) {
      // 브라우저 환경에서만 실행
      if (typeof window !== 'undefined') {
        // 로그인 페이지가 아닌 경우에만 리디렉션
        if (!window.location.pathname.includes('/login')) {
          // 토큰 제거
          localStorage.removeItem('token');
          // 로그인 페이지로 리디렉션
          window.location.href = '/login?expired=true';
        }
      }
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

// 서버 상태 확인 주기적 실행 (1분마다)
if (typeof window !== 'undefined') {
  // 백그라운드에서 1분마다 서버 상태 확인
  setInterval(updateApiBaseURLIfNeeded, 60000);
}

// 질문 관련 API 함수
export const fetchQuestions = async (skip = 0, limit = 100): Promise<Question[]> => {
  await updateApiBaseURLIfNeeded(); // 요청 전 서버 상태 확인
  try {
    const response = await api.get<Question[]>('/questions/', { params: { skip, limit } });
    return response.data;
  } catch (error) {
    console.error('질문 목록 가져오기 실패:', error);
    return []; // 오류 발생 시 빈 배열 반환
  }
};

export const fetchQuestion = async (id: number): Promise<Question> => {
  await updateApiBaseURLIfNeeded();
  const response = await api.get<Question>(`/questions/${id}`);
  return response.data;
};

export const createQuestion = async (question: Question): Promise<Question> => {
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
  const apiResponse = await api.post<Response>('/responses/', response);
  return apiResponse.data;
};

// LLM API 요청
export const askLLM = async (llmType: LLMType, question: Question): Promise<{question: Question, response: Response}> => {
  await updateApiBaseURLIfNeeded();
  
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
  const response = await api.post<CodeSnippet>('/code-snippets/', snippet);
  return response.data;
};

export const updateCodeSnippet = async (id: number, snippet: Partial<CodeSnippet>): Promise<CodeSnippet> => {
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
  const response = await api.post<CodeTemplate>('/code-templates/', template);
  return response.data;
};

// 설정 관련 API 함수
export const fetchSettings = async (): Promise<Settings> => {
  await updateApiBaseURLIfNeeded();
  try {
    const response = await api.get<Settings>('/settings');
    return response.data;
  } catch (error) {
    console.error('설정 가져오기 오류:', error);
    throw error;
  }
};

export const updateSettings = async (settings: Partial<Settings>): Promise<Settings> => {
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
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
  availableServers: string[]
}> => {
  const mainAvailable = await checkServerAvailability(API_BASE_URL);
  const backupAvailable = await checkServerAvailability(BACKUP_API_URL);
  
  const availableServers = [];
  if (mainAvailable) availableServers.push(API_BASE_URL);
  if (backupAvailable) availableServers.push(BACKUP_API_URL);
  
  return {
    apiConnected: mainAvailable || backupAvailable,
    apiUrl: currentApiUrl,
    availableServers
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
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
  const response = await api.get<PromptTemplate>(`/prompt-templates/${id}`);
  return response.data;
};

export const createPromptTemplate = async (template: PromptTemplate): Promise<PromptTemplate> => {
  await updateApiBaseURLIfNeeded();
  const response = await api.post<PromptTemplate>('/prompt-templates/', template);
  return response.data;
};

export const updatePromptTemplate = async (id: number, template: Partial<PromptTemplate>): Promise<PromptTemplate> => {
  await updateApiBaseURLIfNeeded();
  const response = await api.put<PromptTemplate>(`/prompt-templates/${id}`, template);
  return response.data;
};

export const deletePromptTemplate = async (id: number): Promise<void> => {
  await updateApiBaseURLIfNeeded();
  await api.delete(`/prompt-templates/${id}`);
};

// 프롬프트 미리보기 및 실행
export const previewPrompt = async (
  template: string,
  variables: Record<string, string>
): Promise<string> => {
  await updateApiBaseURLIfNeeded();
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
  await updateApiBaseURLIfNeeded();
  const response = await api.post(`/prompt-engineering/execute`, {
    template_id: templateId,
    variables,
    llm_type: llmType
  });
  return response.data;
};

export default api;