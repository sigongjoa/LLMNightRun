"""
플러그인 로더

플러그인 검색 및 로드 기능을 제공합니다.
"""

import os
import sys
import importlib
import importlib.util
import inspect
from typing import Dict, List, Any, Optional, Tuple, Type

from .registry import get_registry
from core.logging import get_logger
from core.config import get_config
from core.events import publish

logger = get_logger("plugin_system")

def load_plugin(plugin_path: str) -> Optional[Tuple[str, Any]]:
    """
    플러그인 로드
    
    Args:
        plugin_path: 플러그인 모듈 파일 경로
    
    Returns:
        (플러그인 ID, 플러그인 인스턴스) 또는 None (로드 실패 시)
    """
    try:
        # 절대 경로 변환
        plugin_path = os.path.abspath(plugin_path)
        
        if not os.path.exists(plugin_path):
            logger.error(f"플러그인 파일을 찾을 수 없음: {plugin_path}")
            return None
        
        # 파일명에서 모듈 이름 추출
        module_name = os.path.splitext(os.path.basename(plugin_path))[0]
        
        # 모듈 로드
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            logger.error(f"플러그인 스펙 로드 실패: {plugin_path}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 플러그인 클래스 찾기
        plugin_class = None
        for name, obj in inspect.getmembers(module):
            # BasePlugin 클래스가 정의된 후에는 아래 조건을 수정해야 함
            if inspect.isclass(obj) and hasattr(obj, 'plugin_id') and hasattr(obj, 'plugin_name'):
                plugin_class = obj
                break
        
        if not plugin_class:
            logger.error(f"플러그인 클래스를 찾을 수 없음: {plugin_path}")
            return None
        
        # 플러그인 인스턴스 생성
        plugin_instance = plugin_class()
        plugin_id = plugin_instance.plugin_id
        
        # 플러그인 등록
        registry = get_registry()
        if not registry.register(plugin_id, plugin_instance):
            logger.error(f"플러그인 등록 실패: {plugin_id}")
            return None
        
        # 이벤트 발행
        publish("plugin.loaded", plugin_id=plugin_id, plugin_path=plugin_path)
        
        logger.info(f"플러그인 로드됨: {plugin_id} ({plugin_path})")
        return (plugin_id, plugin_instance)
    
    except Exception as e:
        logger.error(f"플러그인 로드 중 오류 발생: {str(e)}")
        return None

def load_plugins(plugins_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    디렉토리의 모든 플러그인 로드
    
    Args:
        plugins_dir: 플러그인 디렉토리 (기본값: 설정에서 가져옴)
    
    Returns:
        로드된 플러그인 딕셔너리 {id: instance}
    """
    config = get_config()
    
    # 플러그인 디렉토리 설정
    plugins_dir = plugins_dir or config.get("plugin_system", "plugins_dir")
    
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir, exist_ok=True)
        logger.info(f"플러그인 디렉토리 생성됨: {plugins_dir}")
    
    # 자동 검색 확인
    auto_discover = config.get("plugin_system", "auto_discover", True)
    
    # 결과 저장 딕셔너리
    loaded_plugins = {}
    
    try:
        if auto_discover:
            # 모든 Python 파일 검색
            for filename in os.listdir(plugins_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    plugin_path = os.path.join(plugins_dir, filename)
                    
                    result = load_plugin(plugin_path)
                    if result:
                        plugin_id, plugin_instance = result
                        loaded_plugins[plugin_id] = plugin_instance
        else:
            # 설정에 지정된 플러그인만 로드
            enabled_plugins = config.get("plugin_system", "enabled_plugins", [])
            
            for plugin_id in enabled_plugins:
                # 플러그인 파일 경로 추정
                plugin_path = os.path.join(plugins_dir, f"{plugin_id}.py")
                
                if not os.path.exists(plugin_path):
                    logger.warning(f"설정된 플러그인 파일을 찾을 수 없음: {plugin_path}")
                    continue
                
                result = load_plugin(plugin_path)
                if result:
                    pid, plugin_instance = result
                    loaded_plugins[pid] = plugin_instance
        
        logger.info(f"{len(loaded_plugins)}개 플러그인 로드됨")
    
    except Exception as e:
        logger.error(f"플러그인 로드 중 오류 발생: {str(e)}")
    
    return loaded_plugins

def reload_plugin(plugin_id: str) -> bool:
    """
    플러그인 리로드
    
    Args:
        plugin_id: 플러그인 ID
    
    Returns:
        성공 여부
    """
    registry = get_registry()
    plugin = registry.get_plugin(plugin_id)
    
    if not plugin:
        logger.warning(f"리로드할 플러그인을 찾을 수 없음: {plugin_id}")
        return False
    
    # 플러그인 모듈 경로 찾기
    module = sys.modules.get(plugin.__module__)
    if not module or not hasattr(module, "__file__"):
        logger.error(f"플러그인 모듈 파일을 찾을 수 없음: {plugin_id}")
        return False
    
    # 플러그인 등록 해제
    if not registry.unregister(plugin_id):
        logger.error(f"플러그인 등록 해제 실패: {plugin_id}")
        return False
    
    # 플러그인 다시 로드
    plugin_path = module.__file__
    result = load_plugin(plugin_path)
    
    if not result:
        logger.error(f"플러그인 리로드 실패: {plugin_id}")
        return False
    
    # 이벤트 발행
    publish("plugin.reloaded", plugin_id=plugin_id)
    
    logger.info(f"플러그인 리로드됨: {plugin_id}")
    return True
