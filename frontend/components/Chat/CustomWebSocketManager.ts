/**
 * 웹소켓 연결 및 상태 관리를 위한 클래스
 */
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private pingInterval: NodeJS.Timeout | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isReconnecting = false;
  
  // 이벤트 핸들러
  private onOpenCallback: (() => void) | null = null;
  private onMessageCallback: ((data: any) => void) | null = null;
  private onCloseCallback: ((event: CloseEvent) => void) | null = null;
  private onErrorCallback: ((event: Event) => void) | null = null;
  private onStatusChangeCallback: ((status: { connected: boolean, message: string }) => void) | null = null;
  
  constructor(url: string) {
    this.url = url;
  }
  
  /**
   * 웹소켓 연결 초기화
   */
  public connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket이 이미 연결되어 있습니다.');
      return;
    }
    
    // 기존 시간 초과 타이머 정리
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    console.log(`WebSocket 연결 시도: ${this.url}`);
    
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket 연결 성공');
        this.reconnectAttempts = 0;
        this.isReconnecting = false;
        
        // ping 메시지 설정
        this.startPingInterval();
        
        // 상태 변경 알림
        if (this.onStatusChangeCallback) {
          this.onStatusChangeCallback({ 
            connected: true, 
            message: '서버에 연결되었습니다'
          });
        }
        
        // 사용자 정의 이벤트 핸들러 호출
        if (this.onOpenCallback) {
          this.onOpenCallback();
        }
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // pong 메시지는 로깅하지 않음
          if (data.type !== 'pong') {
            console.log('WebSocket 메시지 수신:', data.type);
          }
          
          // 사용자 정의 메시지 핸들러 호출
          if (this.onMessageCallback) {
            this.onMessageCallback(data);
          }
        } catch (e) {
          console.error('WebSocket 메시지 파싱 오류:', e);
        }
      };
      
      this.ws.onclose = (event) => {
        // ping 간격 정리
        this.stopPingInterval();
        
        console.log(`WebSocket 연결 종료: 코드=${event.code}, 이유=${event.reason || '알 수 없음'}`);
        
        // 상태 변경 알림
        if (this.onStatusChangeCallback) {
          this.onStatusChangeCallback({ 
            connected: false, 
            message: '연결 끊김, 재시도 중...'
          });
        }
        
        // 사용자 정의 이벤트 핸들러 호출
        if (this.onCloseCallback) {
          this.onCloseCallback(event);
        }
        
        // 정상적으로 종료된 경우가 아니라면 재연결 시도
        if (!this.isReconnecting && event.code !== 1000 && event.code !== 1001) {
          this.scheduleReconnect();
        }
      };
      
      this.ws.onerror = (event) => {
        console.error('WebSocket 오류:', event);
        
        // 상태 변경 알림
        if (this.onStatusChangeCallback) {
          this.onStatusChangeCallback({ 
            connected: false, 
            message: '연결 오류 발생'
          });
        }
        
        // 사용자 정의 이벤트 핸들러 호출
        if (this.onErrorCallback) {
          this.onErrorCallback(event);
        }
      };
      
    } catch (e) {
      console.error('WebSocket 생성 중 오류:', e);
      
      // 연결 실패 시 재연결 일정 잡기
      this.scheduleReconnect();
    }
  }
  
  /**
   * 웹소켓 연결 종료
   */
  public disconnect(): void {
    this.stopPingInterval();
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      // 정상 종료 코드로 연결 종료
      this.ws.close(1000, '사용자 요청으로 종료');
      this.ws = null;
    }
  }
  
  /**
   * 메시지 전송
   */
  public send(data: any): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket이 연결되지 않았습니다. 메시지를 보낼 수 없습니다.');
      return false;
    }
    
    try {
      // 메시지 형식 사용 옵션 추가
      if (typeof data === 'object' && data.type === 'chat_request') {
        if (!data.options) data.options = {};
        data.options.use_message_format = true;
      }
      
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.ws.send(message);
      return true;
    } catch (e) {
      console.error('메시지 전송 중 오류:', e);
      return false;
    }
  }
  
  /**
   * 재연결 예약
   */
  private scheduleReconnect(): void {
    if (this.isReconnecting) {
      return;
    }
    
    this.isReconnecting = true;
    this.reconnectAttempts++;
    
    // 지수적 백오프로 재연결 간격 계산
    const delay = Math.min(30000, 3000 * Math.pow(1.5, this.reconnectAttempts - 1));
    
    console.log(`WebSocket 재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts} - ${delay}ms 후...`);
    
    // 최대 재시도 횟수 체크
    if (this.reconnectAttempts <= this.maxReconnectAttempts) {
      this.reconnectTimeout = setTimeout(() => {
        if (document.visibilityState === 'visible') {
          this.connect();
        } else {
          // 페이지가 보이지 않는 경우 연결 시도 연기
          console.log('페이지가 보이지 않아 연결 연기');
          this.isReconnecting = false;
        }
      }, delay);
    } else {
      console.log(`최대 재연결 시도 횟수(${this.maxReconnectAttempts})를 초과했습니다. 재연결을 중지합니다.`);
      this.isReconnecting = false;
      
      // 상태 변경 알림
      if (this.onStatusChangeCallback) {
        this.onStatusChangeCallback({ 
          connected: false, 
          message: '연결 실패: 최대 재시도 횟수 초과'
        });
      }
    }
  }
  
  /**
   * 핑 간격 시작
   */
  private startPingInterval(): void {
    this.stopPingInterval();
    
    // 30초마다 ping 메시지 전송
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      } else {
        this.stopPingInterval();
      }
    }, 30000);
  }
  
  /**
   * 핑 간격 중지
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
  
  /**
   * 이벤트 핸들러 설정
   */
  public onOpen(callback: () => void): void {
    this.onOpenCallback = callback;
  }
  
  public onMessage(callback: (data: any) => void): void {
    this.onMessageCallback = callback;
  }
  
  public onClose(callback: (event: CloseEvent) => void): void {
    this.onCloseCallback = callback;
  }
  
  public onError(callback: (event: Event) => void): void {
    this.onErrorCallback = callback;
  }
  
  public onStatusChange(callback: (status: { connected: boolean, message: string }) => void): void {
    this.onStatusChangeCallback = callback;
  }
  
  /**
   * 연결 상태 확인
   */
  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
  
  /**
   * 연결 URL 가져오기
   */
  public getUrl(): string {
    return this.url;
  }
  
  /**
   * 연결 URL 변경
   */
  public setUrl(url: string): void {
    if (this.url !== url) {
      this.url = url;
      
      // URL이 변경된 경우 재연결
      if (this.isConnected()) {
        this.disconnect();
        this.connect();
      }
    }
  }
}