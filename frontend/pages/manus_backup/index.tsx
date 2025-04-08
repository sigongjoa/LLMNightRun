import { useEffect } from 'react';
import { useRouter } from 'next/router';

const ManusRedirectPage = () => {
  const router = useRouter();

  useEffect(() => {
    // Manus 페이지에서 MCP 페이지로 리다이렉트
    router.replace('/mcp-tools');
  }, [router]);

  return null; // 로딩 화면이나 리다이렉트 메시지를 추가할 수 있습니다
};

export default ManusRedirectPage;