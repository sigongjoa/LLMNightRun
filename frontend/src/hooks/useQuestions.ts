import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { QuestionApi } from '../api';
import { Question, PaginationParams } from '../types';

// 질문 관련 커스텀 훅
export const useQuestions = (params: PaginationParams & { tag?: string } = {}) => {
  return useQuery(['questions', params], () => QuestionApi.fetchQuestions(params), {
    keepPreviousData: true,
  });
};

export const useQuestion = (id: number) => {
  return useQuery(['question', id], () => QuestionApi.fetchQuestion(id), {
    enabled: !!id, // id가 유효할 때만 쿼리 실행
  });
};

export const useCreateQuestion = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (question: Question) => QuestionApi.createQuestion(question),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['questions']);
        // 새로 생성된 질문을 캐시에 추가
        queryClient.setQueryData(['question', data.id], data);
      },
    }
  );
};

export const useUpdateQuestion = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ id, question }: { id: number; question: Partial<Question> }) => 
      QuestionApi.updateQuestion(id, question),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['questions']);
        queryClient.setQueryData(['question', data.id], data);
      },
    }
  );
};

export const useDeleteQuestion = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (id: number) => QuestionApi.deleteQuestion(id),
    {
      onSuccess: (_, id) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['questions']);
        queryClient.removeQueries(['question', id]);
      },
    }
  );
};

export const useSearchQuestions = (query: string, params: PaginationParams = {}) => {
  return useQuery(
    ['questions', 'search', query, params],
    () => QuestionApi.searchQuestions(query, params),
    {
      enabled: !!query, // 검색어가 있을 때만 쿼리 실행
      keepPreviousData: true,
    }
  );
};
