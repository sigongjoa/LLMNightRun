"""
NLTK Punkt 패치 파일

NLTK의 punkt_tab 대신 punkt를 사용하도록 monkey patch 적용
"""

import nltk
import os
import sys
import logging
from functools import wraps

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NLTK 데이터 경로 및 파일 확인
nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nltk_data")

def patch_nltk_punkt():
    """NLTK의 punkt_tab 참조를 punkt로 리디렉션"""
    
    # 원본 find 함수 저장
    original_find = nltk.data.find
    
    # 패치된 find 함수 정의
    @wraps(original_find)
    def patched_find(resource_name, paths=None):
        """
        'punkt_tab'을 'punkt'로 변경하는 패치된 find 함수
        """
        # punkt_tab 요청을 punkt로 변경
        if resource_name == 'tokenizers/punkt_tab' or resource_name == 'tokenizers/punkt_tab/english/':
            logger.info(f"punkt_tab 요청을 punkt로 리디렉션")
            resource_name = 'tokenizers/punkt'
            
        # 원본 함수 호출
        return original_find(resource_name, paths)
    
    # 패치 적용
    nltk.data.find = patched_find
    logger.info("NLTK punkt_tab 패치 적용 완료")

def patch_punkt_tokenizer():
    """PunktTokenizer 관련 패치 적용"""
    try:
        # _params_default 클래스 변수 확인
        from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
        
        # 원본 메서드 저장
        original_load = PunktSentenceTokenizer._load_params
        
        @wraps(original_load)
        def patched_load(self, filename):
            """
            punkt_tab 요청 시 punkt로 변경
            """
            if 'punkt_tab' in filename:
                filename = filename.replace('punkt_tab', 'punkt')
                logger.info(f"PunktSentenceTokenizer에서 punkt_tab을 punkt로 변경: {filename}")
            return original_load(self, filename)
        
        # 패치 적용
        PunktSentenceTokenizer._load_params = patched_load
        logger.info("PunktSentenceTokenizer 패치 적용 완료")
        
    except Exception as e:
        logger.error(f"PunktTokenizer 패치 적용 실패: {e}")

def apply_all_patches():
    """모든 패치 적용"""
    patch_nltk_punkt()
    patch_punkt_tokenizer()
    
    # 패치 적용 테스트
    try:
        sent_tokenize = nltk.tokenize.sent_tokenize
        test_text = "This is a test. Second sentence."
        result = sent_tokenize(test_text)
        logger.info(f"패치 테스트 결과: {result}")
        return True
    except Exception as e:
        logger.error(f"패치 테스트 실패: {e}")
        return False
        
if __name__ == "__main__":
    apply_all_patches()
    print("NLTK punto_tab 패치 적용 완료")
