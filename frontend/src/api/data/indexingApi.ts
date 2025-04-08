import axiosInstance from '../axiosInstance';
import { IndexingSettings, IndexingStatus, SearchResult } from '../../types';

/**
 * 인덱싱 관련 API 함수
 */
export const IndexingApi = {
  /**
   * 인덱싱 설정 조회
   */
  getIndexingSettings: async (codebaseId: number): Promise<IndexingSettings> => {
    const response = await axiosInstance.get<IndexingSettings>(`/codebases/${codebaseId}/indexing/settings`);
    return response.data;
  },

  /**
   * 인덱싱 설정 업데이트
   */
  updateIndexingSettings: async (
    codebaseId: number,
    settings: Partial<IndexingSettings>
  ): Promise<{ success: boolean; message: string; settings: IndexingSettings }> => {
    const response = await axiosInstance.patch<{ success: boolean; message: string; settings: IndexingSettings }>(
      `/codebases/${codebaseId}/indexing/settings`,
      settings
    );
    return response.data;
  },

  /**
   * 인덱싱 상태 조회
   */
  getIndexingStatus: async (codebaseId: number): Promise<{ settings: IndexingSettings; status: IndexingStatus; statistics: any }> => {
    const response = await axiosInstance.get<{ settings: IndexingSettings; status: IndexingStatus; statistics: any }>(
      `/codebases/${codebaseId}/indexing/status`
    );
    return response.data;
  },

  /**
   * 인덱싱 트리거
   */
  triggerIndexing: async (
    codebaseId: number,
    options: { is_full_index?: boolean; priority_files?: number[] } = {}
  ): Promise<{ run_id: number; status: string; message: string; start_time: string | null }> => {
    const response = await axiosInstance.post<{ run_id: number; status: string; message: string; start_time: string | null }>(
      `/codebases/${codebaseId}/indexing/trigger`,
      options
    );
    return response.data;
  },

  /**
   * 코드 검색
   */
  searchCode: async (
    codebaseId: number,
    options: {
      query: string;
      limit?: number;
      threshold?: number;
      file_patterns?: string[];
      exclude_patterns?: string[];
    }
  ): Promise<{ query: string; result_count: number; results: SearchResult[] }> => {
    const response = await axiosInstance.post<{ query: string; result_count: number; results: SearchResult[] }>(
      `/codebases/${codebaseId}/indexing/search`,
      options
    );
    return response.data;
  }
};

export default IndexingApi;
