"""
A/B 테스팅 시스템 테스트

A/B 테스팅 시스템의 기능을 테스트합니다.
"""

import unittest
import asyncio
import json
from unittest.mock import patch, MagicMock

# 테스트 대상 모듈 임포트
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ab_testing.controllers import (
    create_experiment_set, get_experiment_sets, get_experiment_set,
    update_experiment_set, delete_experiment_set, add_experiment,
    get_experiment, update_experiment, delete_experiment,
    run_experiment_set_background, get_experiment_set_status,
    get_experiment_set_results
)


class TestABTestingSystem(unittest.TestCase):
    """A/B 테스팅 시스템 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 비동기 이벤트 루프 설정
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # 테스트 데이터 설정
        self.test_experiment_set_data = {
            "name": "테스트 실험 세트",
            "description": "테스트용 실험 세트입니다.",
            "config": {
                "evaluation_metrics": ["relevance", "fluency", "accuracy"],
                "target_audience": "general"
            },
            "experiments": [
                {
                    "name": "기본 프롬프트",
                    "prompt": "다음 질문에 답변해주세요: {query}",
                    "model": "gpt-4",
                    "params": {"temperature": 0.7, "max_tokens": 500},
                    "is_control": True
                },
                {
                    "name": "세부 지시 프롬프트",
                    "prompt": "다음 질문에 상세하고 명확하게 답변해주세요: {query}",
                    "model": "gpt-4",
                    "params": {"temperature": 0.7, "max_tokens": 500},
                    "is_control": False
                }
            ]
        }
        
        self.test_experiment_data = {
            "name": "새 실험",
            "prompt": "새로운 프롬프트 템플릿: {query}",
            "model": "gpt-4",
            "params": {"temperature": 0.5, "max_tokens": 800},
            "is_control": False
        }
    
    def tearDown(self):
        """테스트 정리"""
        self.loop.close()
    
    def test_create_experiment_set(self):
        """실험 세트 생성 테스트"""
        # 함수 호출
        result = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        
        # 결과 검증
        self.assertIsNotNone(result["id"])
        self.assertEqual(result["name"], "테스트 실험 세트")
        self.assertEqual(len(result["experiments"]), 2)
    
    def test_get_experiment_sets(self):
        """실험 세트 목록 조회 테스트"""
        # 함수 호출
        result = self.loop.run_until_complete(
            get_experiment_sets(active_only=True)
        )
        
        # 결과 검증
        self.assertIsInstance(result, list)
        if result:  # 목록이 비어있지 않은 경우
            self.assertIn("id", result[0])
            self.assertIn("name", result[0])
    
    def test_get_experiment_set(self):
        """실험 세트 상세 조회 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 함수 호출
        result = self.loop.run_until_complete(
            get_experiment_set(experiment_set_id)
        )
        
        # 결과 검증
        self.assertEqual(result["id"], experiment_set_id)
        self.assertEqual(result["name"], "테스트 실험 세트")
        self.assertIn("experiments", result)
    
    def test_update_experiment_set(self):
        """실험 세트 업데이트 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 업데이트 데이터
        update_data = {
            "name": "업데이트된 실험 세트",
            "description": "설명이 업데이트되었습니다."
        }
        
        # 함수 호출
        result = self.loop.run_until_complete(
            update_experiment_set(experiment_set_id, update_data)
        )
        
        # 결과 검증
        self.assertEqual(result["id"], experiment_set_id)
        self.assertEqual(result["name"], "업데이트된 실험 세트")
        self.assertEqual(result["description"], "설명이 업데이트되었습니다.")
    
    def test_delete_experiment_set(self):
        """실험 세트 삭제 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 함수 호출
        result = self.loop.run_until_complete(
            delete_experiment_set(experiment_set_id)
        )
        
        # 결과 검증
        self.assertTrue(result["success"])
        self.assertIn("삭제되었습니다", result["message"])
    
    def test_add_experiment(self):
        """실험 추가 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 함수 호출
        result = self.loop.run_until_complete(
            add_experiment(experiment_set_id, self.test_experiment_data)
        )
        
        # 결과 검증
        self.assertIsNotNone(result["id"])
        self.assertEqual(result["name"], "새 실험")
        self.assertEqual(result["experiment_set_id"], experiment_set_id)
    
    def test_get_experiment(self):
        """실험 상세 조회 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 실험 추가
        experiment = self.loop.run_until_complete(
            add_experiment(experiment_set_id, self.test_experiment_data)
        )
        experiment_id = experiment["id"]
        
        # 함수 호출
        result = self.loop.run_until_complete(
            get_experiment(experiment_id)
        )
        
        # 결과 검증
        self.assertEqual(result["id"], experiment_id)
        self.assertEqual(result["name"], "새 실험")
    
    def test_update_experiment(self):
        """실험 업데이트 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 실험 추가
        experiment = self.loop.run_until_complete(
            add_experiment(experiment_set_id, self.test_experiment_data)
        )
        experiment_id = experiment["id"]
        
        # 업데이트 데이터
        update_data = {
            "name": "업데이트된 실험",
            "prompt": "업데이트된 프롬프트: {query}",
            "params": {"temperature": 0.3}
        }
        
        # 함수 호출
        result = self.loop.run_until_complete(
            update_experiment(experiment_id, update_data)
        )
        
        # 결과 검증
        self.assertEqual(result["id"], experiment_id)
        self.assertEqual(result["name"], "업데이트된 실험")
        self.assertEqual(result["prompt"], "업데이트된 프롬프트: {query}")
        self.assertEqual(result["params"]["temperature"], 0.3)
    
    def test_delete_experiment(self):
        """실험 삭제 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 실험 추가
        experiment = self.loop.run_until_complete(
            add_experiment(experiment_set_id, self.test_experiment_data)
        )
        experiment_id = experiment["id"]
        
        # 함수 호출
        result = self.loop.run_until_complete(
            delete_experiment(experiment_id)
        )
        
        # 결과 검증
        self.assertTrue(result["success"])
        self.assertIn("삭제되었습니다", result["message"])
    
    def test_run_experiment_set(self):
        """실험 세트 실행 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 실행 구성
        run_config = {
            "iterations": 5,
            "parallel": True,
            "timeout": 300
        }
        
        # 함수 호출
        result = self.loop.run_until_complete(
            run_experiment_set_background(experiment_set_id, run_config)
        )
        
        # 결과 검증
        self.assertIsNotNone(result["job_id"])
        self.assertEqual(result["experiment_set_id"], experiment_set_id)
        self.assertEqual(result["status"], "running")
    
    def test_get_experiment_set_status(self):
        """실험 세트 상태 조회 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 실행 시작
        run_result = self.loop.run_until_complete(
            run_experiment_set_background(experiment_set_id)
        )
        job_id = run_result["job_id"]
        
        # 함수 호출
        result = self.loop.run_until_complete(
            get_experiment_set_status(experiment_set_id, job_id)
        )
        
        # 결과 검증
        self.assertEqual(result["experiment_set_id"], experiment_set_id)
        self.assertEqual(result["job_id"], job_id)
        self.assertIn("status", result)
        self.assertIn("items_total", result)
        self.assertIn("items_processed", result)
    
    def test_get_experiment_set_results(self):
        """실험 세트 결과 조회 테스트"""
        # 실험 세트 생성
        experiment_set = self.loop.run_until_complete(
            create_experiment_set(self.test_experiment_set_data)
        )
        experiment_set_id = experiment_set["id"]
        
        # 함수 호출
        result = self.loop.run_until_complete(
            get_experiment_set_results(experiment_set_id)
        )
        
        # 결과 검증
        self.assertEqual(result["experiment_set_id"], experiment_set_id)
        self.assertIn("experiment_results", result)
        self.assertIsInstance(result["experiment_results"], list)


if __name__ == '__main__':
    unittest.main()
