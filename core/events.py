"""
이벤트 시스템

모듈 간 느슨한 결합을 위한 이벤트 발행-구독 시스템을 제공합니다.
"""

import inspect
import threading
import queue
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .logging import get_logger

logger = get_logger("events")

class EventBus:
    """이벤트 버스 클래스"""
    
    def __init__(self):
        """이벤트 버스 초기화"""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._async_queue = queue.Queue()
        self._running = False
        self._async_thread = None
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        이벤트 구독
        
        Args:
            event_type: 이벤트 유형
            callback: 콜백 함수
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(f"이벤트 '{event_type}'에 콜백 등록됨: {callback.__name__}")
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        이벤트 구독 해제
        
        Args:
            event_type: 이벤트 유형
            callback: 콜백 함수
        """
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"이벤트 '{event_type}'에서 콜백 제거됨: {callback.__name__}")
    
    def publish(self, event_type: str, **kwargs) -> None:
        """
        이벤트 발행 (동기)
        
        Args:
            event_type: 이벤트 유형
            **kwargs: 이벤트 데이터
        """
        if event_type not in self._subscribers:
            logger.debug(f"이벤트 '{event_type}'에 구독자가 없음")
            return
        
        for callback in self._subscribers[event_type]:
            try:
                # 콜백 함수의 매개변수 확인
                sig = inspect.signature(callback)
                parameters = sig.parameters
                
                # 이벤트 타입만 필요한 경우
                if len(parameters) == 1 and list(parameters.keys())[0] == "event_type":
                    callback(event_type)
                # 모든 kwargs를 전달하는 경우
                else:
                    # 필요한 매개변수만 필터링
                    filtered_kwargs = {k: v for k, v in kwargs.items() if k in parameters}
                    callback(**filtered_kwargs)
            
            except Exception as e:
                logger.error(f"이벤트 '{event_type}' 처리 중 오류 발생: {str(e)}")
    
    def publish_async(self, event_type: str, **kwargs) -> None:
        """
        이벤트 비동기 발행 (별도 스레드에서 처리)
        
        Args:
            event_type: 이벤트 유형
            **kwargs: 이벤트 데이터
        """
        if not self._running:
            self.start_async_processing()
        
        self._async_queue.put((event_type, kwargs))
    
    def start_async_processing(self) -> None:
        """비동기 이벤트 처리 시작"""
        if self._running:
            return
        
        self._running = True
        self._async_thread = threading.Thread(target=self._process_async_events, daemon=True)
        self._async_thread.start()
        logger.debug("비동기 이벤트 처리 시작됨")
    
    def stop_async_processing(self) -> None:
        """비동기 이벤트 처리 중지"""
        self._running = False
        if self._async_thread:
            self._async_thread.join(timeout=2.0)
            self._async_thread = None
        logger.debug("비동기 이벤트 처리 중지됨")
    
    def _process_async_events(self) -> None:
        """비동기 이벤트 처리 루프"""
        while self._running:
            try:
                # 1초 타임아웃으로 큐에서 이벤트 가져오기
                try:
                    event_type, kwargs = self._async_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # 이벤트 발행 (동기 함수 호출)
                self.publish(event_type, **kwargs)
                
                # 작업 완료 표시
                self._async_queue.task_done()
            
            except Exception as e:
                logger.error(f"비동기 이벤트 처리 중 오류 발생: {str(e)}")
                time.sleep(0.1)  # 오류 발생 시 잠시 대기

# 싱글톤 이벤트 버스 인스턴스
_event_bus = None

def get_event_bus() -> EventBus:
    """
    전역 이벤트 버스 인스턴스 가져오기
    
    Returns:
        이벤트 버스 인스턴스
    """
    global _event_bus
    
    if _event_bus is None:
        _event_bus = EventBus()
    
    return _event_bus

# 편의 함수들
def subscribe(event_type: str, callback: Callable) -> None:
    """
    이벤트 구독 편의 함수
    
    Args:
        event_type: 이벤트 유형
        callback: 콜백 함수
    """
    get_event_bus().subscribe(event_type, callback)

def unsubscribe(event_type: str, callback: Callable) -> None:
    """
    이벤트 구독 해제 편의 함수
    
    Args:
        event_type: 이벤트 유형
        callback: 콜백 함수
    """
    get_event_bus().unsubscribe(event_type, callback)

def publish(event_type: str, **kwargs) -> None:
    """
    이벤트 발행 편의 함수 (동기)
    
    Args:
        event_type: 이벤트 유형
        **kwargs: 이벤트 데이터
    """
    get_event_bus().publish(event_type, **kwargs)

def publish_async(event_type: str, **kwargs) -> None:
    """
    이벤트 비동기 발행 편의 함수
    
    Args:
        event_type: 이벤트 유형
        **kwargs: 이벤트 데이터
    """
    get_event_bus().publish_async(event_type, **kwargs)
