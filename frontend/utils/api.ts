import axios from 'axios';
import { Question, Response, CodeSnippet, CodeTemplate, Settings, LLMType, ApiError, ExportFormat, ExportOptions } from '../types';

// API 기본 URL 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,  // 120초 타임아웃
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
  try {
    const response = await api.post('/github/upload', {
      question_id: questionId,
      folder_path: folderPath,
      repo_id: repoId
    });
    return response.data;
  } catch (error) {
    console.error('GitHub 업로드 오류:', error);
    
    // 개발 모드에서 임시 응답 제공
    if (process.env.NODE_ENV === 'development') {
      return {
        success: false,
        message: '백엔드 API가 준비되지 않았습니다.',
        repo_url: `https://github.com/username/repo/tree/main/${folderPath || `question_${questionId}`}`,
        folder_path: folderPath || `question_${questionId}`,
        commit_message: '업로드 실패 - 백엔드 API가 준비되지 않음'
      };
    }
    
    throw error;
  }
};

export const generateCommitMessage = async (
  questionId: number,
  repoId?: number
): Promise<{commit_message: string}> => {
  try {
    const params = repoId ? { repo_id: repoId } : {};
    const response = await api.get(`/github/generate-commit-message/${questionId}`, { params });
    return response.data;
  } catch (error) {
    console.error('커밋 메시지 생성 오류:', error);
    
    // 개발 모드에서 임시 응답 제공
    if (process.env.NODE_ENV === 'development') {
      return {
        commit_message: `Add code for question #${questionId}`
      };
    }
    
    throw error;
  }
};

export const generateReadme = async (
  questionId: number,
  repoId?: number
): Promise<{readme_content: string}> => {
  try {
    const params = repoId ? { repo_id: repoId } : {};
    const response = await api.get(`/github/generate-readme/${questionId}`, { params });
    return response.data;
  } catch (error) {
    console.error('README 생성 오류:', error);
    
    // 개발 모드에서 임시 응답 제공
    if (process.env.NODE_ENV === 'development') {
      return {
        readme_content: `# Question ${questionId}\n\nThis is a placeholder README because the backend API is not available.`
      };
    }
    
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
  const params: any = { skip, limit };
  if (language) params.language = language;
  if (tag) params.tag = tag;
  if (questionId) params.question_id = questionId;
  if (responseId) params.response_id = responseId;
  
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
  try {
    const response = await api.get<Settings>('/settings/');
    return response.data;
  } catch (error) {
    console.error('설정 가져오기 오류:', error);
    
    // localStorage에서 백업 데이터 가져오기
    const backupSettings: Settings = {};
    
    if (localStorage.getItem('github_token')) {
      backupSettings.github_token = localStorage.getItem('github_token') || undefined;
    }
    if (localStorage.getItem('github_username')) {
      backupSettings.github_username = localStorage.getItem('github_username') || undefined;
    }
    if (localStorage.getItem('github_repo')) {
      backupSettings.github_repo = localStorage.getItem('github_repo') || undefined;
    }
    
    // 백업 데이터가 있으면 반환, 없으면 에러 전파
    if (Object.keys(backupSettings).length > 0) {
      return backupSettings;
    }
    
    throw error;
  }
};

export const updateSettings = async (settings: Partial<Settings>): Promise<Settings> => {
  try {
    const response = await api.post<Settings>('/settings/', settings);
    return response.data;
  } catch (error) {
    console.error('설정 업데이트 오류:', error);
    
    // localStorage에 백업 저장
    if (settings.github_token) {
      localStorage.setItem('github_token', settings.github_token);
    }
    if (settings.github_username) {
      localStorage.setItem('github_username', settings.github_username);
    }
    if (settings.github_repo) {
      localStorage.setItem('github_repo', settings.github_repo);
    }
    
    throw error;
  }
};

// 내보내기 관련 API 함수
export const exportQuestion = async (
  questionId: number, 
  format: ExportFormat, 
  options: ExportOptions
): Promise<Blob> => {
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

// 프롬프트 템플릿 관련 API 함수
export const fetchPromptTemplates = async (
  category?: string,
  tag?: string,
  skip = 0,
  limit = 100
): Promise<PromptTemplate[]> => {
  const params: any = { skip, limit };
  if (category) params.category = category;
  if (tag) params.tag = tag;
  
  const response = await api.get<PromptTemplate[]>('/prompt-templates/', { params });
  return response.data;
};

export const fetchPromptTemplate = async (id: number): Promise<PromptTemplate> => {
  const response = await api.get<PromptTemplate>(`/prompt-templates/${id}`);
  return response.data;
};

export const createPromptTemplate = async (template: PromptTemplate): Promise<PromptTemplate> => {
  const response = await api.post<PromptTemplate>('/prompt-templates/', template);
  return response.data;
};

export const updatePromptTemplate = async (id: number, template: Partial<PromptTemplate>): Promise<PromptTemplate> => {
  const response = await api.put<PromptTemplate>(`/prompt-templates/${id}`, template);
  return response.data;
};

export const deletePromptTemplate = async (id: number): Promise<void> => {
  await api.delete(`/prompt-templates/${id}`);
};

// 프롬프트 미리보기 및 실행
export const previewPrompt = async (
  template: string,
  variables: Record<string, string>
): Promise<string> => {
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
  const response = await api.post(`/prompt-engineering/execute`, {
    template_id: templateId,
    variables,
    llm_type: llmType
  });
  return response.data;
};

export default api;