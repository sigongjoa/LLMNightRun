/**
 * API client for MCP server management
 */

import axios from 'axios';
import { API_BASE_URL } from '../constants';

export interface ServerConfig {
  command: string;
  args: string[];
  env: Record<string, string>;
}

export interface ServerInfo {
  id: string;
  command: string;
  args: string[];
  running: boolean;
}

export interface ServerStatus {
  id: string;
  exists: boolean;
  running: boolean;
  config?: ServerConfig;
  pid?: number;
  uptime?: number;
}

export interface ServerActionResponse {
  success: boolean;
  message: string;
}

export interface MCPConfig {
  mcpServers: Record<string, ServerConfig>;
}

const API_URL = `${API_BASE_URL}/api/mcp`;

/**
 * MCP API client
 */
export const mcpApi = {
  /**
   * Get all configured MCP servers
   */
  listServers: async (): Promise<ServerInfo[]> => {
    const response = await axios.get(`${API_URL}/servers`);
    return response.data;
  },

  /**
   * Get status of a specific server
   */
  getServerStatus: async (serverId: string): Promise<ServerStatus> => {
    const response = await axios.get(`${API_URL}/servers/${serverId}`);
    return response.data;
  },

  /**
   * Create or update a server configuration
   */
  updateServer: async (serverId: string, config: ServerConfig): Promise<ServerActionResponse> => {
    const response = await axios.post(`${API_URL}/servers/${serverId}`, config);
    return response.data;
  },

  /**
   * Delete a server configuration
   */
  deleteServer: async (serverId: string): Promise<ServerActionResponse> => {
    const response = await axios.delete(`${API_URL}/servers/${serverId}`);
    return response.data;
  },

  /**
   * Start a server
   */
  startServer: async (serverId: string): Promise<ServerActionResponse> => {
    const response = await axios.post(`${API_URL}/servers/${serverId}/start`);
    return response.data;
  },

  /**
   * Stop a server
   */
  stopServer: async (serverId: string): Promise<ServerActionResponse> => {
    const response = await axios.post(`${API_URL}/servers/${serverId}/stop`);
    return response.data;
  },

  /**
   * Restart a server
   */
  restartServer: async (serverId: string): Promise<ServerActionResponse> => {
    const response = await axios.post(`${API_URL}/servers/${serverId}/restart`);
    return response.data;
  },

  /**
   * Start all servers
   */
  startAllServers: async (): Promise<Record<string, ServerActionResponse>> => {
    const response = await axios.post(`${API_URL}/start-all`);
    return response.data;
  },

  /**
   * Stop all servers
   */
  stopAllServers: async (): Promise<Record<string, ServerActionResponse>> => {
    const response = await axios.post(`${API_URL}/stop-all`);
    return response.data;
  },

  /**
   * Get the full MCP configuration
   */
  getConfig: async (): Promise<MCPConfig> => {
    const response = await axios.get(`${API_URL}/config`);
    return response.data;
  },

  /**
   * Update the complete MCP configuration
   */
  updateConfig: async (config: MCPConfig): Promise<ServerActionResponse> => {
    const response = await axios.put(`${API_URL}/config`, config);
    return response.data;
  }
};
