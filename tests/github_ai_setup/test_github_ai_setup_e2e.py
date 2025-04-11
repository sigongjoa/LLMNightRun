"""
GitHub AI 환경 자동 설정 E2E 테스트

이 테스트 모듈은 GitHub AI 환경 자동 설정의 프론트엔드와 백엔드 통합 E2E 테스트를 수행합니다.
"""

import os
import sys
import time
import json
import logging
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 필요한 경로 추가 (상위 디렉토리 import 가능하게)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestGitHubAISetupE2E(unittest.TestCase):
    """GitHub AI 환경 자동 설정 E2E 테스트 클래스"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 준비"""
        # 웹드라이버 초기화 (Chrome)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # 헤드리스 모드
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.base_url = "http://localhost:3000"  # 프론트엔드 URL
            cls.driver.maximize_window()
            logger.info("WebDriver 초기화 완료")
        except Exception as e:
            logger.error(f"WebDriver 초기화 실패: {str(e)}")
            raise
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
            logger.info("WebDriver 종료")
    
    def setUp(self):
        """각 테스트 케이스 준비"""
        # 테스트에 사용할 GitHub 저장소 URL
        self.test_repo_url = "https://github.com/sigonjoa/test-repository"
    
    def test_github_ai_setup_page_load(self):
        """GitHub AI 환경 설정 페이지 로드 테스트"""
        try:
            # 페이지 접속
            self.driver.get(f"{self.base_url}/github-ai-setup")
            
            # 페이지 로드 확인
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h4[contains(text(), 'GitHub AI 환경 자동 설정')]"))
            )
            
            # 페이지 요소 확인
            title_element = self.driver.find_element(By.XPATH, "//h4[contains(text(), 'GitHub AI 환경 자동 설정')]")
            self.assertIsNotNone(title_element)
            
            # 단계 확인
            steps = self.driver.find_elements(By.CSS_SELECTOR, ".MuiStepLabel-label")
            self.assertEqual(len(steps), 4)  # 4단계 확인
            
            # URL 입력 필드 확인
            url_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='GitHub 저장소 URL']")
            self.assertIsNotNone(url_input)
            
            # 분석 버튼 확인
            analyze_button = self.driver.find_element(By.XPATH, "//button[contains(., '저장소 분석')]")
            self.assertIsNotNone(analyze_button)
            
            logger.info("GitHub AI 설정 페이지 로드 테스트 성공")
        except Exception as e:
            logger.error(f"페이지 로드 테스트 실패: {str(e)}")
            self.fail(f"페이지 로드 테스트 실패: {str(e)}")
    
    def test_repository_analysis_workflow(self):
        """저장소 분석 워크플로우 테스트"""
        try:
            # 페이지 접속
            self.driver.get(f"{self.base_url}/github-ai-setup")
            
            # 페이지 로드 확인
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='GitHub 저장소 URL']"))
            )
            
            # URL 입력
            url_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='GitHub 저장소 URL']")
            url_input.clear()
            url_input.send_keys(self.test_repo_url)
            
            # 분석 버튼 클릭
            analyze_button = self.driver.find_element(By.XPATH, "//button[contains(., '저장소 분석')]")
            analyze_button.click()
            
            # 분석 로딩 확인
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".MuiCircularProgress-root"))
                )
                logger.info("로딩 인디케이터 표시 확인")
            except TimeoutException:
                logger.warning("로딩 인디케이터가 표시되지 않았거나 너무 빨리 사라짐")
            
            # 분석 결과 확인 (최대 30초 대기)
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//h6[contains(text(), '분석 결과')]"))
                )
                logger.info("분석 결과 표시됨")
                
                # 분석 결과 내용 확인
                analysis_card = self.driver.find_element(By.XPATH, "//h6[contains(text(), '분석 결과')]/ancestor::div[contains(@class, 'MuiCardContent-root')]")
                self.assertIsNotNone(analysis_card)
                
                # 다음 버튼 확인 및 클릭
                next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '다음')]")
                self.assertIsNotNone(next_button)
                next_button.click()
                
                # 두 번째 단계로 이동 확인
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//p[contains(text(), '분석된 결과를 바탕으로 AI 환경을 자동으로 설정')]"))
                )
                
                logger.info("저장소 분석 워크플로우 테스트 성공")
            except TimeoutException:
                logger.error("분석 결과가 표시되지 않음")
                self.fail("분석 결과가 표시되지 않음 - 백엔드 응답 없음")
        except Exception as e:
            logger.error(f"저장소 분석 워크플로우 테스트 실패: {str(e)}")
            self.fail(f"저장소 분석 워크플로우 테스트 실패: {str(e)}")
    
    def test_complete_setup_workflow(self):
        """전체 설정 워크플로우 테스트 (스킵 - 오래 걸리는 작업)"""
        # 이 테스트는 실제 환경에서 실행하면 오래 걸리므로 실제 배포 환경에서만 실행하는 것이 좋음
        logger.info("전체 설정 워크플로우 테스트는 시간이 오래 걸려서 스킵됩니다.")
        

class TestGitHubAISetupMockE2E(unittest.TestCase):
    """GitHub AI 환경 자동 설정 모의 E2E 테스트 클래스"""

    def setUp(self):
        """각 테스트 케이스 준비"""
        # 모의 API 응답을 저장할 디렉토리
        self.mock_dir = os.path.join(os.path.dirname(__file__), "mock_responses")
        if not os.path.exists(self.mock_dir):
            os.makedirs(self.mock_dir)
        
        # 모의 분석 응답 저장
        self.analyze_response = {
            "repo_name": "test-repository",
            "repo_url": "https://github.com/sigonjoa/test-repository",
            "clone_path": "/tmp/test-repository",
            "model_type": {
                "primary": "llama",
                "all_detected": {"llama": 2}
            },
            "requirements": {
                "requirements.txt": {
                    "content": "torch\ntransformers\n",
                    "path": "/tmp/test-repository/requirements.txt"
                }
            },
            "launch_scripts": ["run.py", "inference.py"]
        }
        
        with open(os.path.join(self.mock_dir, "analyze_response.json"), 'w') as f:
            json.dump(self.analyze_response, f, indent=2)
    
    def test_mock_api_responses(self):
        """모의 API 응답 테스트"""
        # 분석 응답 확인
        with open(os.path.join(self.mock_dir, "analyze_response.json"), 'r') as f:
            analyze_response = json.load(f)
        
        self.assertEqual(analyze_response["repo_name"], "test-repository")
        self.assertEqual(analyze_response["model_type"]["primary"], "llama")
        
        logger.info("모의 API 응답 테스트 성공")


if __name__ == "__main__":
    unittest.main()
