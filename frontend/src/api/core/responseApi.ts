import axiosInstance from '../axiosInstance';
import { Response, Question, LLMType, PaginationParams } from '../../types';

/**
 * 응답 관련 API 함수
 */
export const ResponseApi = {
  /**
   * 응답 목록 조회
   */
  fetchResponses: async (
    params: PaginationParams & { question_id?: number; llm_type?: LLMType } = {}
  ): Promise<Response[]> => {
    const response = await axiosInstance.get<Response[]>('/responses/', { params });
    return response.data;
  },

  /**
   * 특정 응답 조회
   */
  fetchResponse: async (id: number): Promise<Response> => {
    const response = await axiosInstance.get<Response>(`/responses/${id}`);
    return response.data;
  },

  /**
   * 응답 생성
   */
  createResponse: async (responseData: Partial<Response>): Promise<Response> => {
    const response = await axiosInstance.post<Response>('/responses/', responseData);
    return response.data;
  },

  /**
   * 응답 삭제
   */
  deleteResponse: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await axiosInstance.delete<{ success: boolean; message: string }>(`/responses/${id}`);
    return response.data;
  },

  /**
   * LLM에 질문 요청
   */
  askLLM: async (
    llmType: LLMType,
    question: Question
  ): Promise<{ question: Question; response: Response }> => {
    // 로컬 LLM인 경우 다른 API 엔드포인트 사용
    if (llmType === LLMType.LOCAL_LLM) {
      const localResponse = await axiosInstance.post('/api/local-llm/chat', {
        messages: [{ role: 'user', content: question.content }]
      });

      // 질문 ID가 없는 경우 질문 먼저 생성
      let questionObj = question;
      if (!question.id) {
        const createdQuestion = await ResponseApi.createQuestion(question);
        questionObj = createdQuestion;
      }

      // 응답 저장
      const responseData: Partial<Response> = {
        question_id: questionObj.id || 0,
        llm_type: LLMType.LOCAL_LLM,
        content: localResponse.data.content
      };

      const savedResponse = await ResponseApi.createResponse(responseData);

      // 응답 형식 변환
      return {
        question: questionObj,
        response: savedResponse
      };
    }

    // 기존 다른 LLM 유형들은 원래 API 사용
    const response = await axiosInstance.post<{ question: Question; response: Response }>(`/ask/${llmType}`, question);
    return response.data;
  },

  /**
   * 질문 생성 (private)
   */
  private createQuestion: async (question: Question): Promise<Question> => {
    const response = await axiosInstance.post<Question>('/questions/', question);
    return response.data;
  }
};

export default ResponseApi;
