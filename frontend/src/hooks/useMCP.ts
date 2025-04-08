import { useQuery } from '@tanstack/react-query';
import { MCPStatusApi } from '../api';

// MCP 상태 관련 커스텀 훅
export const useMCPStatus = () => {
  return useQuery(
    ['mcpStatus'],
    () => MCPStatusApi.getMCPStatus(),
    {
      refetchInterval: 30000, // 30초마다 자동 갱신
    }
  );
};

export const useMCPSessions = () => {
  return useQuery(
    ['mcpSessions'],
    () => MCPStatusApi.getMCPSessions(),
    {
      refetchInterval: 5000, // 5초마다 자동 갱신
    }
  );
};

export const useMCPLogs = (limit: number = 100) => {
  return useQuery(
    ['mcpLogs', limit],
    () => MCPStatusApi.getMCPLogs(limit)
  );
};
