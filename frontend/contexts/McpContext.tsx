import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { 
  mcpApi, 
  ServerInfo,
  ServerStatus,
  ServerConfig,
  MCPConfig
} from '../utils/mcp/api';

interface McpContextType {
  servers: ServerInfo[];
  isLoading: boolean;
  error: string | null;
  refreshServers: () => Promise<void>;
  startServer: (serverId: string) => Promise<void>;
  stopServer: (serverId: string) => Promise<void>;
  restartServer: (serverId: string) => Promise<void>;
  getServerStatus: (serverId: string) => Promise<ServerStatus>;
  updateServer: (serverId: string, config: ServerConfig) => Promise<void>;
  deleteServer: (serverId: string) => Promise<void>;
  getConfig: () => Promise<MCPConfig>;
  updateConfig: (config: MCPConfig) => Promise<void>;
  startAllServers: () => Promise<void>;
  stopAllServers: () => Promise<void>;
}

const McpContext = createContext<McpContextType | undefined>(undefined);

export const McpProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  const [servers, setServers] = useState<ServerInfo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshServers = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await mcpApi.listServers();
      setServers(data);
      return data; // 데이터 반환하여 다른 메서드에서 활용 가능
    } catch (err) {
      console.error('Error fetching MCP servers:', err);
      setError('서버 목록을 가져오는 중 오류가 발생했습니다.');
      setServers([]); // 오류 발생 시 빈 배열로 설정하여 UI가 깨지지 않도록 함
      return []; // 빈 배열 반환
    } finally {
      setIsLoading(false);
    }
  };

  const startServer = async (serverId: string) => {
    try {
      setIsLoading(true);
      await mcpApi.startServer(serverId);
      await refreshServers();
    } catch (err) {
      console.error(`Error starting server ${serverId}:`, err);
      setError(`서버 시작 중 오류가 발생했습니다: ${serverId}`);
      // 오류를 던지지 않고 처리하여 UI가 계속 작동하도록 함
    } finally {
      setIsLoading(false);
    }
  };

  const stopServer = async (serverId: string) => {
    try {
      setIsLoading(true);
      await mcpApi.stopServer(serverId);
      await refreshServers();
    } catch (err) {
      console.error(`Error stopping server ${serverId}:`, err);
      setError(`서버 중지 중 오류가 발생했습니다: ${serverId}`);
      // 오류를 던지지 않고 처리하여 UI가 계속 작동하도록 함
    } finally {
      setIsLoading(false);
    }
  };

  const restartServer = async (serverId: string) => {
    try {
      setIsLoading(true);
      await mcpApi.restartServer(serverId);
      await refreshServers();
    } catch (err) {
      console.error(`Error restarting server ${serverId}:`, err);
      setError(`서버 재시작 중 오류가 발생했습니다: ${serverId}`);
      // 오류를 던지지 않고 처리하여 UI가 계속 작동하도록 함
    } finally {
      setIsLoading(false);
    }
  };

  const getServerStatus = async (serverId: string) => {
    try {
      return await mcpApi.getServerStatus(serverId);
    } catch (err) {
      console.error(`Error getting server status ${serverId}:`, err);
      setError(`서버 상태 조회 중 오류가 발생했습니다: ${serverId}`);
      throw err;
    }
  };

  const updateServer = async (serverId: string, config: ServerConfig) => {
    try {
      await mcpApi.updateServer(serverId, config);
      refreshServers();
    } catch (err) {
      console.error(`Error updating server ${serverId}:`, err);
      setError(`서버 설정 업데이트 중 오류가 발생했습니다: ${serverId}`);
      throw err;
    }
  };

  const deleteServer = async (serverId: string) => {
    try {
      await mcpApi.deleteServer(serverId);
      refreshServers();
    } catch (err) {
      console.error(`Error deleting server ${serverId}:`, err);
      setError(`서버 삭제 중 오류가 발생했습니다: ${serverId}`);
      throw err;
    }
  };

  const getConfig = async () => {
    try {
      return await mcpApi.getConfig();
    } catch (err) {
      console.error('Error getting MCP config:', err);
      setError('MCP 설정을 가져오는 중 오류가 발생했습니다.');
      throw err;
    }
  };

  const updateConfig = async (config: MCPConfig) => {
    try {
      await mcpApi.updateConfig(config);
      refreshServers();
    } catch (err) {
      console.error('Error updating MCP config:', err);
      setError('MCP 설정 업데이트 중 오류가 발생했습니다.');
      throw err;
    }
  };

  const startAllServers = async () => {
    try {
      setIsLoading(true);
      await mcpApi.startAllServers();
      await refreshServers();
    } catch (err) {
      console.error('Error starting all servers:', err);
      setError('모든 서버 시작 중 오류가 발생했습니다.');
      // 오류를 던지지 않고 처리
    } finally {
      setIsLoading(false);
    }
  };

  const stopAllServers = async () => {
    try {
      setIsLoading(true);
      await mcpApi.stopAllServers();
      await refreshServers();
    } catch (err) {
      console.error('Error stopping all servers:', err);
      setError('모든 서버 중지 중 오류가 발생했습니다.');
      // 오류를 던지지 않고 처리
    } finally {
      setIsLoading(false);
    }
  };

  // 초기 데이터 로드 및 주기적 새로고침
  useEffect(() => {
    // 초기 서버 목록 로드
    refreshServers();
    
    // 주기적으로 서버 상태 업데이트 (10초마다)
    const intervalId = setInterval(() => {
      refreshServers();
    }, 10000);
    
    // Clean up
    return () => {
      clearInterval(intervalId);
    };
  }, []);

  const value = {
    servers,
    isLoading,
    error,
    refreshServers,
    startServer,
    stopServer,
    restartServer,
    getServerStatus,
    updateServer,
    deleteServer,
    getConfig,
    updateConfig,
    startAllServers,
    stopAllServers,
  };

  return <McpContext.Provider value={value}>{children}</McpContext.Provider>;
};

export const useMcp = () => {
  const context = useContext(McpContext);
  if (context === undefined) {
    throw new Error('useMcp must be used within a McpProvider');
  }
  return context;
};
