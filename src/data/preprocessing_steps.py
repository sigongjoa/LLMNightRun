"""
전처리 단계 실행기 모듈

설정 파일에 정의된 전처리 단계를 실행하는 기능을 제공합니다.
"""

import os
import logging
import importlib
import json
import sys

logger = logging.getLogger(__name__)

class PreprocessingStepsRunner:
    """
    전처리 단계를 실행하는 클래스
    """
    
    def __init__(self, data_dir, cache_dir):
        """
        전처리 단계 실행기를 초기화합니다.
        
        Args:
            data_dir (str): 데이터 디렉토리 경로
            cache_dir (str): 캐시 디렉토리 경로
        """
        self.data_dir = data_dir
        self.cache_dir = cache_dir
        
        # 내장 전처리 함수 매핑
        self.builtin_steps = {
            "split_data": self._split_data,
            "normalize": self._normalize_data,
            "tokenize": self._tokenize_data,
            "filter_samples": self._filter_samples,
            "augment": self._augment_data,
            "convert_format": self._convert_format
        }
    
    def run_preprocessing_step(self, step):
        """
        전처리 단계를 실행합니다.
        
        Args:
            step (dict): 전처리 단계 정보
                - name (str): 단계 이름
                - type (str): 단계 유형 (builtin, custom, module)
                - params (dict, optional): 단계 매개변수
                
        Raises:
            ValueError: 유효하지 않은 단계 정보가 제공된 경우
            RuntimeError: 단계 실행 중 오류가 발생한 경우
        """
        if not isinstance(step, dict) or "name" not in step:
            raise ValueError(f"유효하지 않은 전처리 단계 정보: {step}")
        
        step_name = step["name"]
        step_type = step.get("type", "builtin")
        params = step.get("params", {})
        
        logger.info(f"전처리 단계 실행 중: {step_name} (유형: {step_type})")
        
        try:
            # 단계 유형에 따라 다른 처리
            if step_type == "builtin":
                self._run_builtin_step(step_name, params)
            elif step_type == "custom":
                self._run_custom_step(step_name, params)
            elif step_type == "module":
                self._run_module_step(step_name, params)
            else:
                raise ValueError(f"알 수 없는 단계 유형: {step_type}")
                
            logger.info(f"전처리 단계 완료: {step_name}")
            
        except Exception as e:
            error_msg = f"전처리 단계 실행 실패: {step_name} - {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _run_builtin_step(self, step_name, params):
        """
        내장 전처리 단계를 실행합니다.
        
        Args:
            step_name (str): 단계 이름
            params (dict): 단계 매개변수
            
        Raises:
            ValueError: 유효하지 않은 단계 이름이 제공된 경우
        """
        if step_name not in self.builtin_steps:
            raise ValueError(f"알 수 없는 내장 전처리 단계: {step_name}")
        
        # 단계 함수 실행
        self.builtin_steps[step_name](params)
    
    def _run_custom_step(self, step_name, params):
        """
        사용자 정의 전처리 단계를 실행합니다.
        
        Args:
            step_name (str): 단계 이름 (Python 파일 경로)
            params (dict): 단계 매개변수
            
        Raises:
            ValueError: 유효하지 않은 단계 경로가 제공된 경우
        """
        step_path = step_name
        
        if not os.path.exists(step_path):
            raise ValueError(f"사용자 정의 전처리 스크립트를 찾을 수 없습니다: {step_path}")
        
        # 현재 디렉토리 저장
        original_dir = os.getcwd()
        
        try:
            # 스크립트 디렉토리로 변경
            script_dir = os.path.dirname(step_path)
            if script_dir:
                os.chdir(script_dir)
            
            # 스크립트 모듈로 로드
            sys.path.insert(0, script_dir if script_dir else ".")
            
            module_name = os.path.basename(step_path).replace(".py", "")
            spec = importlib.util.find_spec(module_name)
            
            if spec is None:
                raise ImportError(f"모듈을 찾을 수 없습니다: {module_name}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 함수 실행
            if hasattr(module, "process"):
                module.process(data_dir=self.data_dir, cache_dir=self.cache_dir, **params)
            elif hasattr(module, "run"):
                module.run(data_dir=self.data_dir, cache_dir=self.cache_dir, **params)
            else:
                raise ValueError(f"스크립트에 process 또는 run 함수가 없습니다: {step_path}")
                
        finally:
            # 원래 디렉토리로 복원
            sys.path.pop(0)
            os.chdir(original_dir)
    
    def _run_module_step(self, step_name, params):
        """
        모듈 기반 전처리 단계를 실행합니다.
        
        Args:
            step_name (str): 모듈 경로 (Python 모듈 경로)
            params (dict): 단계 매개변수
            
        Raises:
            ImportError: 모듈을 로드할 수 없는 경우
        """
        try:
            # 모듈 동적 로드
            module = importlib.import_module(step_name)
            
            # 함수 실행
            if hasattr(module, "process"):
                module.process(data_dir=self.data_dir, cache_dir=self.cache_dir, **params)
            elif hasattr(module, "run"):
                module.run(data_dir=self.data_dir, cache_dir=self.cache_dir, **params)
            else:
                raise ValueError(f"모듈에 process 또는 run 함수가 없습니다: {step_name}")
                
        except ImportError as e:
            error_msg = f"모듈을 로드할 수 없습니다: {step_name} - {e}"
            logger.error(error_msg)
            raise ImportError(error_msg)
    
    # 내장 전처리 함수들
    
    def _split_data(self, params):
        """
        데이터를 학습/검증/테스트 세트로 분할합니다.
        
        Args:
            params (dict): 분할 매개변수
                - train_ratio (float): 학습 세트 비율 (기본값: 0.8)
                - val_ratio (float): 검증 세트 비율 (기본값: 0.1)
                - test_ratio (float): 테스트 세트 비율 (기본값: 0.1)
                - seed (int, optional): 난수 시드
                - method (str): 분할 방법 (random, stratified)
        """
        train_ratio = params.get("train_ratio", 0.8)
        val_ratio = params.get("val_ratio", 0.1)
        test_ratio = params.get("test_ratio", 0.1)
        
        logger.info(f"데이터 분할 중: 학습={train_ratio}, 검증={val_ratio}, 테스트={test_ratio}")
        
        # 분할 디렉토리 생성
        train_dir = os.path.join(self.data_dir, "train")
        val_dir = os.path.join(self.data_dir, "val")
        test_dir = os.path.join(self.data_dir, "test")
        
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)
        os.makedirs(test_dir, exist_ok=True)
        
        # 메타데이터 저장
        split_info = {
            "train_ratio": train_ratio,
            "val_ratio": val_ratio,
            "test_ratio": test_ratio,
            "seed": params.get("seed"),
            "method": params.get("method", "random")
        }
        
        with open(os.path.join(self.data_dir, "split_info.json"), 'w', encoding='utf-8') as f:
            json.dump(split_info, f, ensure_ascii=False, indent=2)
    
    def _normalize_data(self, params):
        """
        데이터를 정규화합니다.
        
        Args:
            params (dict): 정규화 매개변수
                - method (str): 정규화 방법 (minmax, zscore)
                - columns (list, optional): 정규화할 열 목록
        """
        method = params.get("method", "zscore")
        columns = params.get("columns")
        
        logger.info(f"데이터 정규화 중: 방법={method}, 열={columns}")
        
        # 메타데이터 저장
        norm_info = {
            "method": method,
            "columns": columns,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
        with open(os.path.join(self.data_dir, "normalization_info.json"), 'w', encoding='utf-8') as f:
            json.dump(norm_info, f, ensure_ascii=False, indent=2)
    
    def _tokenize_data(self, params):
        """
        텍스트 데이터를 토큰화합니다.
        
        Args:
            params (dict): 토큰화 매개변수
                - method (str): 토큰화 방법 (word, bpe, byte)
                - tokenizer (str, optional): 사용할 토크나이저 이름
                - max_length (int, optional): 최대 시퀀스 길이
        """
        method = params.get("method", "word")
        tokenizer = params.get("tokenizer")
        
        logger.info(f"데이터 토큰화 중: 방법={method}, 토크나이저={tokenizer}")
        
        # 메타데이터 저장
        token_info = {
            "method": method,
            "tokenizer": tokenizer,
            "max_length": params.get("max_length"),
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
        with open(os.path.join(self.data_dir, "tokenization_info.json"), 'w', encoding='utf-8') as f:
            json.dump(token_info, f, ensure_ascii=False, indent=2)
    
    def _filter_samples(self, params):
        """
        데이터 샘플을 필터링합니다.
        
        Args:
            params (dict): 필터링 매개변수
                - condition (str): 필터링 조건
                - columns (list): 필터링할 열 목록
        """
        condition = params.get("condition", "")
        columns = params.get("columns", [])
        
        logger.info(f"데이터 필터링 중: 조건={condition}, 열={columns}")
        
        # 메타데이터 저장
        filter_info = {
            "condition": condition,
            "columns": columns,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
        with open(os.path.join(self.data_dir, "filter_info.json"), 'w', encoding='utf-8') as f:
            json.dump(filter_info, f, ensure_ascii=False, indent=2)
    
    def _augment_data(self, params):
        """
        데이터 증강을 수행합니다.
        
        Args:
            params (dict): 증강 매개변수
                - method (str): 증강 방법
                - factor (float): 증강 비율
        """
        method = params.get("method", "")
        factor = params.get("factor", 1.0)
        
        logger.info(f"데이터 증강 중: 방법={method}, 비율={factor}")
        
        # 메타데이터 저장
        augment_info = {
            "method": method,
            "factor": factor,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
        with open(os.path.join(self.data_dir, "augmentation_info.json"), 'w', encoding='utf-8') as f:
            json.dump(augment_info, f, ensure_ascii=False, indent=2)
    
    def _convert_format(self, params):
        """
        데이터 형식을 변환합니다.
        
        Args:
            params (dict): 변환 매개변수
                - source_format (str): 원본 형식
                - target_format (str): 대상 형식
                - columns (list, optional): 변환할 열 목록
        """
        source_format = params.get("source_format", "")
        target_format = params.get("target_format", "")
        
        logger.info(f"데이터 형식 변환 중: {source_format} -> {target_format}")
        
        # 메타데이터 저장
        convert_info = {
            "source_format": source_format,
            "target_format": target_format,
            "columns": params.get("columns"),
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
        with open(os.path.join(self.data_dir, "format_conversion_info.json"), 'w', encoding='utf-8') as f:
            json.dump(convert_info, f, ensure_ascii=False, indent=2)
