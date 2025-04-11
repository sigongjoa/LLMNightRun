import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { useState, useCallback, useEffect } from 'react';

// API 기본 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 백업 서버 URL (기본 서버에 연결할 수 없는 경우)
const BACKUP_API_URL = 'http://localhost:8001';

// 현재 사용 중인 API URL
let currentApiUrl = API_BASE_URL;

// 기본 API 인스턴스 생성
const createApiInstance = (baseURL: string) => axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10초 타임아웃 설정
});

let apiInstance = createApiInstance(currentApiUrl);

// 서버 상태 확인
const checkServerStatus = async (url: string): Promise<boolean> => {
  try {
    await axios.get(`${url}/health-check`, { timeout: 3000 });
    return true;
  } catch (error) {
    console.warn(`서버 연결 실패: ${url}`, error);
    return false;
  }
};

// API 요청 훅
export const useApi = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [serverConnected, setServerConnected] = useState<boolean>(true);

  // 서버 연결 상태 확인
  useEffect(() => {
    const checkConnection = async () => {
      // 먼저 기본 서버 확인
      const isMainServerAvailable = await checkServerStatus(API_BASE_URL);
      
      if (isMainServerAvailable) {
        currentApiUrl = API_BASE_URL;
        apiInstance = createApiInstance(currentApiUrl);
        setServerConnected(true);
        return;
      }
      
      // 기본 서버에 연결할 수 없는 경우 백업 서버 확인
      const isBackupServerAvailable = await checkServerStatus(BACKUP_API_URL);
      
      if (isBackupServerAvailable) {
        currentApiUrl = BACKUP_API_URL;
        apiInstance = createApiInstance(currentApiUrl);
        setServerConnected(true);
        console.info('백업 서버로 연결됨:', BACKUP_API_URL);
      } else {
        setServerConnected(false);
        console.error('모든 서버에 연결할 수 없습니다.');
      }
    };
    
    checkConnection();
    
    // 주기적으로 서버 상태 확인
    const intervalId = setInterval(checkConnection, 30000); // 30초마다 확인
    
    return () => clearInterval(intervalId);
  }, []);

  // 토큰 가져오기
  const getToken = useCallback(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token') || '';
    }
    return '';
  }, []);

  // 토큰 설정
  apiInstance.interceptors.request.use(
    (config) => {
      const token = getToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // 오류 메시지 포맷팅
  const formatErrorMessage = (err: any): string => {
    if (err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED') {
      return '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.';
    }
    
    if (err.response?.status === 404) {
      return '요청한 리소스를 찾을 수 없습니다.';
    }
    
    if (err.response?.status === 401) {
      return '인증이, 로그인이 필요합니다.';
    }
    
    if (err.response?.status === 403) {
      return '접근 권한이 없습니다.';
    }
    
    return err.response?.data?.detail || err.message || '요청 처리 중 오류가 발생했습니다';
  };

  // GET 요청
  const get = useCallback(async <T>(
    url: string, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    if (!serverConnected) {
      throw new Error('백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiInstance.get<T>(url, config);
      return response.data;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error('API 요청 오류:', url, err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [serverConnected]);

  // POST 요청
  const post = useCallback(async <T>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    if (!serverConnected) {
      throw new Error('백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiInstance.post<T>(url, data, config);
      return response.data;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error('API 요청 오류:', url, err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [serverConnected]);

  // PUT 요청
  const put = useCallback(async <T>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    if (!serverConnected) {
      throw new Error('백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiInstance.put<T>(url, data, config);
      return response.data;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error('API 요청 오류:', url, err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [serverConnected]);

  // DELETE 요청
  const del = useCallback(async <T>(
    url: string, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    if (!serverConnected) {
      throw new Error('백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiInstance.delete<T>(url, config);
      return response.data;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error('API 요청 오류:', url, err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [serverConnected]);

  // API 인스턴스 직접 접근
  const api = useCallback((): AxiosInstance => {
    return apiInstance;
  }, []);

  return {
    loading,
    error,
    serverConnected,
    get,
    post,
    put,
    delete: del, // 'delete'는 예약어이므로 'del'로 정의하고 'delete'로 내보냄
    api,
    currentApiUrl,
  };
};

export default useApi;
