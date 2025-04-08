/**
 * MCP 상태 API client
 */

import axios from 'axios';
import { API_BASE_URL } from '../constants';

export interface MCPServerInfo {
  id: string;
  command: string;
  args: string[];
  running: boolean;
}

export interface MCPServerStatus {
  id: string;
  exists: boolean;
  running: boolean;
  config?: {
    command: string;
    args: string[];
    env: Record<string, string>;
  };
  pid?: number;
  uptime?: number;
}

export interface MCPTool {
  name: string;
  description: string;
  server: string;
  schema?: any;
}

const API_URL = `${API_BASE_URL}/mcp-status`;

/**
 * MCP 상태 API client
 */
export const mcpStatusApi = {
  /**
   * 등록된 MCP 서버 목록 가져오기
   */
  getServers: async (): Promise<MCPServerInfo[]> => {
    const response = await axios.get(`${API_URL}/servers`);
    return response.data.servers;
  },

  /**
   * 특정 MCP 서버 상태 조회
   */
  getServerStatus: async (serverId: string): Promise<MCPServerStatus> => {
    const response = await axios.get(`${API_URL}/servers/${serverId}`);
    return response.data.server;
  },

  /**
   * MCP 설정 조회
   */
  getConfig: async (): Promise<any> => {
    const response = await axios.get(`${API_URL}/config`);
    return response.data.config;
  },

  /**
   * 사용 가능한 MCP 도구 목록 조회
   */
  getTools: async (): Promise<MCPTool[]> => {
    const response = await axios.get(`${API_URL}/tools`);
    return response.data.tools;
  }
};
