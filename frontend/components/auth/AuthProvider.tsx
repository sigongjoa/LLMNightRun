import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { useRouter } from 'next/router';
import api from '../../utils/api';

// 사용자 유형 정의
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_admin: boolean;
  profile_image?: string;
}

// 인증 컨텍스트 유형 정의
interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, email: string, password: string, firstName?: string, lastName?: string) => Promise<void>;
}

// 인증 컨텍스트 생성
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 인증 제공자 프롭스 정의
interface AuthProviderProps {
  children: ReactNode;
}

// 비어있는 상태로 시작할 기본 사용자 정보
const DEFAULT_USER: User | null = null;

// 퍼블릭 경로 (로그인 없이 접근 가능)
const PUBLIC_PATHS = ['/login', '/register', '/reset-password', '/'];

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [user, setUser] = useState<User | null>(DEFAULT_USER);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // 토큰이 있으면 사용자 정보 로드
  useEffect(() => {
    const checkAuth = async () => {
      // 브라우저 환경인지 확인
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      if (token) {
        try {
          // 토큰을 헤더에 설정
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // 사용자 정보 요청
          const response = await api.get('/users/me/');
          setUser(response.data);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('인증 검증 실패:', error);
          if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
          delete api.defaults.headers.common['Authorization'];
        }
      }
      
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  // 현재 경로가 보호된 경로인지 확인
  useEffect(() => {
    if (!isLoading) {
      // 사용자가 인증되지 않았고, 현재 경로가 퍼블릭이 아니면 로그인 페이지로 리디렉션
      if (!isAuthenticated && !PUBLIC_PATHS.includes(router.pathname)) {
        router.push('/login');
      }
    }
  }, [isAuthenticated, isLoading, router]);

  // 로그인 함수
  const login = async (username: string, password: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // FormData 사용 시 FastAPI OAuth2 형식에 맞게 수정
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      console.log('로그인 요청 보냄:', formData.toString());
      
      const response = await api.post('/token', 
        formData.toString(),
        { 
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' } 
        }
      );
      
      // 토큰 저장
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', response.data.access_token);
      }
      
      // 헤더에 인증 토큰 설정
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      // 사용자 정보 설정
      setUser({
        id: response.data.user_id,
        username: response.data.username,
        email: response.data.email || '',
        is_active: true,
        is_admin: response.data.is_admin
      });
      
      setIsAuthenticated(true);
      
      // 대시보드로 리디렉션
      router.push('/');
    } catch (error: any) {
      console.error('로그인 오류:', error);
      if (error.response) {
        // 서버 응답이 있는 경우
        if (error.response.status === 404) {
          setError('로그인 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
        } else if (error.response.status === 401) {
          setError('아이디 또는 비밀번호가 일치하지 않습니다.');
        } else {
          setError(`로그인 오류: ${error.response.data?.detail || '알 수 없는 오류가 발생했습니다.'}`);
        }
      } else if (error.request) {
        // 요청은 보냈지만 응답을 받지 못한 경우
        setError('서버에 연결할 수 없습니다. 인터넷 연결을 확인하고 다시 시도해주세요.');
      } else {
        // 오류 설정 중 문제가 발생한 경우
        setError('로그인 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // 로그아웃 함수
  const logout = (): void => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    setIsAuthenticated(false);
    router.push('/login');
  };

  // 회원가입 함수
  const register = async (
    username: string, 
    email: string, 
    password: string, 
    firstName?: string, 
    lastName?: string
  ): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await api.post('/users/', {
        username,
        email,
        password,
        first_name: firstName,
        last_name: lastName
      });
      
      // 회원가입 성공 후 로그인 페이지로 이동
      router.push('/login?registered=true');
    } catch (error: any) {
      console.error('회원가입 오류:', error);
      setError(error.detail || '회원가입에 실패했습니다. 입력 정보를 확인하세요.');
    } finally {
      setIsLoading(false);
    }
  };

  // 인증 컨텍스트 값
  const authContextValue: AuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    error,
    login,
    logout,
    register
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// 인증 컨텍스트 사용 훅
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
