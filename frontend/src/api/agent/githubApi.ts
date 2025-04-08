import axiosInstance from '../axiosInstance';
import { GitHubUploadResult, GitHubCommitMessage, GitHubReadmeContent } from '../../types';

/**
 * GitHub 관련 API 함수
 */
export const GitHubApi = {
  /**
   * GitHub에 업로드
   */
  uploadToGitHub: async (
    questionId: number,
    folderPath?: string
  ): Promise<GitHubUploadResult> => {
    const response = await axiosInstance.post<GitHubUploadResult>('/github/upload', {
      question_id: questionId,
      folder_path: folderPath
    });
    return response.data;
  },

  /**
   * 커밋 메시지 생성
   */
  generateCommitMessage: async (questionId: number): Promise<GitHubCommitMessage> => {
    const response = await axiosInstance.get<GitHubCommitMessage>(`/github/generate-commit-message/${questionId}`);
    return response.data;
  },

  /**
   * README 생성
   */
  generateReadme: async (questionId: number): Promise<GitHubReadmeContent> => {
    const response = await axiosInstance.get<GitHubReadmeContent>(`/github/generate-readme/${questionId}`);
    return response.data;
  },

  /**
   * 저장소 콘텐츠 조회
   */
  getRepositoryContents: async (path: string = '', branch: string = 'main'): Promise<any[]> => {
    const response = await axiosInstance.get<any[]>(`/github/contents/${path}`, {
      params: { branch }
    });
    return response.data;
  },

  /**
   * 파일 내용 조회
   */
  getFileContent: async (filepath: string, branch: string = 'main'): Promise<any> => {
    const response = await axiosInstance.get<any>(`/github/files/${filepath}`, {
      params: { branch }
    });
    return response.data;
  },

  /**
   * 브랜치 생성
   */
  createBranch: async (branch: string, sourceBranch: string = 'main'): Promise<any> => {
    const response = await axiosInstance.post<any>('/github/branches', {
      branch,
      source_branch: sourceBranch
    });
    return response.data;
  },

  /**
   * PR 생성
   */
  createPullRequest: async (
    title: string,
    body: string,
    headBranch: string,
    baseBranch: string = 'main'
  ): Promise<any> => {
    const response = await axiosInstance.post<any>('/github/pull-requests', {
      title,
      body,
      head_branch: headBranch,
      base_branch: baseBranch
    });
    return response.data;
  }
};

export default GitHubApi;
