"""
Tests for the LLM scrapers.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
from pathlib import Path

# Ensure that parent directory is in path for relative imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm_scraper.models.chatgpt.scraper import ChatGPTScraper
from llm_scraper.models.claude.scraper import ClaudeScraper
from llm_scraper.models.gemini.scraper import GeminiScraper
from llm_scraper.config.settings import load_config


class TestScrapers(unittest.TestCase):
    """Tests for scraper classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = load_config()
        
    @patch('selenium.webdriver.Chrome')
    def test_chatgpt_scraper_init(self, mock_chrome):
        """Test ChatGPT scraper initialization."""
        # Mock the Chrome webdriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Initialize the scraper
        scraper = ChatGPTScraper(
            headless=True, 
            timeout=30, 
            debug=True,
            config=self.config
        )
        
        # Assert the scraper was initialized correctly
        self.assertTrue(scraper.headless)
        self.assertEqual(scraper.timeout, 30)
        self.assertTrue(scraper.debug)
        
    @patch('selenium.webdriver.Chrome')
    def test_claude_scraper_init(self, mock_chrome):
        """Test Claude scraper initialization."""
        # Mock the Chrome webdriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Initialize the scraper
        scraper = ClaudeScraper(
            headless=True, 
            timeout=30, 
            debug=True,
            config=self.config
        )
        
        # Assert the scraper was initialized correctly
        self.assertTrue(scraper.headless)
        self.assertEqual(scraper.timeout, 30)
        self.assertTrue(scraper.debug)
        
    @patch('selenium.webdriver.Chrome')
    def test_gemini_scraper_init(self, mock_chrome):
        """Test Gemini scraper initialization."""
        # Mock the Chrome webdriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Initialize the scraper
        scraper = GeminiScraper(
            headless=True, 
            timeout=30, 
            debug=True,
            config=self.config
        )
        
        # Assert the scraper was initialized correctly
        self.assertTrue(scraper.headless)
        self.assertEqual(scraper.timeout, 30)
        self.assertTrue(scraper.debug)
        

if __name__ == "__main__":
    unittest.main()
