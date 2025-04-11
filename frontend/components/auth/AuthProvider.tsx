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

// 기본 사용자 정보 (자동 로그인용)
const DEFAULT_USER: User = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  is_active: true,
  is_admin: true,
  profile_image: undefined
};

// 퍼블릭 경로 (로그인 없이 접근 가능)
const PUBLIC_PATHS = ['/login', '/register', '/reset-password', '/'];

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // 항상 인증된 상태로 시작
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [user, setUser] = useState<User>(DEFAULT_USER);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  
  // 초기 상태 설정 - 항상 인증되도록 설정
  useEffect(() => {
    // 로컬 스토리지에 기본 사용자 정보 설정
    const defaultUser = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      is_active: true,
      is_admin: true
    };
    
    setUser(defaultUser);
    setIsAuthenticated(true);
    setIsLoading(false);
    
    // 세션 스토리지에 사용자 정보 저장 (출처 기록용)
    sessionStorage.setItem('user', JSON.stringify({
      username: 'admin',
      is_admin: true
    }));
    
    // 인증 헤더 설정
    api.defaults.headers.common['Authorization'] = 'Bearer dummy-token-for-auth';
  }, []);

  // 보호된 경로 검사 제거 - 항상 접근 허용
  useEffect(() => {
    // 로그인/회원가입 페이지 접근 시 홈으로 리디렉션
    if (router.pathname === '/login' || router.pathname === '/register') {
      router.push('/');
    }
  }, [router]);

  // 로그인 함수 - 바로 인증됨
  const login = async (username: string, password: string): Promise<void> => {
    console.log('로그인 요청 처리됨 - 자동 인증됨');
    router.push('/');
  };

  // 로그아웃 함수 - 페이지를 홈으로 리디렉션
  const logout = (): void => {
    console.log('로그아웃 요청 처리됨 - 자동 인증 유지됨');
    router.push('/'); // 로그인 페이지 대신 홈으로 리디렉션
  };

  // 회원가입 함수 - 바로 인증됨
  const register = async (
    username: string, 
    email: string, 
    password: string, 
    firstName?: string, 
    lastName?: string
  ): Promise<void> => {
    console.log('회원가입 요청 처리됨 - 자동 인증됨');
    router.push('/');
  };

  // 인증 컨텍스트 값
  const authContextValue: AuthContextType = {
    isAuthenticated: true,  // 항상 인증됨
    isLoading: false,      // 로딩 없음
    user,                  // 기본 사용자 정보 사용
    error: null,           // 오류 없음
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