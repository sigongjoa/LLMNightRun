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

/**
 * WebSocket client for real-time MCP server status
 */
export class MCPWebSocketClient {
  private socket: WebSocket | null = null;
  private reconnectTimeout: any = null;
  private listeners: Array<(data: any) => void> = [];

  /**
   * Create a new WebSocket connection
   */
  connect(): void {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/mcp/status`;
    
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onopen = () => {
      console.log('MCP WebSocket connected');
      clearTimeout(this.reconnectTimeout);
    };
    
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.notifyListeners(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.socket.onclose = () => {
      console.log('MCP WebSocket disconnected');
      this.reconnect();
    };
    
    this.socket.onerror = (error) => {
      console.error('MCP WebSocket error:', error);
      this.socket?.close();
    };
  }
  
  /**
   * Reconnect to the WebSocket after a delay
   */
  private reconnect(): void {
    clearTimeout(this.reconnectTimeout);
    this.reconnectTimeout = setTimeout(() => {
      console.log('Attempting to reconnect MCP WebSocket...');
      this.connect();
    }, 3000);
  }
  
  /**
   * Send a command to the server
   */
  sendCommand(command: string, data: any = {}): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        command,
        ...data
      }));
    } else {
      console.error('WebSocket not connected, cannot send command');
    }
  }
  
  /**
   * Add a listener for WebSocket messages
   */
  addListener(listener: (data: any) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }
  
  /**
   * Notify all listeners of a message
   */
  private notifyListeners(data: any): void {
    this.listeners.forEach(listener => {
      try {
        listener(data);
      } catch (error) {
        console.error('Error in WebSocket listener:', error);
      }
    });
  }
  
  /**
   * Close the WebSocket connection
   */
  disconnect(): void {
    clearTimeout(this.reconnectTimeout);
    if (this.socket) {
      this.socket.onclose = null; // Prevent auto-reconnect
      this.socket.close();
      this.socket = null;
    }
  }
}

// Singleton instance of the WebSocket client
export const mcpWebSocketClient = new MCPWebSocketClient();
