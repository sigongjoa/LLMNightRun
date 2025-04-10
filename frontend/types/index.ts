// LLM 유형 정의
export enum LLMType {
  OPENAI_API = "openai_api",
  OPENAI_WEB = "openai_web",
  CLAUDE_API = "claude_api",
  CLAUDE_WEB = "claude_web",
  LOCAL_LLM = "local_llm",
  MANUAL = "manual",
}

// 코드 언어 정의
export enum CodeLanguage {
  PYTHON = "python",
  JAVASCRIPT = "javascript",
  TYPESCRIPT = "typescript",
  JAVA = "java",
  CSHARP = "csharp",
  CPP = "cpp",
  GO = "go",
  RUST = "rust",
  PHP = "php",
  RUBY = "ruby",
  SWIFT = "swift",
  KOTLIN = "kotlin",
  OTHER = "other",
}

// 질문 모델
export interface Question {
  id?: number;
  content: string;
  tags: string[];
  created_at?: string;
}

// 응답 모델
export interface Response {
  id?: number;
  question_id: number;
  llm_type: LLMType;
  content: string;
  created_at?: string;
}

// 코드 스니펫 모델
export interface CodeSnippet {
  id?: number;
  title: string;
  description?: string;
  content: string;
  language: CodeLanguage;
  tags: string[];
  source_llm?: LLMType;
  question_id?: number;
  response_id?: number;
  version: number;
  created_at?: string;
  updated_at?: string;
}

// 코드 템플릿 모델
export interface CodeTemplate {
  id?: number;
  name: string;
  description?: string;
  content: string;
  language: CodeLanguage;
  tags: string[];
  created_at?: string;
  updated_at?: string;
}

// 설정 모델
export interface Settings {
  id?: number;
  openai_api_key?: string;
  claude_api_key?: string;
  github_token?: string;
  github_repo?: string;
  github_username?: string;
  updated_at?: string;
}

// GitHub 관련 타입
export { 
  GitHubRepository,
  GitHubRepositoryCreate,
  GitHubRepositoryUpdate,
  GitHubUploadResult,
  GitHubCommitMessage,
  GitHubReadmeContent,
  GitHubRepositoriesResponse
} from './github';

// API 응답 타입
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// 에러 응답 타입
export interface ApiError {
  detail: string;
}

// 작업 예약 유형
export enum ScheduleType {
  INTERVAL = "interval",
  DAILY = "daily",
  WEEKLY = "weekly",
}

// 작업 정보
export interface TaskInfo {
  id: string;
  name: string;
  description: string;
  schedule_type: ScheduleType;
  schedule_value: string | number;
  active: boolean;
  created_at?: string;
  last_run?: string;
  last_result?: string;
}

// 내보내기 형식
export enum ExportFormat {
  MARKDOWN = "markdown",
  JSON = "json",
  HTML = "html",
  PDF = "pdf",
  CODE_PACKAGE = "code_package"
}

// 내보내기 옵션
export interface ExportOptions {
  includeMetadata: boolean;
  includeTags: boolean;
  includeTimestamps: boolean;
  includeLlmInfo: boolean;
  codeHighlighting?: boolean;
}

// 프롬프트 템플릿 모델
export interface PromptTemplate {
  id?: number;
  name: string;
  description?: string;
  content: string;
  template_variables: string[];
  category: string;
  tags: string[];
  created_at?: string;
  updated_at?: string;
}

// 프롬프트 변수 타입
export interface PromptVariable {
  name: string;
  value: string;
  description?: string;
}