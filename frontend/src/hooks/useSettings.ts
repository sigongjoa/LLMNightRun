import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SettingsApi } from '../api';
import { Settings } from '../types';

// 설정 관련 커스텀 훅
export const useSettings = () => {
  return useQuery(
    ['settings'],
    () => SettingsApi.fetchSettings(),
    {
      staleTime: 300000, // 5분 동안 데이터 유지
    }
  );
};

export const useUpdateSettings = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (settings: Partial<Settings>) => SettingsApi.updateSettings(settings),
    {
      onSuccess: () => {
        // 성공 시 캐시 업데이트
        queryClient.invalidateQueries(['settings']);
      },
    }
  );
};
