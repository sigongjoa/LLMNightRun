import axiosInstance from '../axiosInstance';
import { Settings } from '../../types';

/**
 * 설정 관련 API 함수
 */
export const SettingsApi = {
  /**
   * 설정 조회
   */
  fetchSettings: async (): Promise<Settings> => {
    const response = await axiosInstance.get<Settings>('/settings');
    return response.data;
  },

  /**
   * 설정 업데이트
   */
  updateSettings: async (settings: Partial<Settings>): Promise<{
    success: boolean;
    message: string;
    updated_at: string;
  }> => {
    const response = await axiosInstance.post<{
      success: boolean;
      message: string;
      updated_at: string;
    }>('/settings', settings);
    return response.data;
  }
};

export default SettingsApi;
