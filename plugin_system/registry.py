"""
플러그인 레지스트리

플러그인 등록 및 관리 기능을 제공합니다.
"""

import os
from typing import Dict, List, Any, Optional, Callable, Type

from core.logging import get_logger
from core.config import get_config
from core.events import publish

logger = get_logger("plugin_system")

class PluginRegistry:
    """플러그인 레지스트리 클래스"""
    
    def __init__(self):
        """플러그인 레지스트리 초기화"""
        self.plugins = {}  # 플러그인 저장소 {id: instance}
        self.hooks = {}    # 훅 저장소 {hook_name: [callbacks]}
    
    def register(self, plugin_id: str, plugin_instance: Any) -> bool:
        """
        플러그인 등록
        
        Args:
            plugin_id: 플러그인 ID
            plugin_instance: 플러그인 인스턴스
        
        Returns:
            성공 여부
        """
        if plugin_id in self.plugins:
            logger.warning(f"이미 등록된 플러그인 ID: {plugin_id}")
            return False
        
        self.plugins[plugin_id] = plugin_instance
        
        # 이벤트 발행
        publish("plugin.registered", plugin_id=plugin_id)
        
        logger.info(f"플러그인 등록됨: {plugin_id}")
        return True
    
    def unregister(self, plugin_id: str) -> bool:
        """
        플러그인 등록 해제
        
        Args:
            plugin_id: 플러그인 ID
        
        Returns:
            성공 여부
        """
        if plugin_id not in self.plugins:
            logger.warning(f"등록되지 않은 플러그인 ID: {plugin_id}")
            return False
        
        # 플러그인 인스턴스 가져오기
        plugin = self.plugins[plugin_id]
        
        # 등록된 모든 훅에서 이 플러그인의 콜백 제거
        for hook_name, callbacks in self.hooks.items():
            # 필터링: 이 플러그인의 메서드가 아닌 콜백만 유지
            self.hooks[hook_name] = [
                cb for cb in callbacks
                if not hasattr(cb, '__self__') or cb.__self__ is not plugin
            ]
        
        # 플러그인 등록 해제
        del self.plugins[plugin_id]
        
        # 이벤트 발행
        publish("plugin.unregistered", plugin_id=plugin_id)
        
        logger.info(f"플러그인 등록 해제됨: {plugin_id}")
        return True
    
    def get_plugin(self, plugin_id: str) -> Optional[Any]:
        """
        ID로 플러그인 가져오기
        
        Args:
            plugin_id: 플러그인 ID
        
        Returns:
            플러그인 인스턴스 또는 None (없는 경우)
        """
        return self.plugins.get(plugin_id)
    
    def get_plugins(self) -> Dict[str, Any]:
        """
        모든 플러그인 가져오기
        
        Returns:
            플러그인 딕셔너리 {id: instance}
        """
        return self.plugins.copy()
    
    def register_hook(self, hook_name: str, callback: Callable) -> bool:
        """
        훅에 콜백 등록
        
        Args:
            hook_name: 훅 이름
            callback: 콜백 함수
        
        Returns:
            성공 여부
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        # 이미 등록된 콜백인지 확인
        if callback in self.hooks[hook_name]:
            logger.warning(f"이미 등록된 콜백: {hook_name}")
            return False
        
        self.hooks[hook_name].append(callback)
        logger.debug(f"훅 등록됨: {hook_name}")
        return True
    
    def unregister_hook(self, hook_name: str, callback: Callable) -> bool:
        """
        훅에서 콜백 등록 해제
        
        Args:
            hook_name: 훅 이름
            callback: 콜백 함수
        
        Returns:
            성공 여부
        """
        if hook_name not in self.hooks or callback not in self.hooks[hook_name]:
            logger.warning(f"등록되지 않은 훅 또는 콜백: {hook_name}")
            return False
        
        self.hooks[hook_name].remove(callback)
        logger.debug(f"훅 등록 해제됨: {hook_name}")
        return True
    
    def call_hook(self, hook_name: str, **kwargs) -> List[Any]:
        """
        훅 호출
        
        Args:
            hook_name: 훅 이름
            **kwargs: 콜백에 전달할 매개변수
        
        Returns:
            콜백 반환 값 목록
        """
        if hook_name not in self.hooks:
            logger.debug(f"등록된 콜백이 없는 훅: {hook_name}")
            return []
        
        results = []
        
        for callback in self.hooks[hook_name]:
            try:
                result = callback(**kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"훅 '{hook_name}' 호출 중 오류 발생: {str(e)}")
                results.append(None)
        
        return results
    
    def clear(self) -> None:
        """모든 플러그인 및 훅 등록 해제"""
        self.plugins = {}
        self.hooks = {}
        logger.info("플러그인 레지스트리 초기화됨")

# 싱글톤 레지스트리 인스턴스
_registry = None

def get_registry() -> PluginRegistry:
    """
    전역 플러그인 레지스트리 인스턴스 가져오기
    
    Returns:
        플러그인 레지스트리 인스턴스
    """
    global _registry
    
    if _registry is None:
        _registry = PluginRegistry()
    
    return _registry
