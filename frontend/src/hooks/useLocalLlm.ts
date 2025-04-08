import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LocalLlmApi } from '../api';

// 로컬 LLM 관련 커스텀 훅
export const useChatWithLocalLLM = () => {
  return useMutation(
    (messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>) => 
      LocalLlmApi.chatWithLocalLLM(messages)
  );
};

export const useLocalLLMStatus = () => {
  return useQuery(
    ['localLlmStatus'],
    () => LocalLlmApi.getLocalLLMStatus(),
    {
      refetchInterval: (data) => {
        // 로딩 중인 경우 더 자주 갱신
        return data?.status === 'loading' ? 1000 : 10000;
      },
    }
  );
};

export const useLocalLLMSettings = () => {
  return useQuery(
    ['localLlmSettings'],
    () => LocalLlmApi.getLocalLLMSettings()
  );
};

export const useUpdateLocalLLMSettings = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (settings: Partial<{
      model_path: string;
      model_name: string;
      quantization: string;
      context_size: number;
      temperature: number;
      top_p: number;
      max_tokens: number;
      autoload: boolean;
    }>) => LocalLlmApi.updateLocalLLMSettings(settings),
    {
      onSuccess: () => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['localLlmSettings']);
      },
    }
  );
};

export const useStartLocalLLM = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    () => LocalLlmApi.startLocalLLM(),
    {
      onSuccess: () => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['localLlmStatus']);
      },
    }
  );
};

export const useStopLocalLLM = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    () => LocalLlmApi.stopLocalLLM(),
    {
      onSuccess: () => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['localLlmStatus']);
      },
    }
  );
};
