"""
Vector DB 유닛 테스트 코드
실행 방법: python vector_db_test.py
"""

import os
import unittest
import tempfile
import shutil
import numpy as np
from pathlib import Path
import sys

# 현재 디렉토리를 sys.path에 추가하여 모듈을 임포트할 수 있도록 함
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from vector_db.vector_store import VectorDB, Document
    from vector_db.encoders import DefaultEncoder

    # 디버그 모드 활성화
    DEBUG = True

    class TestDocument(unittest.TestCase):
        """Document 클래스 테스트"""
        
        def test_document_creation(self):
            """문서 생성 및 속성 테스트"""
            print("문서 생성 테스트 시작")
            
            # 최소 정보로 문서 생성
            doc1 = Document(text="테스트 문서")
            self.assertEqual(doc1.text, "테스트 문서")
            self.assertIsNotNone(doc1.id)
            self.assertEqual(doc1.metadata, {})
            
            # 모든 속성을 지정하여 문서 생성
            doc2 = Document(
                text="메타데이터가 있는 테스트",
                metadata={"source": "unit_test", "importance": "high"},
                id="test-123"
            )
            self.assertEqual(doc2.text, "메타데이터가 있는 테스트")
            self.assertEqual(doc2.id, "test-123")
            self.assertEqual(doc2.metadata["source"], "unit_test")
            self.assertEqual(doc2.metadata["importance"], "high")
            
            print("문서 생성 테스트 완료")
        
        def test_document_serialization(self):
            """문서 직렬화 및 역직렬화 테스트"""
            print("문서 직렬화 테스트 시작")
            
            # 원본 문서 생성
            original = Document(
                text="직렬화 테스트",
                metadata={"test_type": "serialization"},
                id="ser-123"
            )
            
            # 딕셔너리로 변환
            doc_dict = original.to_dict()
            
            # 다시 Document로 변환
            reconstructed = Document.from_dict(doc_dict)
            
            # 모든 속성이 일치하는지 확인
            self.assertEqual(reconstructed.id, original.id)
            self.assertEqual(reconstructed.text, original.text)
            self.assertEqual(reconstructed.metadata, original.metadata)
            
            print("문서 직렬화 테스트 완료")

    class TestVectorDB(unittest.TestCase):
        """VectorDB 클래스 테스트"""
        
        def setUp(self):
            """테스트용 임시 디렉토리 생성 및 DB 초기화"""
            self.temp_dir = tempfile.mkdtemp()
            print(f"테스트용 임시 디렉토리 생성: {self.temp_dir}")
            
            # 메모리 기반 데이터베이스 생성
            self.db = VectorDB(encoder=DefaultEncoder(dimension=64))
            
            # 샘플 문서
            self.sample_docs = [
                "Python은 배우기 쉽고 사용하기 쉬운 프로그래밍 언어입니다.",
                "자연어 처리는 컴퓨터가 인간의 언어를 이해하도록 돕습니다.",
                "벡터 데이터베이스는 임베딩을 사용하여 유사한 문서를 찾습니다.",
                "머신러닝 알고리즘은 데이터에서 패턴을 학습합니다.",
                "인공지능은 스마트한 기계를 만드는 것을 목표로 합니다."
            ]
            
            # 샘플 문서 추가
            self.doc_ids = []
            for doc in self.sample_docs:
                doc_id = self.db.add(doc, metadata={"source": "test"})
                self.doc_ids.append(doc_id)
            
            print(f"데이터베이스에 {len(self.sample_docs)}개 문서 추가 완료")
        
        def tearDown(self):
            """테스트 후 임시 디렉토리 삭제"""
            shutil.rmtree(self.temp_dir)
            print(f"임시 디렉토리 삭제: {self.temp_dir}")
        
        def test_add_documents(self):
            """문서 추가 테스트"""
            print("문서 추가 테스트 시작")
            
            # 문서 수 확인
            self.assertEqual(self.db.count(), len(self.sample_docs))
            
            # 문서 추가
            new_id = self.db.add("추가 테스트 문서", metadata={"new": True})
            
            # 업데이트된 문서 수 확인
            self.assertEqual(self.db.count(), len(self.sample_docs) + 1)
            
            # 문서가 존재하는지 확인
            doc = self.db.get(new_id)
            self.assertIsNotNone(doc)
            self.assertEqual(doc.text, "추가 테스트 문서")
            self.assertTrue(doc.metadata["new"])
            
            print("문서 추가 테스트 완료")
        
        def test_add_batch(self):
            """일괄 문서 추가 테스트"""
            print("일괄 문서 추가 테스트 시작")
            
            # 새 데이터베이스 생성
            db = VectorDB()
            
            # 문서 배치 추가
            batch_docs = ["문서 1", "문서 2", "문서 3"]
            batch_metadata = [
                {"index": 0, "batch": True},
                {"index": 1, "batch": True},
                {"index": 2, "batch": True}
            ]
            
            doc_ids = db.add_batch(batch_docs, metadatas=batch_metadata)
            
            # 문서 수 확인
            self.assertEqual(db.count(), len(batch_docs))
            
            # 모든 문서가 올바른 메타데이터와 함께 존재하는지 확인
            for i, doc_id in enumerate(doc_ids):
                doc = db.get(doc_id)
                self.assertEqual(doc.text, batch_docs[i])
                self.assertEqual(doc.metadata["index"], i)
                self.assertTrue(doc.metadata["batch"])
            
            print("일괄 문서 추가 테스트 완료")
        
        def test_search(self):
            """문서 검색 테스트"""
            print("문서 검색 테스트 시작")
            
            # 쿼리와 유사한 문서 검색
            query = "컴퓨터가 언어를 이해하는 방법은?"
            results = self.db.search(query, k=2)
            
            # 결과 수 확인
            self.assertEqual(len(results), 2)
            
            # 결과가 (Document, score) 튜플인지 확인
            self.assertIsInstance(results[0][0], Document)
            self.assertIsInstance(results[0][1], float)
            
            # 점수가 0과 1 사이인지 확인
            for _, score in results:
                self.assertGreaterEqual(score, 0)
                self.assertLessEqual(score, 1)
            
            # 가장 유사한 문서가 NLP 관련 내용인지 확인
            # (기본 인코더는 확률적이지만 일반적으로 작동해야 함)
            expected_content = "자연어 처리"
            self.assertTrue(any(expected_content in doc.text for doc, _ in results))
            
            print("문서 검색 테스트 완료")
        
        def test_metadata_filter(self):
            """메타데이터 필터링 테스트"""
            print("메타데이터 필터링 테스트 시작")
            
            # 다양한 메타데이터로 문서 추가
            self.db.add("카테고리 A의 문서", metadata={"category": "A"})
            self.db.add("카테고리 B의 문서", metadata={"category": "B"})
            self.db.add("카테고리 A의 다른 문서", metadata={"category": "A"})
            
            # 메타데이터 필터로 검색
            results = self.db.search("문서", filter_metadata={"category": "A"})
            
            # 모든 결과가 카테고리 A인지 확인
            for doc, _ in results:
                self.assertEqual(doc.metadata["category"], "A")
            
            print("메타데이터 필터링 테스트 완료")
        
        def test_update_document(self):
            """문서 업데이트 테스트"""
            print("문서 업데이트 테스트 시작")
            
            # 첫 번째 문서 ID 가져오기
            doc_id = self.doc_ids[0]
            
            # 원본 문서
            original = self.db.get(doc_id)
            
            # 텍스트 업데이트
            new_text = "업데이트된 문서 텍스트"
            self.db.update(doc_id, text=new_text)
            
            # 텍스트가 업데이트되었는지 확인
            updated = self.db.get(doc_id)
            self.assertEqual(updated.text, new_text)
            
            # 메타데이터 업데이트
            new_metadata = {"updated": True, "version": 2}
            self.db.update(doc_id, metadata=new_metadata)
            
            # 메타데이터가 업데이트되었는지 확인
            updated = self.db.get(doc_id)
            self.assertEqual(updated.metadata, new_metadata)
            
            # 텍스트와 메타데이터 모두 업데이트
            self.db.update(doc_id, text="둘 다 업데이트", metadata={"both": True})
            updated = self.db.get(doc_id)
            self.assertEqual(updated.text, "둘 다 업데이트")
            self.assertTrue(updated.metadata["both"])
            
            print("문서 업데이트 테스트 완료")
        
        def test_delete_document(self):
            """문서 삭제 테스트"""
            print("문서 삭제 테스트 시작")
            
            # 초기 문서 수
            initial_count = self.db.count()
            
            # 첫 번째 문서 삭제
            first_id = self.doc_ids[0]
            self.db.delete(first_id)
            
            # 문서 수가 감소했는지 확인
            self.assertEqual(self.db.count(), initial_count - 1)
            
            # 문서가 더 이상 존재하지 않는지 확인
            self.assertIsNone(self.db.get(first_id))
            
            # 존재하지 않는 문서 삭제 시도
            result = self.db.delete("non-existent-id")
            self.assertFalse(result)
            
            print("문서 삭제 테스트 완료")
        
        def test_clear_database(self):
            """데이터베이스 초기화 테스트"""
            print("데이터베이스 초기화 테스트 시작")
            
            # 초기 문서 수
            self.assertGreater(self.db.count(), 0)
            
            # 데이터베이스 초기화
            self.db.clear()
            
            # 문서 수가 0인지 확인
            self.assertEqual(self.db.count(), 0)
            
            # 첫 번째 문서가 더 이상 존재하지 않는지 확인
            self.assertIsNone(self.db.get(self.doc_ids[0]))
            
            print("데이터베이스 초기화 테스트 완료")
        
        def test_persistence(self):
            """데이터베이스 영구 저장 테스트"""
            print("데이터베이스 영구 저장 테스트 시작")
            
            # 저장소가 있는 데이터베이스 생성
            storage_path = os.path.join(self.temp_dir, "test_db")
            db1 = VectorDB(storage_dir=storage_path)
            
            # 문서 추가
            doc_ids = []
            for i, doc in enumerate(self.sample_docs):
                doc_id = db1.add(doc, metadata={"index": i})
                doc_ids.append(doc_id)
            
            # 같은 저장소를 가리키는 새 데이터베이스 인스턴스 생성
            db2 = VectorDB(storage_dir=storage_path)
            
            # 새 인스턴스에 문서가 존재하는지 확인
            self.assertEqual(db2.count(), len(self.sample_docs))
            
            # 문서 내용 확인
            for i, doc_id in enumerate(doc_ids):
                doc = db2.get(doc_id)
                self.assertEqual(doc.text, self.sample_docs[i])
                self.assertEqual(doc.metadata["index"], i)
            
            print("데이터베이스 영구 저장 테스트 완료")

    class TestDefaultEncoder(unittest.TestCase):
        """DefaultEncoder 클래스 테스트"""
        
        def setUp(self):
            """테스트용 인코더 생성"""
            self.encoder = DefaultEncoder(dimension=128)
        
        def test_encode(self):
            """단일 텍스트 인코딩 테스트"""
            print("단일 텍스트 인코딩 테스트 시작")
            
            # 텍스트 인코딩
            text = "인코딩 테스트 문서입니다"
            embedding = self.encoder.encode(text)
            
            # 형태 확인
            self.assertEqual(embedding.shape, (128,))
            
            # 벡터가 정규화되었는지 확인
            norm = np.linalg.norm(embedding)
            self.assertAlmostEqual(norm, 1.0, places=6)
            
            # 결정론적인지 확인 (같은 텍스트는 같은 임베딩을 생성해야 함)
            embedding2 = self.encoder.encode(text)
            np.testing.assert_array_almost_equal(embedding, embedding2)
            
            # 다른 텍스트는 다른 임베딩을 생성해야 함
            different = self.encoder.encode("다른 텍스트입니다")
            self.assertFalse(np.array_equal(embedding, different))
            
            print("단일 텍스트 인코딩 테스트 완료")
        
        def test_encode_batch(self):
            """다중 텍스트 인코딩 테스트"""
            print("다중 텍스트 인코딩 테스트 시작")
            
            # 배치 인코딩
            texts = ["텍스트 1", "텍스트 2", "텍스트 3"]
            embeddings = self.encoder.encode_batch(texts)
            
            # 형태 확인
            self.assertEqual(embeddings.shape, (len(texts), 128))
            
            # 개별 인코딩이 일치하는지 확인
            for i, text in enumerate(texts):
                single_embedding = self.encoder.encode(text)
                np.testing.assert_array_equal(embeddings[i], single_embedding)
            
            print("다중 텍스트 인코딩 테스트 완료")
        
        def test_empty_text(self):
            """빈 텍스트 인코딩 테스트"""
            print("빈 텍스트 인코딩 테스트 시작")
            
            # 빈 텍스트 인코딩
            embedding = self.encoder.encode("")
            
            # 0 벡터여야 함
            expected = np.zeros(128)
            np.testing.assert_array_equal(embedding, expected)
            
            # 빈 텍스트가 있는 배치
            texts = ["텍스트 1", "", "텍스트 3"]
            embeddings = self.encoder.encode_batch(texts)
            
            # 두 번째 임베딩이 0 벡터인지 확인
            np.testing.assert_array_equal(embeddings[1], expected)
            
            print("빈 텍스트 인코딩 테스트 완료")

    # 메인 함수 - 테스트 실행
    def run_tests():
        """모든 테스트 실행"""
        print("\n===== Vector DB 유닛 테스트 시작 =====\n")
        
        # 테스트 스위트 생성
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # 테스트 클래스 추가
        suite.addTest(loader.loadTestsFromTestCase(TestDocument))
        suite.addTest(loader.loadTestsFromTestCase(TestVectorDB))
        suite.addTest(loader.loadTestsFromTestCase(TestDefaultEncoder))
        
        # 테스트 실행
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        print("\n===== Vector DB 유닛 테스트 완료 =====")
        
        # 테스트 결과 요약
        print(f"\n결과 요약:")
        print(f"  실행된 테스트: {result.testsRun}")
        print(f"  성공: {result.testsRun - len(result.errors) - len(result.failures)}")
        print(f"  실패: {len(result.failures)}")
        print(f"  에러: {len(result.errors)}")
        
        # 성공 여부 반환
        return len(result.failures) == 0 and len(result.errors) == 0

    if __name__ == "__main__":
        success = run_tests()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print("vector_db 모듈을 먼저 설치해주세요.")
    sys.exit(1)
except Exception as e:
    print(f"테스트 실행 중 오류 발생: {e}")
    sys.exit(1)
