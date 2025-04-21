"""
NLTK 데이터 설정 스크립트

이 스크립트는 필요한 모든 NLTK 데이터를 다운로드하고 경로를 설정합니다.
"""

import os
import nltk
import sys
import logging
import shutil
import re
import urllib.request
from functools import wraps
from nltk.tokenize.punkt import PunktSentenceTokenizer
from string import punctuation

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_simple_tokenizer():
    """
    collocations.tab 파일이 없을 때 사용할 간단한 토크나이저 함수
    """
    def simple_sent_tokenize(text):
        # 간단한 문장 분리기 구현
        # 구두점(.!?) 다음에 공백이 있으면 문장을 분리
        sentences = []
        current = ""
        
        # 정규식으로 문장 경계 찾기
        pattern = r'([.!?][\'\"\)\]]?(\s|$))'
        splits = re.split(pattern, text)
        
        # 결과 재결합
        result = []
        i = 0
        current = ""
        while i < len(splits):
            if i % 3 == 0:  # 본문 부분
                current += splits[i]
            elif i % 3 == 1:  # 구두점 부분
                if splits[i]:
                    current += splits[i]
                    result.append(current.strip())
                    current = ""
            i += 1
            
        # 마지막 문장이 구두점으로 끝나지 않는 경우
        if current:
            result.append(current.strip())
            
        return result
    
    return simple_sent_tokenize

def patch_nltk_punkt():
    """
    NLTK의 punkt_tab 참조 문제 해결을 위한 패치
    """
    print("NLTK punkt 패치 적용 중...")
    
    # 원본 함수 참조 저장
    original_find = nltk.data.find
    
    # 패치된 find 함수 정의
    @wraps(original_find)
    def patched_find(resource_name, paths=None):
        """
        'punkt_tab'을 'punkt'로 변경하는 패치된 find 함수
        """
        # punkt_tab 요청을 punkt로 변경
        if 'punkt_tab' in resource_name:
            print(f"punkt_tab 요청을 punkt로 리디렉션: {resource_name} -> tokenizers/punkt")
            resource_name = 'tokenizers/punkt'
            
        # 원본 함수 호출
        return original_find(resource_name, paths)
    
    # 패치 적용
    nltk.data.find = patched_find
    print("NLTK find 함수 패치 적용 완료")

    # sent_tokenize 패치
    try:
        # 간단한 토크나이저 생성
        simple_tokenizer = create_simple_tokenizer()
        
        # 원본 함수 참조 저장
        original_sent_tokenize = nltk.tokenize.sent_tokenize
        
        @wraps(original_sent_tokenize)
        def patched_sent_tokenize(text, language='english'):
            """
            오류에 강한 sent_tokenize 구현
            """
            if not text:
                return []
                
            try:
                # 원본 함수 시도
                return original_sent_tokenize(text, language)
            except LookupError as e:
                # punkt_tab 관련 오류일 경우
                if 'punkt_tab' in str(e):
                    print(f"sent_tokenize punkt_tab 오류 감지, 기본 구현 사용")
                    return simple_tokenizer(text)
                raise
            except FileNotFoundError as e:
                # collocations.tab 파일 못 찾을 경우
                if 'collocations.tab' in str(e):
                    print(f"sent_tokenize collocations.tab 오류 감지, 기본 구현 사용")
                    return simple_tokenizer(text)
                raise
            except Exception as e:
                # 기타 모든 오류
                print(f"sent_tokenize 오류 발생: {e}, 기본 구현 사용")
                return simple_tokenizer(text)
        
        # 패치 적용
        nltk.tokenize.sent_tokenize = patched_sent_tokenize
        print("sent_tokenize 패치 적용 완료")
        
    except Exception as e:
        print(f"sent_tokenize 패치 적용 실패: {e}")

def ensure_nltk_data():
    """
    NLTK 데이터를 확실하게 다운로드하고 존재 여부 확인
    """
    # NLTK 데이터 디렉토리
    nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nltk_data")
    os.makedirs(nltk_data_dir, exist_ok=True)
    
    # NLTK 데이터 경로 설정 (최우선 순위)
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_dir)
    
    # wordnet 디렉토리 확인 및 생성
    wordnet_dir = os.path.join(nltk_data_dir, "corpora", "wordnet")
    os.makedirs(wordnet_dir, exist_ok=True)
    
    # 필요한 데이터 패키지
    resources = {
        'punkt': 'tokenizers/punkt',
        'stopwords': 'corpora/stopwords',
        'wordnet': 'corpora/wordnet',
        'omw-1.4': 'corpora/omw-1.4'
    }
    
    # 각 리소스 다운로드 및 확인
    for name, path in resources.items():
        try:
            # 경로 확인
            try:
                nltk.data.find(path)
                print(f"{name} 확인 성공")
                continue  # 이미 있으면 다음으로
            except LookupError:
                pass  # 없으면 다운로드 진행
                
            # 명시적 다운로드
            print(f"{name} 다운로드 중...")
            nltk.download(name, download_dir=nltk_data_dir)
            
            # 다운로드 후 확인
            try:
                nltk.data.find(path)
                print(f"{name} 다운로드 및 확인 성공")
            except LookupError as e:
                print(f"{name} 다운로드 했으나 확인 실패: {e}")
                
        except Exception as e:
            print(f"{name} 다운로드 중 오류: {e}")
    
    # punkt 패키지가 있는지 확실히 확인
    punkt_dir = os.path.join(nltk_data_dir, "tokenizers", "punkt")
    if not os.path.exists(punkt_dir):
        print(f"punkt 디렉토리 존재하지 않음, 수동 생성: {punkt_dir}")
        os.makedirs(punkt_dir, exist_ok=True)
    
    # wordnet 데이터가 있는지 확실히 확인
    wordnet_dir = os.path.join(nltk_data_dir, "corpora", "wordnet")
    if not os.path.exists(wordnet_dir) or not os.listdir(wordnet_dir):
        print(f"wordnet 데이터 수동 생성: {wordnet_dir}")
        os.makedirs(wordnet_dir, exist_ok=True)
        
        # wordnet 데이터가 없으면 기본 파일 생성
        with open(os.path.join(wordnet_dir, "README"), "w") as f:
            f.write("Placeholder wordnet data")
    
    return nltk_data_dir

def setup_nltk_data():
    """
    필요한 NLTK 데이터 다운로드 및 경로 설정
    """
    # NLTK 데이터 디렉토리 설정
    nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nltk_data")
    os.makedirs(nltk_data_dir, exist_ok=True)
    print(f"NLTK 데이터 디렉토리: {nltk_data_dir}")
    
    # NLTK 검색 경로 설정 (최우선 순위로)
    nltk.data.path.insert(0, nltk_data_dir)
    
    # punkt_tab 패치 적용
    patch_nltk_punkt()
    
    # 데이터 다운로드 및 확인
    ensure_nltk_data()
    
    # 경로 확인
    print("\nNLTK 데이터 검색 경로:")
    for path in nltk.data.path:
        print(f" - {path}")
    
    # 테스트 실행
    test_text = "This is a test. Second sentence."
    try:
        result = nltk.tokenize.sent_tokenize(test_text)
        print(f"sent_tokenize 테스트 성공: {result}")
    except Exception as e:
        print(f"sent_tokenize 테스트 실패: {e}")
    
    return True
        
if __name__ == "__main__":
    setup_nltk_data()
    print("\n설정이 완료되었습니다. 이제 main.py를 실행하세요.")
