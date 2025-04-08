import axiosInstance from '../axiosInstance';
import { DocGenerationTask } from '../../types';

/**
 * 문서 관리 관련 API 함수
 */
export const DocsManagerApi = {
  /**
   * 문서 생성 요청
   */
  generateDocs: async (
    options: {
      codebase_id: number;
      doc_types: string[];
      output_format: string;
      git_branch?: string;
      commit_changes?: boolean;
    }
  ): Promise<DocGenerationTask> => {
    const response = await axiosInstance.post<DocGenerationTask>('/auto-docs/generate', options);
    return response.data;
  },

  /**
   * 문서 생성 상태 조회
   */
  getDocGenerationStatus: async (taskId: string): Promise<DocGenerationTask> => {
    const response = await axiosInstance.get<DocGenerationTask>(`/auto-docs/status/${taskId}`);
    return response.data;
  },

  /**
   * 생성된 문서 조회
   */
  getGeneratedDoc: async (taskId: string, docType: string): Promise<string> => {
    const response = await axiosInstance.get<string>(`/auto-docs/${taskId}/${docType}`, {
      responseType: 'text'
    });
    return response.data;
  },

  /**
   * 생성된 문서 커밋
   */
  commitGeneratedDocs: async (
    taskId: string,
    options: {
      doc_types: string[];
      commit_message: string;
      branch?: string;
      create_pr?: boolean;
      pr_title?: string;
      pr_description?: string;
    }
  ): Promise<{
    success: boolean;
    message: string;
    commit_url?: string;
    pr_url?: string;
  }> => {
    const response = await axiosInstance.post<{
      success: boolean;
      message: string;
      commit_url?: string;
      pr_url?: string;
    }>(`/auto-docs/${taskId}/commit`, options);
    return response.data;
  }
};

export default DocsManagerApi;
