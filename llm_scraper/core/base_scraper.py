"""
Base scraper class providing common functionality for all LLM web interface scrapers.
"""
from abc import ABC, abstractmethod
import logging
import time
from typing import Dict, List, Optional, Union, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseScraper(ABC):
    """
    Abstract base class for LLM web interface scrapers.
    
    This class provides common functionality for web scraping operations
    including browser initialization, navigation, and error handling.
    """
    
    def __init__(
        self,
        headless: bool = False,
        timeout: int = 60,
        browser_type: str = "chrome",
        user_data_dir: Optional[str] = None,
        debug: bool = False,
    ):
        """
        Initialize the base scraper.
        
        Args:
            headless: Whether to run the browser in headless mode
            timeout: Default timeout for wait operations in seconds
            browser_type: Type of browser to use ('chrome' or 'firefox')
            user_data_dir: Path to user data directory for browser profile
            debug: Enable debug logging
        """
        self.headless = headless
        self.timeout = timeout
        self.browser_type = browser_type
        self.user_data_dir = user_data_dir
        self.debug = debug
        self.driver = None
        self.logged_in = False
        
        # Set up logging level
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
    def __enter__(self):
        """Context manager entry."""
        self.initialize_browser()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
        
    def initialize_browser(self):
        """Initialize the web browser with appropriate settings."""
        if self.browser_type == "chrome":
            options = ChromeOptions()
            
            if self.headless:
                options.add_argument("--headless=new")
                
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            
            if self.user_data_dir:
                options.add_argument(f"--user-data-dir={self.user_data_dir}")
                
            # Add performance and stability options
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            
            try:
                self.driver = webdriver.Chrome(options=options)
                self.driver.set_page_load_timeout(self.timeout)
                logger.info("Chrome browser initialized")
            except WebDriverException as e:
                logger.error(f"Failed to initialize Chrome browser: {e}")
                raise
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")
    
    def cleanup(self):
        """Clean up resources and close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error while closing browser: {e}")
    
    def navigate_to(self, url: str):
        """
        Navigate the browser to a URL.
        
        Args:
            url: The URL to navigate to
        """
        if not self.driver:
            self.initialize_browser()
            
        try:
            logger.info(f"Navigating to {url}")
            self.driver.get(url)
        except TimeoutException:
            logger.warning(f"Timeout while loading {url}")
            # Attempt to continue anyway
        except WebDriverException as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise
    
    def wait_for_element(
        self, 
        locator: tuple, 
        timeout: Optional[int] = None, 
        condition: str = "visible"
    ):
        """
        Wait for an element to be present/visible/clickable.
        
        Args:
            locator: A tuple of (By, selector) to locate the element
            timeout: Timeout in seconds, defaults to self.timeout
            condition: The condition to wait for ('present', 'visible', 'clickable')
            
        Returns:
            The WebElement once the condition is met
        """
        if not timeout:
            timeout = self.timeout
            
        wait = WebDriverWait(self.driver, timeout)
        
        try:
            if condition == "present":
                return wait.until(EC.presence_of_element_located(locator))
            elif condition == "visible":
                return wait.until(EC.visibility_of_element_located(locator))
            elif condition == "clickable":
                return wait.until(EC.element_to_be_clickable(locator))
            else:
                raise ValueError(f"Unsupported wait condition: {condition}")
        except TimeoutException:
            logger.error(f"Timeout waiting for element {locator} to be {condition}")
            if self.debug:
                self.save_screenshot(f"error_wait_for_{condition}.png")
            raise
    
    def save_screenshot(self, filename: str):
        """
        Save a screenshot of the current browser window.
        
        Args:
            filename: Name of the file to save the screenshot to
        """
        if not self.driver:
            logger.warning("Cannot take screenshot: browser not initialized")
            return
            
        try:
            filepath = f"screenshots/{filename}"
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
    
    @abstractmethod
    def login(self, credentials: Dict[str, str]):
        """
        Log in to the LLM web interface.
        
        Args:
            credentials: Dictionary with authentication information
        """
        pass
    
    @abstractmethod
    def submit_prompt(self, prompt: str) -> str:
        """
        Submit a prompt to the LLM and return the response.
        
        Args:
            prompt: The text prompt to submit
            
        Returns:
            The LLM's response text
        """
        pass
    
    @abstractmethod
    def is_response_complete(self) -> bool:
        """
        Check if the LLM has finished generating its response.
        
        Returns:
            True if the response is complete, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_response(self) -> str:
        """
        Extract the LLM's response from the web page.
        
        Returns:
            The text of the LLM's response
        """
        pass
    
    def wait_for_response_completion(self, check_interval: float = 0.5, max_wait: int = None):
        """
        Wait for the LLM to complete its response.
        
        Args:
            check_interval: Time in seconds between completion checks
            max_wait: Maximum time to wait in seconds, defaults to self.timeout
        """
        if not max_wait:
            max_wait = self.timeout
            
        logger.info("Waiting for response completion...")
        start_time = time.time()
        
        while not self.is_response_complete():
            if time.time() - start_time > max_wait:
                logger.warning(f"Timed out after {max_wait}s waiting for response completion")
                break
            time.sleep(check_interval)
            
        logger.info("Response completed")
