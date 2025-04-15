"""
Vector DB 통합 테스트 코드
실행 방법: python vector_db_integration_test.py
"""

import os
import time
import sys
import shutil
import tempfile
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가하여 모듈을 임포트할 수 있도록 함
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from vector_db import VectorDB, Document
    from vector_db.encoders import DefaultEncoder
    
    # SentenceTransformer 인코더 임포트 시도
    try:
        from vector_db.encoders import SentenceTransformerEncoder
        SENTENCE_TRANSFORMER_AVAILABLE = True
    except ImportError:
        SENTENCE_TRANSFORMER_AVAILABLE = False
    
    # 테스트 설정
    DEBUG = True
    TEST_DIR = tempfile.mkdtemp(prefix="vector_db_integration_test_")
    
    def print_header(title: str) -> None:
        """형식화된 헤더 출력"""
        print("\n" + "=" * 80)
        print(f" {title} ".center(80, "="))
        print("=" * 80 + "\n")
    
    def cleanup() -> None:
        """테스트 후 임시 디렉토리 정리"""
        try:
            shutil.rmtree(TEST_DIR)
            print(f"임시 테스트 디렉토리 삭제 완료: {TEST_DIR}")
        except Exception as e:
            print(f"디렉토리 정리 중 오류 발생: {e}")
    
    def test_basic_workflow() -> bool:
        """기본 워크플로우 테스트: 생성, 추가, 검색, 삭제"""
        print_header("기본 워크플로우 테스트")
        
        success = True
        try:
            # 데이터베이스 생성
            print("1. 벡터 데이터베이스 초기화")
            db = VectorDB(encoder=DefaultEncoder(dimension=64))
            
            # 문서 추가
            print("\n2. 문서 추가")
            sample_docs = [
                "인공지능(AI)은 기계에 의해 시연되는 지능입니다.",
                "머신러닝은 데이터 기반 학습에 중점을 둔 AI의 하위 집합입니다.",
                "자연어 처리(NLP)는 컴퓨터가 인간 언어를 이해하도록 도와줍니다.",
                "컴퓨터 비전은 기계가 시각적 정보를 해석하고 처리할 수 있게 합니다.",
                "신경망은 생물학적 신경망에서 영감을 받은 컴퓨팅 시스템입니다."
            ]
            
            doc_ids = []
            for i, doc in enumerate(sample_docs):
                doc_id = db.add(doc, metadata={"index": i, "topic": "AI"})
                doc_ids.append(doc_id)
                print(f"  - 문서 추가됨: ID={doc_id}, 인덱스={i}")
            
            print(f"  => 총 {db.count()}개 문서 추가됨")
            
            if db.count() != len(sample_docs):
                print("  [오류] 문서 수가 일치하지 않습니다!")
                success = False
            
            # 유사 문서 검색
            print("\n3. 유사 문서 검색")
            query = "컴퓨터가 인간 언어를 이해하는 방법은 무엇인가요?"
            print(f"  검색 쿼리: '{query}'")
            
            results = db.search(query, k=3)
            print(f"  검색 결과 {len(results)}개:")
            
            for i, (doc, score) in enumerate(results):
                print(f"  {i+1}. 점수: {score:.4f}")
                print(f"     텍스트: {doc.text}")
                print(f"     메타데이터: {doc.metadata}")
            
            if len(results) != 3:
                print("  [오류] 검색 결과 수가 예상과 다릅니다!")
                success = False
            
            # 메타데이터 필터링
            print("\n4. 메타데이터 필터링 테스트")
            
            # 추가 문서 (다른 주제)
            other_doc_id = db.add("이것은 다른 주제에 관한 문서입니다.", 
                                metadata={"topic": "other"})
            print(f"  - 다른 주제 문서 추가됨: ID={other_doc_id}")
            
            # 주제별 필터링
            filtered_results = db.search(query, filter_metadata={"topic": "AI"})
            print(f"  AI 주제로 필터링된 검색 결과: {len(filtered_results)}개")
            
            # 모든 결과가 AI 주제인지 확인
            all_ai = all(doc.metadata.get("topic") == "AI" for doc, _ in filtered_results)
            print(f"  모든 결과가 AI 주제임: {all_ai}")
            
            if not all_ai:
                print("  [오류] 필터링된 결과에 다른 주제가 포함되어 있습니다!")
                success = False
            
            # 문서 업데이트
            print("\n5. 문서 업데이트")
            first_id = doc_ids[0]
            print(f"  문서 ID {first_id} 업데이트")
            
            update_success = db.update(
                first_id,
                text="인공지능(AI)은 인간과 같이 생각하고 학습하도록 프로그래밍된 기계의 지능 시뮬레이션입니다.",
                metadata={"index": 0, "topic": "AI", "updated": True}
            )
            
            print(f"  업데이트 성공: {update_success}")
            
            if not update_success:
                print("  [오류] 문서 업데이트에 실패했습니다!")
                success = False
            
            # 업데이트된 문서 확인
            updated_doc = db.get(first_id)
            print(f"  업데이트된 문서: {updated_doc.text[:50]}...")
            print(f"  업데이트된 메타데이터: {updated_doc.metadata}")
            
            if not updated_doc.metadata.get("updated"):
                print("  [오류] 문서 메타데이터가 제대로 업데이트되지 않았습니다!")
                success = False
            
            # 문서 삭제
            print("\n6. 문서 삭제")
            delete_id = doc_ids[-1]
            print(f"  문서 ID {delete_id} 삭제")
            
            before_count = db.count()
            delete_success = db.delete(delete_id)
            after_count = db.count()
            
            print(f"  삭제 전 문서 수: {before_count}")
            print(f"  삭제 후 문서 수: {after_count}")
            print(f"  삭제 성공: {delete_success}")
            
            if not delete_success or (before_count - after_count) != 1:
                print("  [오류] 문서 삭제에 실패했습니다!")
                success = False
            
            # 데이터베이스 초기화
            print("\n7. 데이터베이스 초기화")
            db.clear()
            
            print(f"  초기화 후 문서 수: {db.count()}")
            
            if db.count() != 0:
                print("  [오류] 데이터베이스가 제대로 초기화되지 않았습니다!")
                success = False
            
            print("\n=> 기본 워크플로우 테스트 결과:", "성공" if success else "실패")
            
        except Exception as e:
            print(f"\n[오류] 테스트 실행 중 예외 발생: {e}")
            success = False
        
        return success
    
    def test_persistence() -> bool:
        """영구 저장 기능 테스트"""
        print_header("영구 저장 기능 테스트")
        
        success = True
        storage_path = os.path.join(TEST_DIR, "persistent_db")
        
        try:
            # 첫 번째 인스턴스 생성 및 데이터 추가
            print("1. 첫 번째 데이터베이스 인스턴스 생성")
            db1 = VectorDB(storage_dir=storage_path)
            
            # 샘플 데이터 추가
            print("\n2. 첫 번째 인스턴스에 문서 추가")
            docs = [
                "첫 번째 샘플 문서입니다.",
                "두 번째 샘플 문서입니다.",
                "세 번째 샘플 문서입니다."
            ]
            
            doc_ids = []
            for i, doc in enumerate(docs):
                doc_id = db1.add(doc, metadata={"index": i, "instance": "first"})
                doc_ids.append(doc_id)
                print(f"  - 문서 추가됨: ID={doc_id}")
            
            print(f"  => 총 {db1.count()}개 문서 추가됨")
            
            if db1.count() != len(docs):
                print("  [오류] 문서 수가 일치하지 않습니다!")
                success = False
            
            # 두 번째 인스턴스로 데이터 로드
            print("\n3. 두 번째 데이터베이스 인스턴스 생성 (같은 저장소)")
            db2 = VectorDB(storage_dir=storage_path)
            
            print(f"  두 번째 인스턴스의 문서 수: {db2.count()}")
            
            if db2.count() != len(docs):
                print("  [오류] 두 번째 인스턴스의 문서 수가 일치하지 않습니다!")
                success = False
            
            # 원본 문서 확인
            print("\n4. 두 번째 인스턴스에서 문서 내용 확인")
            for i, doc_id in enumerate(doc_ids):
                doc = db2.get(doc_id)
                if doc is None:
                    print(f"  [오류] ID {doc_id}의 문서를 찾을 수 없습니다!")
                    success = False
                    continue
                
                print(f"  - 문서 ID {doc_id}: '{doc.text}'")
                
                if doc.text != docs[i]:
                    print(f"  [오류] 문서 내용이 일치하지 않습니다!")
                    success = False
            
            # 두 번째 인스턴스에 문서 추가
            print("\n5. 두 번째 인스턴스에 추가 문서 추가")
            new_doc_id = db2.add("두 번째 인스턴스에서 추가한 문서입니다.", 
                               metadata={"instance": "second"})
            
            print(f"  - 추가된 문서 ID: {new_doc_id}")
            print(f"  => 두 번째 인스턴스의 문서 수: {db2.count()}")
            
            # 첫 번째 인스턴스 다시 로드하여 변경 확인
            print("\n6. 첫 번째 인스턴스 다시 로드하여 변경 확인")
            db1 = VectorDB(storage_dir=storage_path)
            
            print(f"  재로드된 첫 번째 인스턴스의 문서 수: {db1.count()}")
            
            if db1.count() != len(docs) + 1:
                print("  [오류] 재로드된 인스턴스의 문서 수가 일치하지 않습니다!")
                success = False
            
            # 새 문서 확인
            new_doc = db1.get(new_doc_id)
            if new_doc is None:
                print(f"  [오류] 추가된 문서를 첫 번째 인스턴스에서 찾을 수 없습니다!")
                success = False
            else:
                print(f"  - 두 번째 인스턴스에서 추가한 문서: '{new_doc.text}'")
                print(f"  - 문서 메타데이터: {new_doc.metadata}")
                
                if new_doc.metadata.get("instance") != "second":
                    print("  [오류] 메타데이터가 일치하지 않습니다!")
                    success = False
            
            # 정리
            print("\n7. 데이터베이스 초기화")
            db1.clear()
            
            print(f"  초기화 후 db1 문서 수: {db1.count()}")
            
            # 두 번째 인스턴스도 비어 있는지 확인
            db2 = VectorDB(storage_dir=storage_path)
            print(f"  초기화 후 db2 문서 수: {db2.count()}")
            
            if db1.count() != 0 or db2.count() != 0:
                print("  [오류] 데이터베이스가 제대로 초기화되지 않았습니다!")
                success = False
            
            print("\n=> 영구 저장 테스트 결과:", "성공" if success else "실패")
            
        except Exception as e:
            print(f"\n[오류] 테스트 실행 중 예외 발생: {e}")
            success = False
        
        return success
    
    def test_batch_operations() -> bool:
        """일괄 작업 테스트"""
        print_header("일괄 작업 테스트")
        
        success = True
        try:
            # 데이터베이스 생성
            db = VectorDB()
            
            # 문서 및 메타데이터 배치 준비
            print("1. 배치 문서 및 메타데이터 준비")
            batch_docs = [
                "일괄 처리 첫 번째 문서입니다.",
                "일괄 처리 두 번째 문서입니다.",
                "일괄 처리 세 번째 문서입니다.",
                "일괄 처리 네 번째 문서입니다.",
                "일괄 처리 다섯 번째 문서입니다."
            ]
            
            batch_metadata = [
                {"index": 0, "batch": 1, "priority": "high"},
                {"index": 1, "batch": 1, "priority": "medium"},
                {"index": 2, "batch": 1, "priority": "low"},
                {"index": 3, "batch": 1, "priority": "medium"},
                {"index": 4, "batch": 1, "priority": "high"}
            ]
            
            # 일괄 추가 실행 및 성능 측정
            print("\n2. 일괄 추가 실행")
            start_time = time.time()
            doc_ids = db.add_batch(batch_docs, metadatas=batch_metadata)
            end_time = time.time()
            
            print(f"  - {len(doc_ids)}개 문서 일괄 추가 완료")
            print(f"  - 소요 시간: {(end_time - start_time):.4f}초")
            
            if len(doc_ids) != len(batch_docs):
                print("  [오류] 추가된 문서 수가 일치하지 않습니다!")
                success = False
            
            # 모든 문서 확인
            print("\n3. 추가된 모든 문서 확인")
            for i, doc_id in enumerate(doc_ids):
                doc = db.get(doc_id)
                if doc is None:
                    print(f"  [오류] ID {doc_id}의 문서를 찾을 수 없습니다!")
                    success = False
                    continue
                
                print(f"  - 문서 {i}: '{doc.text}'")
                print(f"    메타데이터: {doc.metadata}")
                
                if doc.metadata.get("index") != i:
                    print(f"  [오류] 메타데이터 인덱스가 일치하지 않습니다!")
                    success = False
            
            # 메타데이터 필터링으로 검색
            print("\n4. 우선순위 기준 필터링 검색")
            
            # 높은 우선순위 검색
            high_results = db.search("일괄 처리", filter_metadata={"priority": "high"})
            print(f"  - 높은 우선순위 문서 수: {len(high_results)}")
            
            # 모든 결과가 높은 우선순위인지 확인
            if not all(doc.metadata.get("priority") == "high" for doc, _ in high_results):
                print("  [오류] 필터링된 결과에 잘못된 우선순위가 포함되어 있습니다!")
                success = False
            
            # 중간 우선순위 검색
            medium_results = db.search("일괄 처리", filter_metadata={"priority": "medium"})
            print(f"  - 중간 우선순위 문서 수: {len(medium_results)}")
            
            # 낮은 우선순위 검색
            low_results = db.search("일괄 처리", filter_metadata={"priority": "low"})
            print(f"  - 낮은 우선순위 문서 수: {len(low_results)}")
            
            # 우선순위별 문서 수 확인
            expected_high = 2
            expected_medium = 2
            expected_low = 1
            
            if len(high_results) != expected_high:
                print(f"  [오류] 높은 우선순위 문서 수가 예상({expected_high})과 다릅니다!")
                success = False
            
            if len(medium_results) != expected_medium:
                print(f"  [오류] 중간 우선순위 문서 수가 예상({expected_medium})과 다릅니다!")
                success = False
            
            if len(low_results) != expected_low:
                print(f"  [오류] 낮은 우선순위 문서 수가 예상({expected_low})과 다릅니다!")
                success = False
            
            # 정리
            print("\n5. 데이터베이스 초기화")
            db.clear()
            
            print(f"  초기화 후 문서 수: {db.count()}")
            
            if db.count() != 0:
                print("  [오류] 데이터베이스가 제대로 초기화되지 않았습니다!")
                success = False
            
            print("\n=> 일괄 작업 테스트 결과:", "성공" if success else "실패")
            
        except Exception as e:
            print(f"\n[오류] 테스트 실행 중 예외 발생: {e}")
            success = False
        
        return success
    
    def test_sentence_transformer_encoder() -> bool:
        """SentenceTransformer 인코더 테스트 (설치된 경우만)"""
        print_header("SentenceTransformer 인코더 테스트")
        
        if not SENTENCE_TRANSFORMER_AVAILABLE:
            print("SentenceTransformer가 설치되어 있지 않습니다.")
            print("pip install sentence-transformers 명령으로 설치할 수 있습니다.")
            return True  # 설치되지 않은 경우 테스트 성공으로 간주
        
        success = True
        try:
            # SentenceTransformer 인코더 생성
            print("1. SentenceTransformer 인코더 생성")
            encoder = SentenceTransformerEncoder(model_name="all-MiniLM-L6-v2")
            db = VectorDB(encoder=encoder)
            
            # 의미적으로 관련된 문서 추가
            print("\n2. 의미적으로 관련된 문서 추가")
            semantic_docs = [
                "고양이가 매트 위에 앉아 있습니다.",
                "한 마리의 고양이가 바닥에 쉬고 있습니다.",
                "강아지가 공원에서 뛰어다닙니다.",
                "한 마리의 개가 정원에서 산책하고 있습니다.",
                "파이썬은 프로그래밍 언어입니다.",
                "자바스크립트는 웹 개발에 사용됩니다."
            ]
            
            doc_ids = []
            for doc in semantic_docs:
                doc_id = db.add(doc)
                doc_ids.append(doc_id)
            
            print(f"  - {len(doc_ids)}개 문서 추가됨")
            
            # 의미적으로 유사한 문서 검색 (고양이 관련)
            print("\n3. 의미적 유사성 테스트 쿼리")
            cat_query = "고양이가 카펫 위에서 휴식을 취하고 있습니다."
            print(f"  쿼리: '{cat_query}'")
            
            cat_results = db.search(cat_query, k=2)
            print("\n  결과:")
            for i, (doc, score) in enumerate(cat_results):
                print(f"  {i+1}. 점수: {score:.4f}, 문서: '{doc.text}'")
            
            # 상위 결과가 고양이 관련 문서인지 확인
            expected_cat_keyword = "고양이"
            has_cat_keyword = any(expected_cat_keyword in doc.text for doc, _ in cat_results)
            if not has_cat_keyword:
                print(f"  [오류] 고양이 관련 쿼리 결과에 예상 키워드가 없습니다!")
                success = False
            
            # 의미적으로 유사한 문서 검색 (프로그래밍 관련)
            print("\n  프로그래밍 쿼리")
            prog_query = "코딩과 소프트웨어 개발"
            print(f"  쿼리: '{prog_query}'")
            
            prog_results = db.search(prog_query, k=2)
            print("\n  결과:")
            for i, (doc, score) in enumerate(prog_results):
                print(f"  {i+1}. 점수: {score:.4f}, 문서: '{doc.text}'")
            
            # 상위 결과가 프로그래밍 관련 문서인지 확인
            expected_prog_keywords = ["파이썬", "자바스크립트", "프로그래밍", "개발"]
            has_prog_keyword = any(any(keyword in doc.text for keyword in expected_prog_keywords) 
                                  for doc, _ in prog_results)
            
            if not has_prog_keyword:
                print(f"  [오류] 프로그래밍 관련 쿼리 결과에 예상 키워드가 없습니다!")
                success = False
            
            # 단일 토큰 검색 테스트
            print("\n4. 단일 토큰 쿼리 테스트")
            token_query = "프로그래밍"
            print(f"  쿼리: '{token_query}'")
            
            token_results = db.search(token_query, k=1)
            print("\n  결과:")
            for i, (doc, score) in enumerate(token_results):
                print(f"  {i+1}. 점수: {score:.4f}, 문서: '{doc.text}'")
            
            # 결과가 프로그래밍 관련 문서인지 확인
            has_programming = "파이썬" in token_results[0][0].text or "프로그래밍" in token_results[0][0].text
            if not has_programming:
                print(f"  [오류] 프로그래밍 토큰 쿼리 결과가 관련 문서가 아닙니다!")
                success = False
            
            # 정리
            print("\n5. 데이터베이스 초기화")
            db.clear()
            
            print(f"  초기화 후 문서 수: {db.count()}")
            
            if db.count() != 0:
                print("  [오류] 데이터베이스가 제대로 초기화되지 않았습니다!")
                success = False
            
            print("\n=> SentenceTransformer 인코더 테스트 결과:", "성공" if success else "실패")
            
        except Exception as e:
            print(f"\n[오류] 테스트 실행 중 예외 발생: {e}")
            success = False
        
        return success

    # 메인 함수
    def run_integration_tests():
        """통합 테스트 실행"""
        print("\n===== Vector DB 통합 테스트 시작 =====\n")
        
        results = {}
        
        # 기본 워크플로우 테스트
        results["기본 워크플로우"] = test_basic_workflow()
        
        # 영구 저장 테스트
        results["영구 저장"] = test_persistence()
        
        # 일괄 작업 테스트
        results["일괄 작업"] = test_batch_operations()
        
        # SentenceTransformer 인코더 테스트 (설치된 경우)
        if SENTENCE_TRANSFORMER_AVAILABLE:
            results["SentenceTransformer"] = test_sentence_transformer_encoder()
        
        # 결과 요약
        print("\n===== Vector DB 통합 테스트 결과 요약 =====\n")
        all_passed = True
        
        for test_name, passed in results.items():
            status = "성공 ✓" if passed else "실패 ✗"
            print(f"{test_name}: {status}")
            all_passed = all_passed and passed
        
        print("\n전체 결과:", "성공 ✓" if all_passed else "실패 ✗")
        
        # 정리
        cleanup()
        
        return all_passed

    if __name__ == "__main__":
        success = run_integration_tests()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print("vector_db 모듈을 먼저 설치해주세요.")
    sys.exit(1)
except Exception as e:
    print(f"테스트 실행 중 오류 발생: {e}")
    sys.exit(1)
