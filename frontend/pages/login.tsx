import { useEffect } from 'react';
import { useRouter } from 'next/router';

const LoginPage = () => {
  const router = useRouter();

  // 자동으로 홈으로 리디렉션
  useEffect(() => {
    router.push('/');
  }, [router]);

  return null; // 빈 화면 표시 (리디렉션 중)
};

export default LoginPage;