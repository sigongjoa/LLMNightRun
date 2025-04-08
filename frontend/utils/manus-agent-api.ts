/**
 * Manus 에이전트 API 클라이언트
 */

import axios from 'axios';
import { API_BASE_URL } from './constants';

const API_URL = `${API_BASE_URL}/manus/mcp`;

// API 인스턴스 생성
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,  // 120초 타임아웃
});

/**
 * 에이전트에 쿼리를 보내고 응답을 받습니다.
 * 
 * @param query 사용자 질의
 * @param withTools 도구 사용 여부 (기본값: true)
 * @param modelId 사용할 모델 ID (선택 사항)
 */
export const sendQuery = async (
  query: string, 
  withTools: boolean = true,
  modelId?: string
) => {
  try {
    const response = await api.post(`/agent/query`, {
      query,
      with_tools: withTools,
      model_id: modelId
    });
    return response.data;
  } catch (error) {
    console.error('에이전트 쿼리 오류:', error);
    throw error;
  }
};

/**
 * 파일 작업을 수행합니다.
 * 
 * @param operation 작업 종류 ('read', 'write', 'list')
 * @param path 파일 경로
 * @param content 파일 내용 (쓰기 작업시에만 필요)
 */
export const performFileOperation = async (
  operation: 'read' | 'write' | 'list',
  path: string,
  content?: string
) => {
  try {
    const response = await api.post(`/agent/file_operation`, {
      operation,
      path,
      content
    });
    return response.data;
  } catch (error) {
    console.error('파일 작업 오류:', error);
    throw error;
  }
};

/**
 * 대화 기록을 초기화합니다.
 */
export const clearHistory = async () => {
  try {
    const response = await api.post(`/agent/history/clear`);
    return response.data;
  } catch (error) {
    console.error('대화 기록 초기화 오류:', error);
    throw error;
  }
};

/**
 * 대화 기록을 가져옵니다.
 */
export const getHistory = async () => {
  try {
    const response = await api.get(`/agent/history`);
    return response.data;
  } catch (error) {
    console.error('대화 기록 가져오기 오류:', error);
    throw error;
  }
};

/**
 * 모델 ID를 설정합니다.
 * 
 * @param modelId 사용할 모델 ID
 */
export const setModel = async (modelId: string) => {
  try {
    const response = await api.post(`/agent/set_model`, {
      model_id: modelId
    });
    return response.data;
  } catch (error) {
    console.error('모델 설정 오류:', error);
    throw error;
  }
};

/**
 * 직접 MCP 도구를 호출합니다.
 * 
 * @param name 도구 이름
 * @param arguments 도구 인자
 */
export const callTool = async (
  name: string,
  args: Record<string, any>
) => {
  try {
    const response = await api.post(`/tools/call`, {
      name,
      arguments: args
    });
    return response.data;
  } catch (error) {
    console.error('도구 호출 오류:', error);
    throw error;
  }
};

/**
 * MCP 리소스를 읽습니다.
 * 
 * @param uri 리소스 URI
 */
export const readResource = async (uri: string) => {
  try {
    const response = await api.post(`/resources/read`, {
      uri
    });
    return response.data;
  } catch (error) {
    console.error('리소스 읽기 오류:', error);
    throw error;
  }
};

/**
 * 사용 가능한 MCP 도구 목록을 가져옵니다.
 */
export const listTools = async () => {
  try {
    const response = await api.post(`/tools/list`);
    return response.data;
  } catch (error) {
    console.error('도구 목록 가져오기 오류:', error);
    throw error;
  }
};

/**
 * 사용 가능한 MCP 리소스 목록을 가져옵니다.
 */
export const listResources = async () => {
  try {
    const response = await api.post(`/resources/list`);
    return response.data;
  } catch (error) {
    console.error('리소스 목록 가져오기 오류:', error);
    throw error;
  }
};
