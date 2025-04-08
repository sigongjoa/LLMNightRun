import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AgentApi } from '../api';
import { Agent } from '../types';

// 에이전트 관련 커스텀 훅
export const useCreateAgent = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    () => AgentApi.createAgent(),
    {
      onSuccess: (data) => {
        // 성공 시 캐시에 에이전트 상태 추가
        queryClient.setQueryData(['agent', data.agent_id], data);
      },
    }
  );
};

export const useRunAgent = (agentId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ prompt, workspace, maxSteps }: { prompt: string; workspace?: string; maxSteps?: number }) => 
      AgentApi.runAgent(agentId, prompt, workspace, maxSteps),
    {
      onSuccess: (data) => {
        // 성공 시 캐시 업데이트
        queryClient.setQueryData(['agent', data.agent_id], data);
      },
    }
  );
};

export const useAgentStatus = (agentId: string) => {
  return useQuery(
    ['agent', agentId],
    () => AgentApi.getAgentStatus(agentId),
    {
      enabled: !!agentId, // agentId가 유효할 때만 쿼리 실행
      refetchInterval: (data) => {
        // 에이전트가 실행 중인 경우 주기적으로 상태 확인
        return data?.state === 'running' ? 1000 : false;
      },
    }
  );
};

export const useDeleteAgent = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (agentId: string) => AgentApi.deleteAgent(agentId),
    {
      onSuccess: (_, agentId) => {
        // 성공 시 캐시에서 에이전트 제거
        queryClient.removeQueries(['agent', agentId]);
      },
    }
  );
};
