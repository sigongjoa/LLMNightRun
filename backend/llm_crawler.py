import os
import time
import logging
import json
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from models import LLMType
from database.operations import get_settings
from database.connection import SessionLocal

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMCrawler:
    """다양한 LLM 웹 인터페이스를 크롤링하는 클래스"""
    
    def __init__(self):
        """크롤러 초기화"""
        # 설정 가져오기
        self.settings = self._get_settings()
        
        # Selenium 설정
        self.options = webdriver.ChromeOptions()
        
        # 헤드리스 모드 (GUI 없이 실행, 서버 환경에 적합)
        if os.getenv("HEADLESS", "true").lower() == "true":
            self.options.add_argument("--headless")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--no-sandbox")
            self.options.add_argument("--disable-dev-shm-usage")
        
        # 기본 사용자 에이전트 지정
        self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        
        # 웹드라이버 생성
        self.driver = None
    
    def _get_settings(self) -> Dict[str, Any]:
        """데이터베이스에서 설정을 가져옵니다."""
        db = SessionLocal()
        try:
            settings = get_settings(db)
            if settings:
                # 필요한 설정 반환
                return {
                    "openai_username": os.getenv("OPENAI_USERNAME"),
                    "openai_password": os.getenv("OPENAI_PASSWORD"),
                    "claude_username": os.getenv("CLAUDE_USERNAME"),
                    "claude_password": os.getenv("CLAUDE_PASSWORD")
                }
            return {}
        finally:
            db.close()
    
    def _initialize_driver(self):
        """웹드라이버를 초기화합니다."""
        if self.driver is not None:
            self.driver.quit()
        
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_page_load_timeout(30)
    
    def _login_openai(self) -> bool:
        """OpenAI 로그인을 수행합니다."""
        username = self.settings.get("openai_username")
        password = self.settings.get("openai_password")
        
        if not username or not password:
            logger.error("OpenAI 로그인 정보가 없습니다.")
            return False
        
        try:
            # ChatGPT 로그인 페이지로 이동
            self.driver.get("https://chat.openai.com/auth/login")
            time.sleep(2)
            
            # 로그인 버튼 클릭
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in')]"))
            )
            login_button.click()
            
            # 이메일 입력
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.send_keys(username)
            time.sleep(1)
            email_input.send_keys(Keys.RETURN)
            
            # 비밀번호 입력
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_input.send_keys(password)
            time.sleep(1)
            password_input.send_keys(Keys.RETURN)
            
            # 로그인 성공 확인 (메인 채팅 영역이 로드되는지 확인)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'text-input')]"))
            )
            
            logger.info("OpenAI 로그인 성공")
            return True
        except Exception as e:
            logger.error(f"OpenAI 로그인 실패: {str(e)}")
            return False
    
    def _login_claude(self) -> bool:
        """Claude 로그인을 수행합니다."""
        username = self.settings.get("claude_username")
        password = self.settings.get("claude_password")
        
        if not username or not password:
            logger.error("Claude 로그인 정보가 없습니다.")
            return False
        
        try:
            # Claude 로그인 페이지로 이동
            self.driver.get("https://claude.ai/login")
            time.sleep(2)
            
            # 이메일 입력
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
            )
            email_input.send_keys(username)
            
            # 계속 버튼 클릭
            continue_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
            )
            continue_button.click()
            
            # 비밀번호 입력
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
            )
            password_input.send_keys(password)
            
            # 로그인 버튼 클릭
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
            )
            login_button.click()
            
            # 로그인 성공 확인 (메인 채팅 영역이 로드되는지 확인)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chat-input')]"))
            )
            
            logger.info("Claude 로그인 성공")
            return True
        except Exception as e:
            logger.error(f"Claude 로그인 실패: {str(e)}")
            return False
    
    def get_openai_response(self, prompt: str) -> Optional[str]:
        """
        OpenAI 웹 인터페이스에서 응답을 가져옵니다.
        
        Args:
            prompt: 질문 내용
            
        Returns:
            OpenAI의 응답 텍스트 또는 None (실패 시)
        """
        try:
            self._initialize_driver()
            
            # 로그인
            if not self._login_openai():
                return None
            
            # 새 대화 시작
            new_chat_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'New chat')]"))
            )
            new_chat_button.click()
            time.sleep(2)
            
            # 메시지 입력
            message_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'text-input')]"))
            )
            message_input.send_keys(prompt)
            message_input.send_keys(Keys.RETURN)
            
            # 응답 대기
            time.sleep(5)  # 초기 대기
            
            # 응답이 완료될 때까지 대기
            max_wait_time = 120  # 최대 2분
            wait_start = time.time()
            
            while time.time() - wait_start < max_wait_time:
                # 응답 생성 중 표시자 확인
                try:
                    generating_indicator = self.driver.find_element(By.XPATH, "//div[contains(@class, 'result-streaming')]")
                    if not generating_indicator.is_displayed():
                        # 생성 완료
                        break
                except NoSuchElementException:
                    # 표시자가 없으면 응답이 완료된 것으로 간주
                    break
                
                time.sleep(1)
            
            # 최신 응답 가져오기 (마지막 메시지)
            response_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'markdown')]")
            if response_elements:
                # 마지막 응답 요소의 텍스트 반환
                return response_elements[-1].text
            
            return None
        except Exception as e:
            logger.error(f"OpenAI 웹 응답 가져오기 실패: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def get_claude_response(self, prompt: str) -> Optional[str]:
        """
        Claude 웹 인터페이스에서 응답을 가져옵니다.
        
        Args:
            prompt: 질문 내용
            
        Returns:
            Claude의 응답 텍스트 또는 None (실패 시)
        """
        try:
            self._initialize_driver()
            
            # 로그인
            if not self._login_claude():
                return None
            
            # 새 대화 시작
            new_chat_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'New chat')]"))
            )
            new_chat_button.click()
            time.sleep(2)
            
            # 메시지 입력
            message_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chat-input')]"))
            )
            message_input.send_keys(prompt)
            
            # 전송 버튼 클릭
            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Send message']"))
            )
            send_button.click()
            
            # 응답 대기
            time.sleep(5)  # 초기 대기
            
            # 응답이 완료될 때까지 대기
            max_wait_time = 120  # 최대 2분
            wait_start = time.time()
            
            while time.time() - wait_start < max_wait_time:
                # 응답 생성 중 표시자 확인
                try:
                    generating_indicator = self.driver.find_element(By.XPATH, "//div[contains(@class, 'typing-indicator')]")
                    if not generating_indicator.is_displayed():
                        # 생성 완료
                        break
                except NoSuchElementException:
                    # 표시자가 없으면 응답이 완료된 것으로 간주
                    break
                
                time.sleep(1)
            
            # 최신 응답 가져오기 (마지막 AI 메시지)
            response_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'assistant-message')]")
            if response_elements:
                # 마지막 응답 요소의 텍스트 반환
                return response_elements[-1].text
            
            return None
        except Exception as e:
            logger.error(f"Claude 웹 응답 가져오기 실패: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

def get_web_llm_response(llm_type: LLMType, prompt: str) -> Optional[str]:
    """
    웹 인터페이스를 통해 LLM에 프롬프트를 전송하고 응답을 받아옵니다.
    
    Args:
        llm_type: LLM 유형
        prompt: 질문 내용
        
    Returns:
        LLM의 응답 텍스트 또는 None (실패 시)
    """
    crawler = LLMCrawler()
    
    if llm_type == LLMType.OPENAI_WEB:
        return crawler.get_openai_response(prompt)
    elif llm_type == LLMType.CLAUDE_WEB:
        return crawler.get_claude_response(prompt)
    else:
        logger.error(f"웹 크롤링이 지원되지 않는 LLM 유형입니다: {llm_type}")
        return None