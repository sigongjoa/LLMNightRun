import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ResponseApi } from '../api';
import { Response, Question, LLMType, PaginationParams } from '../types';

// 응답 관련 커스텀 훅
export const useResponses = (params: PaginationParams & { question_id?: number; llm_type?: LLMType } = {}) => {
  return useQuery(
    ['responses', params],
    () => ResponseApi.fetchResponses(params),
    {
      keepPreviousData: true,
      enabled: params.question_id !== undefined || params.llm_type !== undefined || true,
    }
  );
};

export const useResponse = (id: number) => {
  return useQuery(['response', id], () => ResponseApi.fetchResponse(id), {
    enabled: !!id, // id가 유효할 때만 쿼리 실행
  });
};

export const useCreateResponse = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (response: Partial<Response>) => ResponseApi.createResponse(response),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['responses']);
        // 새로 생성된 응답을 캐시에 추가
        queryClient.setQueryData(['response', data.id], data);
        // 관련 질문의 응답 목록 캐시도 업데이트
        if (data.question_id) {
          queryClient.invalidateQueries(['responses', { question_id: data.question_id }]);
        }
      },
    }
  );
};

export const useDeleteResponse = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (id: number) => ResponseApi.deleteResponse(id),
    {
      onSuccess: (_, id) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['responses']);
        queryClient.removeQueries(['response', id]);
      },
    }
  );
};

export const useAskLLM = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ llmType, question }: { llmType: LLMType; question: Question }) => 
      ResponseApi.askLLM(llmType, question),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['questions']);
        queryClient.invalidateQueries(['responses']);
        // 새로운 질문 캐싱
        if (data.question.id) {
          queryClient.setQueryData(['question', data.question.id], data.question);
        }
        // 새로운 응답 캐싱
        if (data.response.id) {
          queryClient.setQueryData(['response', data.response.id], data.response);
        }
      },
    }
  );
};
