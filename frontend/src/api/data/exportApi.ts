import axiosInstance from '../axiosInstance';
import { ExportFormat, ExportOptions } from '../../types';

/**
 * 내보내기 관련 API 함수
 */
export const ExportApi = {
  /**
   * 질문 내보내기
   */
  exportQuestion: async (
    questionId: number,
    format: ExportFormat,
    options: ExportOptions = {}
  ): Promise<Blob> => {
    const params = {
      format,
      include_metadata: options.includeMetadata,
      include_tags: options.includeTags,
      include_timestamps: options.includeTimestamps,
      include_llm_info: options.includeLlmInfo,
      code_highlighting: options.codeHighlighting
    };

    const response = await axiosInstance.get(`/export/question/${questionId}`, {
      params,
      responseType: 'blob'
    });

    return response.data;
  },

  /**
   * 코드 스니펫 내보내기
   */
  exportCodeSnippet: async (
    snippetId: number,
    format: ExportFormat,
    options: ExportOptions = {}
  ): Promise<Blob> => {
    const params = {
      format,
      include_metadata: options.includeMetadata,
      include_tags: options.includeTags,
      include_timestamps: options.includeTimestamps,
      include_llm_info: options.includeLlmInfo
    };

    const response = await axiosInstance.get(`/export/code-snippet/${snippetId}`, {
      params,
      responseType: 'blob'
    });

    return response.data;
  },

  /**
   * 에이전트 로그 내보내기
   */
  exportAgentLogs: async (
    sessionId: string,
    format: ExportFormat,
    options: ExportOptions = {}
  ): Promise<Blob> => {
    const params = {
      format,
      include_timestamps: options.includeTimestamps
    };

    const response = await axiosInstance.get(`/export/agent-logs/${sessionId}`, {
      params,
      responseType: 'blob'
    });

    return response.data;
  },

  /**
   * 일괄 내보내기
   */
  exportBatch: async (
    items: Array<{ type: 'question' | 'code_snippet' | 'agent_logs'; id: number | string }>,
    format: ExportFormat,
    options: ExportOptions = {}
  ): Promise<Blob> => {
    const params = {
      format,
      include_metadata: options.includeMetadata,
      include_tags: options.includeTags,
      include_timestamps: options.includeTimestamps,
      include_llm_info: options.includeLlmInfo
    };

    const response = await axiosInstance.post('/export/batch', items, {
      params,
      responseType: 'blob'
    });

    return response.data;
  },

  /**
   * 다운로드 헬퍼 함수
   */
  downloadBlob: (blob: Blob, filename: string): void => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};

export default ExportApi;
