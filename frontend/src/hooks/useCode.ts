import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CodeApi } from '../api';
import { CodeSnippet, CodeTemplate, PaginationParams } from '../types';

// 코드 스니펫 관련 훅
export const useCodeSnippets = (params: PaginationParams & { language?: string; tag?: string } = {}) => {
  return useQuery(
    ['codeSnippets', params],
    () => CodeApi.fetchCodeSnippets(params),
    {
      keepPreviousData: true,
    }
  );
};

export const useCodeSnippet = (id: number) => {
  return useQuery(['codeSnippet', id], () => CodeApi.fetchCodeSnippet(id), {
    enabled: !!id, // id가 유효할 때만 쿼리 실행
  });
};

export const useCreateCodeSnippet = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (snippet: CodeSnippet) => CodeApi.createCodeSnippet(snippet),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['codeSnippets']);
        // 새로 생성된 스니펫을 캐시에 추가
        queryClient.setQueryData(['codeSnippet', data.id], data);
      },
    }
  );
};

export const useUpdateCodeSnippet = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ id, snippet }: { id: number; snippet: Partial<CodeSnippet> }) => 
      CodeApi.updateCodeSnippet(id, snippet),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['codeSnippets']);
        queryClient.setQueryData(['codeSnippet', data.id], data);
      },
    }
  );
};

export const useDeleteCodeSnippet = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (id: number) => CodeApi.deleteCodeSnippet(id),
    {
      onSuccess: (_, id) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['codeSnippets']);
        queryClient.removeQueries(['codeSnippet', id]);
      },
    }
  );
};

// 코드 템플릿 관련 훅
export const useCodeTemplates = (params: PaginationParams & { language?: string; tag?: string } = {}) => {
  return useQuery(
    ['codeTemplates', params],
    () => CodeApi.fetchCodeTemplates(params),
    {
      keepPreviousData: true,
    }
  );
};

export const useCodeTemplate = (id: number) => {
  return useQuery(['codeTemplate', id], () => CodeApi.fetchCodeTemplate(id), {
    enabled: !!id, // id가 유효할 때만 쿼리 실행
  });
};

export const useCreateCodeTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (template: CodeTemplate) => CodeApi.createCodeTemplate(template),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['codeTemplates']);
        // 새로 생성된 템플릿을 캐시에 추가
        queryClient.setQueryData(['codeTemplate', data.id], data);
      },
    }
  );
};

export const useUpdateCodeTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ id, template }: { id: number; template: Partial<CodeTemplate> }) => 
      CodeApi.updateCodeTemplate(id, template),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['codeTemplates']);
        queryClient.setQueryData(['codeTemplate', data.id], data);
      },
    }
  );
};

export const useDeleteCodeTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (id: number) => CodeApi.deleteCodeTemplate(id),
    {
      onSuccess: (_, id) => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['codeTemplates']);
        queryClient.removeQueries(['codeTemplate', id]);
      },
    }
  );
};
