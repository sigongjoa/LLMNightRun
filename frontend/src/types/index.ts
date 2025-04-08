// 기본 타입 정의
export enum LLMType {
  OPENAI_API = 'openai_api',
  CLAUDE_API = 'claude_api',
  LOCAL_LLM = 'local_llm',
  CUSTOM_LLM = 'custom_llm'
}

export interface ApiError {
  detail: string;
  code?: string;
  params?: Record<string, any>;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

// 질문 관련 타입
export interface Question {
  id?: number;
  content: string;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

// 응답 관련 타입
export interface Response {
  id?: number;
  question_id: number;
  llm_type: LLMType;
  content: string;
  created_at?: string;
  updated_at?: string;
  metadata?: ResponseMetadata;
}

export interface ResponseMetadata {
  model?: string;
  tokens?: {
    prompt?: number;
    completion?: number;
    total?: number;
  };
  duration_ms?: number;
  temperature?: number;
}

// 코드 스니펫 관련 타입
export interface CodeSnippet {
  id?: number;
  title: string;
  description?: string;
  content: string;
  language: string;
  tags?: string[];
  source_llm?: LLMType;
  question_id?: number;
  response_id?: number;
  parent_id?: number;
  version?: number;
  created_at?: string;
  updated_at?: string;
}

// 코드 템플릿 관련 타입
export interface CodeTemplate {
  id?: number;
  name: string;
  description?: string;
  content: string;
  language: string;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

// 프롬프트 템플릿 관련 타입
export interface PromptTemplate {
  id?: number;
  title: string;
  content: string;
  category?: string;
  tags?: string[];
  variables?: string[];
  description?: string;
  created_at?: string;
  updated_at?: string;
}

// 설정 관련 타입
export interface Settings {
  openai_api_key?: string;
  claude_api_key?: string;
  github_token?: string;
  github_repo?: string;
  github_username?: string;
  updated_at?: string;
}

// 내보내기 관련 타입
export enum ExportFormat {
  MARKDOWN = 'markdown',
  JSON = 'json',
  HTML = 'html',
  PDF = 'pdf',
  CODE_PACKAGE = 'code_package'
}

export interface ExportOptions {
  includeMetadata?: boolean;
  includeTags?: boolean;
  includeTimestamps?: boolean;
  includeLlmInfo?: boolean;
  codeHighlighting?: boolean;
}

// 에이전트 관련 타입
export interface Agent {
  agent_id: string;
  state: 'idle' | 'running' | 'finished' | 'error';
  messages: AgentMessage[];
  result: string;
}

export interface AgentMessage {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  tool_calls?: AgentToolCall[];
  tool_call_id?: string;
  name?: string;
}

export interface AgentToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

// 인덱싱 관련 타입
export interface IndexingSettings {
  is_enabled: boolean;
  frequency: 'on_commit' | 'daily' | 'weekly' | 'manual';
  excluded_patterns: string[];
  priority_patterns: string[];
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  include_comments: boolean;
  max_files_per_run: number;
  created_at?: string;
  updated_at?: string;
}

export interface IndexingStatus {
  is_indexing_now: boolean;
  current_run_id: number | null;
  last_run: IndexingRun | null;
  recent_runs: IndexingRun[];
}

export interface IndexingRun {
  id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  start_time: string | null;
  end_time: string | null;
  files_processed?: number;
  files_indexed?: number;
  files_skipped?: number;
  is_full_index?: boolean;
  error_message?: string | null;
}

export interface SearchResult {
  file_id: number;
  file_path: string;
  chunk_id: string;
  content: string;
  similarity_score: number;
  metadata: {
    file_name: string;
    language: string;
    code_elements: {
      functions: string[];
      classes: string[];
      variables: string[];
    };
  };
}

// GitHub 관련 타입
export interface GitHubUploadResult {
  message: string;
  repo_url: string;
  folder_path: string;
  commit_message: string;
}

export interface GitHubCommitMessage {
  commit_message: string;
}

export interface GitHubReadmeContent {
  readme_content: string;
}

// 자동 문서 생성 관련 타입
export interface DocGenerationTask {
  task_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  completed_docs?: string[];
  pending_docs?: string[];
  estimated_time?: number;
}

// 커뮤니케이션 기록 관련 타입
export interface HistoryItem {
  id: number;
  type: 'question' | 'response' | 'code_snippet';
  content: string;
  created_at: string;
}

// v2 API 타입
export interface MessageRequest {
  messages: {
    role: 'user' | 'assistant' | 'system';
    content: string;
  }[];
  model?: string;
  temperature?: number;
  stream?: boolean;
}

export interface MessageResponse {
  id: string;
  model: string;
  choices: {
    message: {
      role: 'assistant';
      content: string;
    };
    finish_reason: string;
  }[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}
