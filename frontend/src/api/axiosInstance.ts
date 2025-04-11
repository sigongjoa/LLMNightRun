import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import { ApiError } from '../types';

// API 기본 URL 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Axios 인스턴스 생성 및 설정
 */
const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120초 타임아웃
});

/**
 * 요청 인터셉터
 * 요청이 서버로 전송되기 전에 실행됨
 */
axiosInstance.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 토큰이 있는 경우 인증 헤더 추가
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    console.error('API 요청 오류:', error);
    return Promise.reject(error);
  }
);

/**
 * 응답 인터셉터
 * 서버의 응답이 클라이언트에 도달하기 전에 실행됨
 */
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // API 오류 처리
    const apiError: ApiError = error.response?.data || { 
      detail: '알 수 없는 오류가 발생했습니다.',
      code: 'UNKNOWN_ERROR' 
    };
    
    console.error('API 응답 오류:', apiError);
    
    // 인증 오류(401) 처리
    if (error.response?.status === 401) {
      console.error('인증 오류: 로그인이 필요합니다');
      
      // 브라우저 환경에서만 실행
      if (typeof window !== 'undefined') {
        // 현재 페이지가 로그인 페이지가 아닌 경우에만 리디렉션
        if (!window.location.pathname.includes('/login')) {
          // 토큰 제거
          localStorage.removeItem('token');
          // 로그인 페이지로 리디렉션
          window.location.href = '/login?expired=true';
        }
      }
    }
    
    return Promise.reject(apiError);
  }
);

export default axiosInstance;
