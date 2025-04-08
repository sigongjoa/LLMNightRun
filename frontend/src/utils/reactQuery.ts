import { QueryClient } from '@tanstack/react-query';

// React Query 클라이언트 설정
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // 윈도우 포커스 시 자동 리페치 비활성화
      retry: 1, // 실패 시 최대 1번 재시도
      staleTime: 300000, // 5분 동안 데이터 유지
    },
  },
});
