import axiosInstance from '../axiosInstance';
import { CodeSnippet, CodeTemplate, PaginationParams } from '../../types';

/**
 * 코드 스니펫 및 템플릿 관련 API 함수
 */
export const CodeApi = {
  /**
   * 코드 스니펫 목록 조회
   */
  fetchCodeSnippets: async (
    params: PaginationParams & { language?: string; tag?: string } = {}
  ): Promise<CodeSnippet[]> => {
    const response = await axiosInstance.get<CodeSnippet[]>('/code-snippets/', { params });
    return response.data;
  },

  /**
   * 특정 코드 스니펫 조회
   */
  fetchCodeSnippet: async (id: number): Promise<CodeSnippet> => {
    const response = await axiosInstance.get<CodeSnippet>(`/code-snippets/${id}`);
    return response.data;
  },

  /**
   * 코드 스니펫 생성
   */
  createCodeSnippet: async (snippet: CodeSnippet): Promise<CodeSnippet> => {
    const response = await axiosInstance.post<CodeSnippet>('/code-snippets/', snippet);
    return response.data;
  },

  /**
   * 코드 스니펫 수정 (새 버전 생성)
   */
  updateCodeSnippet: async (id: number, snippet: Partial<CodeSnippet>): Promise<CodeSnippet> => {
    const response = await axiosInstance.put<CodeSnippet>(`/code-snippets/${id}`, snippet);
    return response.data;
  },

  /**
   * 코드 스니펫 삭제
   */
  deleteCodeSnippet: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await axiosInstance.delete<{ success: boolean; message: string }>(`/code-snippets/${id}`);
    return response.data;
  },

  /**
   * 코드 템플릿 목록 조회
   */
  fetchCodeTemplates: async (
    params: PaginationParams & { language?: string; tag?: string } = {}
  ): Promise<CodeTemplate[]> => {
    const response = await axiosInstance.get<CodeTemplate[]>('/code-templates/', { params });
    return response.data;
  },

  /**
   * 특정 코드 템플릿 조회
   */
  fetchCodeTemplate: async (id: number): Promise<CodeTemplate> => {
    const response = await axiosInstance.get<CodeTemplate>(`/code-templates/${id}`);
    return response.data;
  },

  /**
   * 코드 템플릿 생성
   */
  createCodeTemplate: async (template: CodeTemplate): Promise<CodeTemplate> => {
    const response = await axiosInstance.post<CodeTemplate>('/code-templates/', template);
    return response.data;
  },

  /**
   * 코드 템플릿 수정
   */
  updateCodeTemplate: async (id: number, template: Partial<CodeTemplate>): Promise<CodeTemplate> => {
    const response = await axiosInstance.put<CodeTemplate>(`/code-templates/${id}`, template);
    return response.data;
  },

  /**
   * 코드 템플릿 삭제
   */
  deleteCodeTemplate: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await axiosInstance.delete<{ success: boolean; message: string }>(`/code-templates/${id}`);
    return response.data;
  }
};

export default CodeApi;
