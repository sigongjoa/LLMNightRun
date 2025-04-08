import { useEffect } from 'react';
import { useRouter } from 'next/router';

const MCPChatRedirect = () => {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/mcp-chat/new');
  }, [router]);
  
  return null;
};

export default MCPChatRedirect;