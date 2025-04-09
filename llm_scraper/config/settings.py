"""
Configuration settings for LLM Scraper.
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Base directories
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
CONFIG_DIR = ROOT_DIR / "config"
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Default settings
DEFAULT_SETTINGS = {
    "browser": {
        "type": "chrome",
        "headless": False,
        "timeout": 60,
        "user_data_dir": None,
    },
    "output": {
        "format": "json",
        "directory": str(OUTPUT_DIR),
        "include_metadata": True,
    },
    "models": {
        "chatgpt": {
            "url": "https://chat.openai.com/",
            "selectors": {
                "login_button": "//button[contains(text(), 'Log in')]",
                "prompt_textarea": "//textarea[@placeholder='Send a message']",
                "submit_button": "//button[@type='submit']",
                "response_container": "//div[contains(@class, 'markdown')]",
                "thinking_indicator": "//div[contains(@class, 'thinking')]",
            },
        },
        "claude": {
            "url": "https://claude.ai/",
            "selectors": {
                "login_button": "//button[contains(text(), 'Log in')]",
                "prompt_textarea": "//textarea[contains(@placeholder, 'Message')]",
                "submit_button": "//button[@type='submit']",
                "response_container": "//div[contains(@class, 'message') and contains(@class, 'assistant')]",
                "thinking_indicator": "//div[contains(@class, 'typing-indicator')]",
            },
        },
        "gemini": {
            "url": "https://gemini.google.com/app",
            "selectors": {
                "login_button": "//button[contains(text(), 'Sign in')]",
                "prompt_textarea": "//textarea[contains(@placeholder, 'Enter')]",
                "submit_button": "//button[@aria-label='Send message']",
                "response_container": "//div[contains(@class, 'response-container')]",
                "thinking_indicator": "//div[contains(@class, 'loading')]",
            },
        },
    },
    "credentials": {
        "env_prefix": "LLM_SCRAPER_",
    },
    "retry": {
        "max_attempts": 3,
        "delay": 2,
        "backoff_factor": 2,
    },
}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file and merge with defaults.
    
    Args:
        config_path: Path to custom configuration file
        
    Returns:
        Merged configuration dictionary
    """
    config = DEFAULT_SETTINGS.copy()
    
    # If a config path is provided, load and merge it
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            custom_config = yaml.safe_load(f)
            
        # Recursively merge custom config into defaults
        _merge_configs(config, custom_config)
        
    # Look for credentials in environment variables
    env_prefix = config["credentials"]["env_prefix"]
    for model in config["models"]:
        username_var = f"{env_prefix}{model.upper()}_USERNAME"
        password_var = f"{env_prefix}{model.upper()}_PASSWORD"
        
        if username_var in os.environ and password_var in os.environ:
            if "credentials" not in config["models"][model]:
                config["models"][model]["credentials"] = {}
                
            config["models"][model]["credentials"]["username"] = os.environ[username_var]
            config["models"][model]["credentials"]["password"] = os.environ[password_var]
            
    return config

def _merge_configs(base: Dict[str, Any], custom: Dict[str, Any]) -> None:
    """
    Recursively merge custom config into base config.
    
    Args:
        base: Base configuration dictionary to be updated
        custom: Custom configuration to merge in
    """
    for key, value in custom.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _merge_configs(base[key], value)
        else:
            base[key] = value

def save_config(config: Dict[str, Any], path: str) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration dictionary
        path: Path to save configuration file
    """
    # Remove sensitive information
    safe_config = config.copy()
    for model in safe_config.get("models", {}):
        if "credentials" in safe_config["models"][model]:
            safe_config["models"][model]["credentials"] = {"_redacted_": True}
    
    with open(path, 'w') as f:
        yaml.dump(safe_config, f, default_flow_style=False)

# Create default configuration file if it doesn't exist
default_config_path = CONFIG_DIR / "config.yaml"
if not default_config_path.exists():
    save_config(DEFAULT_SETTINGS, default_config_path)
