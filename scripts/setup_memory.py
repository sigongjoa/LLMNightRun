#!/usr/bin/env python
"""
LLM 메모리 시스템 설정 스크립트

이 스크립트는 LLM Memory와 Vector DB 시스템을 초기화하고,
필요한 디렉토리를 생성하며, 임베딩 모델을 다운로드합니다.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("memory-setup")

# 프로젝트 루트 디렉토리 설정
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

def setup_environment():
    """환경 설정 및 필요한 디렉토리 생성"""
    try:
        # 데이터 디렉토리 생성
        data_dir = root_dir / "backend" / "data"
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"데이터 디렉토리 생성 완료: {data_dir}")
        
        # 벡터 스토어 디렉토리 생성
        vector_store_dir = data_dir / "faiss_store"
        os.makedirs(vector_store_dir, exist_ok=True)
        logger.info(f"FAISS 벡터 스토어 디렉토리 생성 완료: {vector_store_dir}")
        
        return True
    except Exception as e:
        logger.error(f"환경 설정 중 오류 발생: {str(e)}")
        return False

def download_embedding_model():
    """임베딩 모델 다운로드"""
    try:
        logger.info("임베딩 모델 다운로드 시작...")
        
        # sentence-transformers 모델 다운로드 시작
        # 이 과정은 모델을 로드하는 것만으로 자동 다운로드됨
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info(f"임베딩 모델 다운로드 완료: {model.get_sentence_embedding_dimension()}차원")
        
        return True
    except Exception as e:
        logger.error(f"임베딩 모델 다운로드 중 오류 발생: {str(e)}")
        return False

def test_vector_store():
    """벡터 스토어 기능 테스트"""
    try:
        logger.info("벡터 스토어 테스트 시작...")
        
        # 백엔드 메모리 모듈 가져오기
        from backend.memory.vector_store import get_vector_store
        
        # 벡터 스토어 초기화
        vector_store = get_vector_store()
        
        # 간단한 테스트 데이터 추가
        test_texts = ["이것은 테스트 메모리입니다.", "벡터 DB가 정상적으로 작동하는지 확인합니다."]
        test_metadata = [{"type": "test", "timestamp": 1234567890} for _ in test_texts]
        
        # 벡터 스토어에 추가
        ids = vector_store.add(test_texts, metadatas=test_metadata)
        logger.info(f"테스트 데이터 추가 완료: {len(ids)} 항목")
        
        # 검색 테스트
        results = vector_store.search("테스트", top_k=1)
        logger.info(f"검색 테스트 완료: {len(results)} 결과")
        
        # 테스트 데이터 삭제
        vector_store.delete(ids)
        logger.info("테스트 데이터 삭제 완료")
        
        return True
    except Exception as e:
        logger.error(f"벡터 스토어 테스트 중 오류 발생: {str(e)}")
        return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="LLM 메모리 시스템 설정")
    parser.add_argument('--skip-model', action='store_true', help='임베딩 모델 다운로드 건너뛰기')
    parser.add_argument('--skip-test', action='store_true', help='벡터 DB 테스트 건너뛰기')
    args = parser.parse_args()
    
    logger.info("LLM 메모리 시스템 설정 시작...")
    
    # 환경 설정
    if not setup_environment():
        logger.error("환경 설정 실패")
        return 1
        
    # 임베딩 모델 다운로드
    if not args.skip_model:
        if not download_embedding_model():
            logger.error("임베딩 모델 다운로드 실패")
            return 1
    else:
        logger.info("임베딩 모델 다운로드 건너뛰기")
    
    # 벡터 스토어 테스트
    if not args.skip_test:
        if not test_vector_store():
            logger.error("벡터 스토어 테스트 실패")
            return 1
    else:
        logger.info("벡터 스토어 테스트 건너뛰기")
    
    logger.info("LLM 메모리 시스템 설정 완료!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
