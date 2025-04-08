import axiosInstance from '../axiosInstance';
import { Question, PaginationParams } from '../../types';

/**
 * 질문 관련 API 함수
 */
export const QuestionApi = {
  /**
   * 질문 목록 조회
   */
  fetchQuestions: async (params: PaginationParams & { tag?: string } = {}): Promise<Question[]> => {
    const response = await axiosInstance.get<Question[]>('/questions/', { params });
    return response.data;
  },

  /**
   * 특정 질문 조회
   */
  fetchQuestion: async (id: number): Promise<Question> => {
    const response = await axiosInstance.get<Question>(`/questions/${id}`);
    return response.data;
  },

  /**
   * 질문 생성
   */
  createQuestion: async (question: Question): Promise<Question> => {
    const response = await axiosInstance.post<Question>('/questions/', question);
    return response.data;
  },

  /**
   * 질문 수정
   */
  updateQuestion: async (id: number, question: Partial<Question>): Promise<Question> => {
    const response = await axiosInstance.put<Question>(`/questions/${id}`, question);
    return response.data;
  },

  /**
   * 질문 삭제
   */
  deleteQuestion: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await axiosInstance.delete<{ success: boolean; message: string }>(`/questions/${id}`);
    return response.data;
  },

  /**
   * 질문 검색
   */
  searchQuestions: async (query: string, params: PaginationParams = {}): Promise<Question[]> => {
    const response = await axiosInstance.get<Question[]>('/questions/search/', {
      params: { query, ...params }
    });
    return response.data;
  }
};

export default QuestionApi;
