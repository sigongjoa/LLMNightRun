import React, { createContext, useContext, useState, ReactNode } from 'react';
import { AlertColor } from '@mui/material';
import { Notification } from '../components/ui';

// 컨텍스트 타입 정의
interface NotificationContextType {
  showNotification: (message: string, severity?: AlertColor) => void;
  hideNotification: () => void;
}

// 기본값으로 빈 함수를 가진 컨텍스트 생성
const NotificationContext = createContext<NotificationContextType>({
  showNotification: () => {},
  hideNotification: () => {},
});

// 컨텍스트 Hook
export const useNotification = () => useContext(NotificationContext);

// 컨텍스트 제공자 컴포넌트
interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [severity, setSeverity] = useState<AlertColor>('info');

  // 알림 표시
  const showNotification = (msg: string, sev: AlertColor = 'info') => {
    setMessage(msg);
    setSeverity(sev);
    setOpen(true);
  };

  // 알림 숨기기
  const hideNotification = () => {
    setOpen(false);
  };

  return (
    <NotificationContext.Provider value={{ showNotification, hideNotification }}>
      {children}
      <Notification
        open={open}
        message={message}
        severity={severity}
        onClose={hideNotification}
      />
    </NotificationContext.Provider>
  );
};

export default NotificationContext;
