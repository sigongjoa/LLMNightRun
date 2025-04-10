/**
 * GitHub 관련 타입 정의
 */

export interface GitHubRepository {
  id: number;
  name: string;
  description?: string;
  owner: string;
  url?: string;
  is_default: boolean;
  is_private: boolean;
  branch: string;
  project_id?: number;
}

export interface GitHubRepositoryCreate {
  name: string;
  description?: string;
  owner: string;
  token: string;
  is_default?: boolean;
  is_private?: boolean;
  branch?: string;
  project_id?: number;
}

export interface GitHubRepositoryUpdate {
  name?: string;
  description?: string;
  owner?: string;
  token?: string;
  is_default?: boolean;
  is_private?: boolean;
  branch?: string;
  project_id?: number;
}

export interface GitHubUploadResult {
  success: boolean;
  message: string;
  repo_url: string;
  folder_path: string;
  commit_message: string;
  files?: string[];
}

export interface GitHubCommitMessage {
  commit_message: string;
}

export interface GitHubReadmeContent {
  readme_content: string;
}

export interface GitHubRepositoriesResponse {
  repositories: GitHubRepository[];
}
