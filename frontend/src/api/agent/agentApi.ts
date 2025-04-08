import axiosInstance from '../axiosInstance';
import { Agent } from '../../types';

/**
 * 에이전트 관련 API 함수
 */
export const AgentApi = {
  /**
   * 에이전트 생성
   */
  createAgent: async (): Promise<Agent> => {
    const response = await axiosInstance.post<Agent>('/agent/create');
    return response.data;
  },

  /**
   * 에이전트 실행
   */
  runAgent: async (
    agentId: string,
    prompt: string,
    workspace?: string,
    maxSteps: number = 10
  ): Promise<Agent> => {
    const response = await axiosInstance.post<Agent>(`/agent/${agentId}/run`, {
      prompt,
      workspace,
      max_steps: maxSteps
    });
    return response.data;
  },

  /**
   * 에이전트 상태 조회
   */
  getAgentStatus: async (agentId: string): Promise<Agent> => {
    const response = await axiosInstance.get<Agent>(`/agent/${agentId}/status`);
    return response.data;
  },

  /**
   * 에이전트 삭제
   */
  deleteAgent: async (agentId: string): Promise<{ message: string }> => {
    const response = await axiosInstance.delete<{ message: string }>(`/agent/${agentId}`);
    return response.data;
  }
};

export default AgentApi;
