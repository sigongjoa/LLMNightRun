import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { IndexingApi } from '../api';
import { IndexingSettings } from '../types';

// 인덱싱 관련 커스텀 훅
export const useIndexingSettings = (codebaseId: number) => {
  return useQuery(
    ['indexingSettings', codebaseId],
    () => IndexingApi.getIndexingSettings(codebaseId),
    {
      enabled: !!codebaseId, // codebaseId가 유효할 때만 쿼리 실행
    }
  );
};

export const useUpdateIndexingSettings = (codebaseId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (settings: Partial<IndexingSettings>) => IndexingApi.updateIndexingSettings(codebaseId, settings),
    {
      onSuccess: () => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['indexingSettings', codebaseId]);
        queryClient.invalidateQueries(['indexingStatus', codebaseId]);
      },
    }
  );
};

export const useIndexingStatus = (codebaseId: number) => {
  return useQuery(
    ['indexingStatus', codebaseId],
    () => IndexingApi.getIndexingStatus(codebaseId),
    {
      enabled: !!codebaseId, // codebaseId가 유효할 때만 쿼리 실행
      refetchInterval: (data) => {
        // 인덱싱 중인 경우 주기적으로 상태 확인
        return data?.status.is_indexing_now ? 3000 : false;
      },
    }
  );
};

export const useTriggerIndexing = (codebaseId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (options: { is_full_index?: boolean; priority_files?: number[] } = {}) => 
      IndexingApi.triggerIndexing(codebaseId, options),
    {
      onSuccess: () => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['indexingStatus', codebaseId]);
      },
    }
  );
};

export const useSearchCode = (codebaseId: number) => {
  return useMutation(
    (options: {
      query: string;
      limit?: number;
      threshold?: number;
      file_patterns?: string[];
      exclude_patterns?: string[];
    }) => IndexingApi.searchCode(codebaseId, options)
  );
};
