"""
의존성 주입 컨테이너 모듈

애플리케이션 전체에서 사용되는 서비스 인스턴스를 관리하는 의존성 주입 컨테이너를 제공합니다.
이를 통해 서비스 간의 결합도를 낮추고 테스트 용이성을 높입니다.
"""

import inspect
from typing import Dict, Type, TypeVar, Generic, Any, Optional, get_type_hints, Callable, cast

T = TypeVar('T')


class DiContainer:
    """
    의존성 주입 컨테이너 클래스
    
    애플리케이션 내 서비스 인스턴스의 생성 및 관리를 담당합니다.
    싱글톤 패턴을 사용하여 서비스 인스턴스를 캐싱합니다.
    """
    
    def __init__(self):
        """컨테이너 초기화"""
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[..., Any]] = {}
    
    def register(self, interface_type: Type[T], implementation_type: Optional[Type[T]] = None) -> None:
        """
        인터페이스에 대한 구현 클래스를 등록합니다.
        
        Args:
            interface_type: 등록할 인터페이스 타입
            implementation_type: 구현 클래스 타입 (None인 경우 인터페이스 타입이 직접 사용됨)
        """
        if implementation_type is None:
            implementation_type = interface_type
        
        self._factories[interface_type] = lambda: self._create_instance(implementation_type)
    
    def register_instance(self, interface_type: Type[T], instance: T) -> None:
        """
        이미 생성된 인스턴스를 등록합니다.
        
        Args:
            interface_type: 등록할 인터페이스 타입
            instance: 인스턴스 객체
        """
        self._instances[interface_type] = instance
    
    def register_factory(self, interface_type: Type[T], factory: Callable[..., T]) -> None:
        """
        인스턴스를 생성하는 팩토리 함수를 등록합니다.
        
        Args:
            interface_type: 등록할 인터페이스 타입
            factory: 인스턴스를 생성하는 팩토리 함수
        """
        self._factories[interface_type] = factory
    
    def resolve(self, interface_type: Type[T]) -> T:
        """
        등록된 인터페이스에 대한 인스턴스를 해결합니다.
        
        Args:
            interface_type: 해결할 인터페이스 타입
            
        Returns:
            인터페이스에 대한 구현 인스턴스
            
        Raises:
            KeyError: 등록되지 않은 인터페이스인 경우
        """
        # 이미 생성된 인스턴스가 있는 경우
        if interface_type in self._instances:
            return cast(T, self._instances[interface_type])
        
        # 등록된 팩토리가 있는 경우
        if interface_type in self._factories:
            instance = self._factories[interface_type]()
            self._instances[interface_type] = instance  # 싱글톤으로 캐싱
            return cast(T, instance)
        
        # 등록되지 않은 인터페이스인 경우
        raise KeyError(f"인터페이스 {interface_type.__name__}가 등록되지 않았습니다.")
    
    def _create_instance(self, implementation_type: Type[T]) -> T:
        """
        구현 클래스의 인스턴스를 생성합니다.
        생성자의 매개변수는 자동으로 의존성을 해결합니다.
        
        Args:
            implementation_type: 구현 클래스 타입
            
        Returns:
            생성된 인스턴스
        """
        # 생성자 시그니처 분석
        constructor = implementation_type.__init__
        if constructor is object.__init__:
            # 기본 생성자인 경우
            return implementation_type()
        
        # 생성자 매개변수 타입 힌트 가져오기
        type_hints = get_type_hints(constructor)
        signature = inspect.signature(constructor)
        params = {}
        
        # self 매개변수 제외
        for name, param in list(signature.parameters.items())[1:]:
            # 타입 힌트가 있는 경우 의존성 해결
            if name in type_hints:
                param_type = type_hints[name]
                try:
                    params[name] = self.resolve(param_type)
                except KeyError:
                    # 기본값이 있는 경우 기본값 사용
                    if param.default is not inspect.Parameter.empty:
                        params[name] = param.default
                    else:
                        raise KeyError(f"매개변수 {name}: {param_type.__name__}의 의존성을 해결할 수 없습니다.")
            # 타입 힌트가 없지만 기본값이 있는 경우
            elif param.default is not inspect.Parameter.empty:
                params[name] = param.default
        
        # 인스턴스 생성
        return implementation_type(**params)


# 글로벌 DiContainer 인스턴스
container = DiContainer()
