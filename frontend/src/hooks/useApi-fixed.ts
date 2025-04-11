import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
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

// 디버그 모드
const DEBUG = true;

// 서버 상태 확인
const checkServerStatus = async (url: string): Promise<boolean> => {
  try {
    if (DEBUG) console.log(`서버 상태 확인 중: ${url}/health-check`);
    await axios.get(`${url}/health-check`, { timeout: 3000 });
    if (DEBUG) console.log(`서버 연결 성공: ${url}`);
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
      if (DEBUG) console.log("서버 연결 상태 확인 중...");
      
      // 먼저 기본 서버 확인
      const isMainServerAvailable = await checkServerStatus(API_BASE_URL);
      
      if (isMainServerAvailable) {
        currentApiUrl = API_BASE_URL;
        apiInstance = createApiInstance(currentApiUrl);
        setServerConnected(true);
        if (DEBUG) console.log("메인 서버 연결됨:", API_BASE_URL);
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
      if (DEBUG) console.log(`요청 준비 중: ${config.method?.toUpperCase()} ${config.url}`, config.data);
      
      const token = getToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      console.error("요청 인터셉터 오류:", error);
      return Promise.reject(error);
    }
  );

  // 응답 처리
  apiInstance.interceptors.response.use(
    (response) => {
      if (DEBUG) console.log(`응답 수신: ${response.status} ${response.config.url}`, response.data);
      return response;
    },
    (error) => {
      console.error("응답 인터셉터 오류:", error);
      return Promise.reject(error);
    }
  );

  // 오류 메시지 포맷팅
  const formatErrorMessage = (err: any): string => {
    if (err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED') {
      return '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.';
    }
    
    if (err.response?.status === 404) {
      return `요청한 리소스를 찾을 수 없습니다: ${err.config?.url}`;
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
      if (DEBUG) console.log(`GET 요청 시작: ${url}`);
      const response = await apiInstance.get<T>(url, config);
      if (DEBUG) console.log(`GET 요청 성공: ${url}`, response.data);
      return response.data;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error('API GET 요청 오류:', url, err);
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
      if (DEBUG) console.log(`POST 요청 시작: ${url}`, data);
      const response = await apiInstance.post<T>(url, data, config);
      if (DEBUG) console.log(`POST 요청 성공: ${url}`, response.data);
      return response.data;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error('API POST 요청 오류:', url, err);
      
      // 응답 및 상태 코드 확인 (디버깅용)
      if (err.response) {
        console.error(`상태 코드: ${err.response.status}`);
        console.error('응답 데이터:', err.response.data);
        console.error('응답 헤더:', err.response.headers);
      } else if (err.request) {
        console.error('요청은 전송되었지만 응답이 없습니다:', err.request);
      } else {
        console.error('요청 설정 중 오류:', err.message);
      }
      
      // 연결 재시도 시도
      if (err.code === 'ERR_NETWORK') {
        console.log('서버 연결 재시도 중...');
        try {
          await checkServerStatus(currentApiUrl);
        } catch (retryErr) {
          console.error('재연결 시도 실패:', retryErr);
        }
      }
      
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
      if (DEBUG) console.log(`PUT 요청 시작: ${url}`, data);
      const response = await apiInstance.put<T>(url, data, config);
      if (DEBUG) console.log(`PUT 요청 성공: ${url}`, response.data);
      return response.data;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error('API PUT 요청 오류:', url, err);
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
      if (DEBUG) console.log(`DELETE 요청 시작: ${url}`);
      const response = await apiInstance.delete<T>(url, config);
      if (DEBUG) console.log(`DELETE 요청 성공: ${url}`, response.data);
      return response.data;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error('API DELETE 요청 오류:', url, err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [serverConnected]);

  // API 인스턴스 직접 접근
  const api = useCallback((): AxiosInstance => {
    return apiInstance;
  }, []);

  // 직접 API 호출 (응답 전체 반환)
  const fetchWithFullResponse = useCallback(async <T>(
    method: string,
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> => {
    if (!serverConnected) {
      throw new Error('백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      if (DEBUG) console.log(`${method.toUpperCase()} 요청 시작: ${url}`, data);
      let response: AxiosResponse<T>;
      
      switch (method.toLowerCase()) {
        case 'get':
          response = await apiInstance.get<T>(url, config);
          break;
        case 'post':
          response = await apiInstance.post<T>(url, data, config);
          break;
        case 'put':
          response = await apiInstance.put<T>(url, data, config);
          break;
        case 'delete':
          response = await apiInstance.delete<T>(url, config);
          break;
        default:
          throw new Error(`지원하지 않는 HTTP 메서드: ${method}`);
      }
      
      if (DEBUG) console.log(`${method.toUpperCase()} 요청 성공: ${url}`, response.data);
      return response;
    } catch (err: any) {
      const errorMessage = formatErrorMessage(err);
      setError(errorMessage);
      console.error(`API ${method.toUpperCase()} 요청 오류:`, url, err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [serverConnected]);

  return {
    loading,
    error,
    serverConnected,
    get,
    post,
    put,
    delete: del, // 'delete'는 예약어이므로 'del'로 정의하고 'delete'로 내보냄
    api,
    fetchWithFullResponse,
    currentApiUrl,
  };
};

export default useApi;
