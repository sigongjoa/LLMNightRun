"""
Claude web interface scraper implementation.
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

class ClaudeScraper(BaseScraper):
    """
    Scraper for the Claude web interface.
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
        Initialize the Claude scraper.
        
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
        self.model_config = self.config.get("models", {}).get("claude", {})
        self.url = self.model_config.get("url", "https://claude.ai/")
        self.selectors = self.model_config.get("selectors", {})
        
        # Default selectors if not provided in config
        self.login_button_selector = self.selectors.get(
            "login_button", "//button[contains(text(), 'Continue with')]"
        )
        self.prompt_textarea_selector = self.selectors.get(
            "prompt_textarea", "//div[@role='textbox']"
        )
        self.submit_button_selector = self.selectors.get(
            "submit_button", "//button[@aria-label='Send message']"
        )
        self.response_container_selector = self.selectors.get(
            "response_container", "//div[contains(@class, 'claude-response')]"
        )
        self.thinking_indicator_selector = self.selectors.get(
            "thinking_indicator", "//div[contains(@class, 'typing-indicator')]"
        )
        
        self.last_response_text = ""
        self.current_conversation_id = None
    
    def login(self, credentials: Dict[str, str]) -> bool:
        """
        Log in to Claude web interface.
        
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
                new_chat_btn = self.wait_for_element(
                    (By.XPATH, "//button[contains(text(), 'New chat')]"), 
                    timeout=5
                )
                logger.info("Already logged in to Claude")
                self.logged_in = True
                return True
            except TimeoutException:
                # Not logged in, continue with login process
                logger.info("Not logged in, proceeding with login")
            
            # Claude uses OAuth for login (Google, Apple, etc.)
            # Click continue with Google/Email
            login_options = self.driver.find_elements(
                By.XPATH, self.login_button_selector
            )
            
            if not login_options:
                logger.error("No login options found")
                return False
                
            # Prefer email login if available
            email_login = None
            for option in login_options:
                if "email" in option.text.lower():
                    email_login = option
                    break
                    
            # Otherwise use the first option (usually Google)
            login_button = email_login or login_options[0]
            login_button.click()
            
            # Handle email login flow
            if email_login:
                # Wait for email input
                email_input = self.wait_for_element(
                    (By.XPATH, "//input[@type='email']"), 
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
                    (By.XPATH, "//input[@type='password']"), 
                    condition="visible"
                )
                password_input.send_keys(credentials.get("password", ""))
                
                # Click login
                login_submit = self.wait_for_element(
                    (By.XPATH, "//button[@type='submit']"), 
                    condition="clickable"
                )
                login_submit.click()
            else:
                # Google login flow - more complex and may require manual steps
                logger.warning("Google login flow selected - may require manual intervention")
                
                # Wait for Google login page
                email_input = self.wait_for_element(
                    (By.XPATH, "//input[@type='email']"), 
                    condition="visible"
                )
                email_input.send_keys(credentials.get("username", ""))
                
                # Click next
                next_button = self.wait_for_element(
                    (By.XPATH, "//button[contains(text(), 'Next') or contains(@id, 'Next')]"), 
                    condition="clickable"
                )
                next_button.click()
                
                # Wait for password input
                password_input = self.wait_for_element(
                    (By.XPATH, "//input[@type='password']"), 
                    condition="visible"
                )
                password_input.send_keys(credentials.get("password", ""))
                
                # Click next/sign in
                sign_in_button = self.wait_for_element(
                    (By.XPATH, "//button[contains(text(), 'Next') or contains(@id, 'signIn')]"), 
                    condition="clickable"
                )
                sign_in_button.click()
            
            # Wait for the chat interface to load
            self.wait_for_element(
                (By.XPATH, "//button[contains(text(), 'New chat')]"), 
                timeout=30,
                condition="visible"
            )
            
            logger.info("Successfully logged in to Claude")
            self.logged_in = True
            return True
            
        except TimeoutException as e:
            logger.error(f"Timeout during login: {e}")
            if self.debug:
                self.save_screenshot("claude_login_timeout.png")
            return False
        except Exception as e:
            logger.error(f"Error during login: {e}")
            if self.debug:
                self.save_screenshot("claude_login_error.png")
            return False
    
    def start_new_conversation(self) -> bool:
        """
        Start a new conversation in Claude.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Click the New Chat button
            new_chat_button = self.wait_for_element(
                (By.XPATH, "//button[contains(text(), 'New chat')]"), 
                timeout=5,
                condition="clickable"
            )
            new_chat_button.click()
            
            # Wait for the textarea to be ready
            self.wait_for_element(
                (By.XPATH, self.prompt_textarea_selector), 
                condition="visible"
            )
            
            logger.info("Started new conversation in Claude")
            return True
            
        except TimeoutException:
            logger.warning("New chat button not found")
            return False
        except Exception as e:
            logger.error(f"Error starting new conversation: {e}")
            if self.debug:
                self.save_screenshot("claude_new_chat_error.png")
            return False
    
    def submit_prompt(self, prompt: str) -> bool:
        """
        Submit a prompt to Claude.
        
        Args:
            prompt: The text prompt to submit
            
        Returns:
            True if successful, False otherwise
        """
        if not self.logged_in:
            logger.error("Not logged in to Claude")
            return False
            
        try:
            # Find textarea and input the prompt
            textarea = self.wait_for_element(
                (By.XPATH, self.prompt_textarea_selector),
                condition="clickable"
            )
            
            # Clear any existing text and focus
            textarea.click()
            
            # Type the prompt
            textarea.send_keys(prompt)
            
            # Submit the prompt
            submit_button = self.wait_for_element(
                (By.XPATH, self.submit_button_selector),
                condition="clickable"
            )
            submit_button.click()
            
            logger.info(f"Submitted prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting prompt: {e}")
            if self.debug:
                self.save_screenshot("claude_submit_error.png")
            return False
    
    def is_response_complete(self) -> bool:
        """
        Check if Claude has finished generating its response.
        
        Returns:
            True if the response is complete, False otherwise
        """
        try:
            # Look for the thinking indicator
            thinking_indicators = self.driver.find_elements(
                By.XPATH, self.thinking_indicator_selector
            )
            
            # Also check for "Stop generating" button
            stop_button = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Stop generating')]"
            )
            
            # Claude shows a progress bar - check if that's visible
            progress_bar = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'progress')]"
            )
            
            # Response is complete if no thinking indicators, no stop button, and no progress bar
            response_complete = (
                len(thinking_indicators) == 0 and 
                len(stop_button) == 0 and 
                len(progress_bar) == 0
            )
            
            # Check if we can find a response too
            if response_complete:
                try:
                    response_elements = self.driver.find_elements(
                        By.XPATH, self.response_container_selector
                    )
                    if not response_elements:
                        response_complete = False
                except Exception:
                    response_complete = False
                    
            return response_complete
            
        except Exception as e:
            logger.error(f"Error checking if response is complete: {e}")
            return False
    
    def extract_response(self) -> str:
        """
        Extract the response from Claude.
        
        Returns:
            The text of the response
        """
        try:
            # Wait for the response to be complete
            if not self.is_response_complete():
                self.wait_for_response_completion()
                
            # Find the response container - Claude's response is usually the last one in the chat
            response_elements = self.driver.find_elements(
                By.XPATH, self.response_container_selector
            )
            
            if not response_elements:
                logger.warning("No response elements found")
                return ""
                
            # Get the last response
            response_text = response_elements[-1].text
            
            logger.info(f"Extracted response: {response_text[:50]}{'...' if len(response_text) > 50 else ''}")
            self.last_response_text = response_text
            return response_text
            
        except Exception as e:
            logger.error(f"Error extracting response: {e}")
            if self.debug:
                self.save_screenshot("claude_extract_error.png")
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
            
            # Try to determine Claude model version
            model_info = "claude-3"  # Default assumption
            
            # Try to find model selector dropdown to get exact model
            model_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'model-selector')]"
            )
            
            if model_elements:
                model_text = model_elements[0].text
                if "opus" in model_text.lower():
                    model_info = "claude-3-opus"
                elif "sonnet" in model_text.lower():
                    model_info = "claude-3-sonnet"
                elif "haiku" in model_text.lower():
                    model_info = "claude-3-haiku"
            
            metadata = {
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "model": model_info,
                "platform": "claude",
            }
            
            self.current_conversation_id = conversation_id
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting conversation metadata: {e}")
            return {
                "conversation_id": None,
                "timestamp": datetime.now().isoformat(),
                "platform": "claude",
            }
    
    def save_response(self, prompt: str, response: str, output_file: str = None) -> Dict[str, Any]:
        """
        Save the prompt and response to a file.
        
        Args:
            prompt: The submitted prompt
            response: The response from Claude
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
