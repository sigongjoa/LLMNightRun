import axiosInstance from '../axiosInstance';

/**
 * MCP 상태 관련 API 함수
 */
export const MCPStatusApi = {
  /**
   * MCP 상태 조회
   */
  getMCPStatus: async (): Promise<{
    status: 'online' | 'offline';
    connected_agents: number;
    available_models: string[];
    version: string;
    uptime: number;
  }> => {
    const response = await axiosInstance.get<{
      status: 'online' | 'offline';
      connected_agents: number;
      available_models: string[];
      version: string;
      uptime: number;
    }>('/mcp/status');
    return response.data;
  },

  /**
   * MCP 활성 세션 조회
   */
  getMCPSessions: async (): Promise<{
    active_sessions: Array<{
      id: string;
      started_at: string;
      user: string;
      model: string;
      messages: number;
    }>;
    total: number;
  }> => {
    const response = await axiosInstance.get<{
      active_sessions: Array<{
        id: string;
        started_at: string;
        user: string;
        model: string;
        messages: number;
      }>;
      total: number;
    }>('/mcp/sessions');
    return response.data;
  },

  /**
   * MCP 로그 조회
   */
  getMCPLogs: async (limit: number = 100): Promise<{
    logs: Array<{
      timestamp: string;
      level: string;
      message: string;
      details?: any;
    }>;
  }> => {
    const response = await axiosInstance.get<{
      logs: Array<{
        timestamp: string;
        level: string;
        message: string;
        details?: any;
      }>;
    }>('/mcp/logs', { params: { limit } });
    return response.data;
  }
};

export default MCPStatusApi;
