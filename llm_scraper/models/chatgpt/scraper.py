"""
ChatGPT web interface scraper implementation.
"""
import time
from typing import Dict, Optional, Any
import logging
import json
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException
)

from ...core.base_scraper import BaseScraper
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

class ChatGPTScraper(BaseScraper):
    """
    Scraper for the ChatGPT web interface.
    """
    
    def __init__(
        self,
        headless: bool = False,
        timeout: int = 60,
        user_data_dir: Optional[str] = None,
        debug: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the ChatGPT scraper.
        
        Args:
            headless: Whether to run the browser in headless mode
            timeout: Default timeout for wait operations in seconds
            user_data_dir: Path to user data directory for browser profile
            debug: Enable debug logging
            config: Configuration dictionary with model-specific settings
        """
        super().__init__(
            headless=headless,
            timeout=timeout,
            browser_type="chrome",
            user_data_dir=user_data_dir,
            debug=debug,
        )
        
        self.config = config or {}
        self.model_config = self.config.get("models", {}).get("chatgpt", {})
        self.url = self.model_config.get("url", "https://chat.openai.com/")
        self.selectors = self.model_config.get("selectors", {})
        
        # Default selectors if not provided in config
        self.login_button_selector = self.selectors.get(
            "login_button", "//button[contains(text(), 'Log in')]"
        )
        self.prompt_textarea_selector = self.selectors.get(
            "prompt_textarea", "//textarea[@placeholder='Send a message']"
        )
        self.submit_button_selector = self.selectors.get(
            "submit_button", "//button[@type='submit']"
        )
        self.response_container_selector = self.selectors.get(
            "response_container", "//div[contains(@class, 'markdown')]"
        )
        self.thinking_indicator_selector = self.selectors.get(
            "thinking_indicator", "//div[contains(@class, 'thinking')]"
        )
        
        self.last_response_text = ""
        self.current_conversation_id = None
    
    def login(self, credentials: Dict[str, str]) -> bool:
        """
        Log in to ChatGPT web interface.
        
        Args:
            credentials: Dictionary with 'username' and 'password' keys
            
        Returns:
            True if login successful, False otherwise
        """
        if not self.driver:
            self.initialize_browser()
            
        self.navigate_to(self.url)
        
        try:
            # Check if already logged in
            try:
                # Look for elements that indicate we're already logged in
                self.wait_for_element((By.XPATH, self.prompt_textarea_selector), timeout=5)
                logger.info("Already logged in to ChatGPT")
                self.logged_in = True
                return True
            except TimeoutException:
                # Not logged in, continue with login process
                logger.info("Not logged in, proceeding with login")
            
            # Click login button
            login_button = self.wait_for_element(
                (By.XPATH, self.login_button_selector), 
                condition="clickable"
            )
            login_button.click()
            
            # Wait for email input
            email_input = self.wait_for_element(
                (By.ID, "username"), 
                condition="visible"
            )
            email_input.send_keys(credentials.get("username", ""))
            
            # Click continue
            continue_button = self.wait_for_element(
                (By.XPATH, "//button[@type='submit']"), 
                condition="clickable"
            )
            continue_button.click()
            
            # Wait for password input
            password_input = self.wait_for_element(
                (By.ID, "password"), 
                condition="visible"
            )
            password_input.send_keys(credentials.get("password", ""))
            
            # Click login
            login_submit = self.wait_for_element(
                (By.XPATH, "//button[@type='submit']"), 
                condition="clickable"
            )
            login_submit.click()
            
            # Wait for the chat interface to load
            self.wait_for_element(
                (By.XPATH, self.prompt_textarea_selector), 
                timeout=20,
                condition="visible"
            )
            
            logger.info("Successfully logged in to ChatGPT")
            self.logged_in = True
            return True
            
        except TimeoutException as e:
            logger.error(f"Timeout during login: {e}")
            if self.debug:
                self.save_screenshot("chatgpt_login_timeout.png")
            return False
        except Exception as e:
            logger.error(f"Error during login: {e}")
            if self.debug:
                self.save_screenshot("chatgpt_login_error.png")
            return False
    
    def start_new_conversation(self) -> bool:
        """
        Start a new conversation in ChatGPT.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Look for "New chat" button
            new_chat_button = self.wait_for_element(
                (By.XPATH, "//a[contains(@class, 'new-chat')]"), 
                timeout=5,
                condition="clickable"
            )
            new_chat_button.click()
            
            # Wait for the textarea to be ready
            self.wait_for_element(
                (By.XPATH, self.prompt_textarea_selector), 
                condition="visible"
            )
            
            logger.info("Started new conversation in ChatGPT")
            return True
            
        except TimeoutException:
            # No new chat button found, might already be on a new chat
            logger.info("New chat button not found, may already be in a new conversation")
            return True
        except Exception as e:
            logger.error(f"Error starting new conversation: {e}")
            if self.debug:
                self.save_screenshot("chatgpt_new_chat_error.png")
            return False
    
    def submit_prompt(self, prompt: str) -> bool:
        """
        Submit a prompt to ChatGPT.
        
        Args:
            prompt: The text prompt to submit
            
        Returns:
            True if successful, False otherwise
        """
        if not self.logged_in:
            logger.error("Not logged in to ChatGPT")
            return False
            
        try:
            # Find textarea and input the prompt
            textarea = self.wait_for_element(
                (By.XPATH, self.prompt_textarea_selector),
                condition="clickable"
            )
            textarea.clear()
            
            # Type the prompt (char by char for stability)
            for char in prompt:
                textarea.send_keys(char)
                time.sleep(0.01)  # Small delay for stability
                
            # Submit the prompt
            textarea.send_keys(Keys.RETURN)
            
            logger.info(f"Submitted prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting prompt: {e}")
            if self.debug:
                self.save_screenshot("chatgpt_submit_error.png")
            return False
    
    def is_response_complete(self) -> bool:
        """
        Check if ChatGPT has finished generating its response.
        
        Returns:
            True if the response is complete, False otherwise
        """
        try:
            # Look for the thinking indicator
            thinking_indicators = self.driver.find_elements(
                By.XPATH, self.thinking_indicator_selector
            )
            
            # Check for the "Stop generating" button
            stop_button = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Stop generating')]"
            )
            
            # Response is complete if no thinking indicators and no stop button
            response_complete = len(thinking_indicators) == 0 and len(stop_button) == 0
            
            # Check if we can find a response - if not, it might still be loading
            if response_complete:
                try:
                    self.driver.find_element(By.XPATH, self.response_container_selector)
                except NoSuchElementException:
                    # No response element found yet
                    response_complete = False
                    
            return response_complete
            
        except Exception as e:
            logger.error(f"Error checking if response is complete: {e}")
            return False
    
    def extract_response(self) -> str:
        """
        Extract the response from ChatGPT.
        
        Returns:
            The text of the response
        """
        try:
            # Wait for the response to be complete
            if not self.is_response_complete():
                self.wait_for_response_completion()
                
            # Find the response container
            response_elements = self.driver.find_elements(
                By.XPATH, self.response_container_selector
            )
            
            if not response_elements:
                logger.warning("No response elements found")
                return ""
                
            # Get the last response (most recent)
            response_text = response_elements[-1].text
            
            logger.info(f"Extracted response: {response_text[:50]}{'...' if len(response_text) > 50 else ''}")
            self.last_response_text = response_text
            return response_text
            
        except Exception as e:
            logger.error(f"Error extracting response: {e}")
            if self.debug:
                self.save_screenshot("chatgpt_extract_error.png")
            return ""
    
    def get_conversation_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the current conversation.
        
        Returns:
            Dictionary containing metadata
        """
        try:
            # Try to get conversation ID from URL
            current_url = self.driver.current_url
            conversation_id = current_url.split("/")[-1]
            
            # Get timestamp
            timestamp = datetime.now().isoformat()
            
            # Get model info if possible
            model_info = "gpt-4" if "gpt-4" in self.driver.page_source.lower() else "gpt-3.5-turbo"
            
            metadata = {
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "model": model_info,
                "platform": "chatgpt",
            }
            
            self.current_conversation_id = conversation_id
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting conversation metadata: {e}")
            return {
                "conversation_id": None,
                "timestamp": datetime.now().isoformat(),
                "platform": "chatgpt",
            }
    
    def save_response(self, prompt: str, response: str, output_file: str = None) -> Dict[str, Any]:
        """
        Save the prompt and response to a file.
        
        Args:
            prompt: The submitted prompt
            response: The response from ChatGPT
            output_file: Path to save the output
            
        Returns:
            Dictionary with saved data
        """
        metadata = self.get_conversation_metadata()
        
        data = {
            "prompt": prompt,
            "response": response,
            "metadata": metadata,
        }
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved response to {output_file}")
            except Exception as e:
                logger.error(f"Error saving response: {e}")
        
        return data
