"""
Command line interface for LLM Scraper.
"""
import os
import sys
import argparse
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml
import csv

from .config.settings import load_config
from .models.chatgpt.scraper import ChatGPTScraper
from .models.claude.scraper import ClaudeScraper
from .models.gemini.scraper import GeminiScraper
from .utils.data_processor import DataProcessor
from .utils.logger import setup_logger

logger = setup_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LLM Scraper - Collect and compare responses from web-based LLMs"
    )
    
    # Main arguments
    parser.add_argument(
        "--model", 
        type=str, 
        choices=["web/chatgpt", "web/claude", "web/gemini", "all"],
        help="LLM model to use"
    )
    
    parser.add_argument(
        "--prompt", 
        type=str,
        help="Prompt to submit to the LLM"
    )
    
    parser.add_argument(
        "--prompt-file", 
        type=str,
        help="File containing the prompt to submit"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="output",
        help="Directory to save output files"
    )
    
    parser.add_argument(
        "--output-format", 
        type=str, 
        choices=["json", "csv", "md", "txt"], 
        default="json",
        help="Output file format"
    )
    
    parser.add_argument(
        "--config", 
        type=str,
        help="Path to configuration file"
    )
    
    # Browser options
    parser.add_argument(
        "--headless", 
        action="store_true",
        help="Run browser in headless mode"
    )
    
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=60,
        help="Timeout for browser operations in seconds"
    )
    
    parser.add_argument(
        "--user-data-dir", 
        type=str,
        help="Path to browser user data directory"
    )
    
    # Credentials
    parser.add_argument(
        "--credentials-file", 
        type=str,
        help="Path to credentials file (JSON format)"
    )
    
    # Debug options
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--batch", 
        type=str,
        help="Path to batch file with multiple prompts (JSON or CSV)"
    )
    
    parser.add_argument(
        "--compare", 
        action="store_true",
        help="Compare responses when using 'all' or batch mode"
    )
    
    return parser.parse_args()

def load_prompt(prompt_arg: Optional[str], prompt_file: Optional[str]) -> str:
    """
    Load prompt from argument or file.
    
    Args:
        prompt_arg: Prompt text from command line
        prompt_file: Path to file containing prompt
        
    Returns:
        Prompt text
    """
    if prompt_arg:
        return prompt_arg
        
    if prompt_file:
        if not os.path.exists(prompt_file):
            logger.error(f"Prompt file not found: {prompt_file}")
            sys.exit(1)
            
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading prompt file: {e}")
            sys.exit(1)
    
    logger.error("No prompt provided. Use --prompt or --prompt-file")
    sys.exit(1)

def load_credentials(credentials_file: Optional[str], config: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Load credentials from file or environment variables.
    
    Args:
        credentials_file: Path to credentials file
        config: Configuration dictionary
        
    Returns:
        Dictionary of credentials by model
    """
    credentials = {}
    
    # Try to load from file first
    if credentials_file:
        if not os.path.exists(credentials_file):
            logger.error(f"Credentials file not found: {credentials_file}")
            sys.exit(1)
            
        try:
            with open(credentials_file, 'r', encoding='utf-8') as f:
                file_creds = json.load(f)
                credentials.update(file_creds)
        except Exception as e:
            logger.error(f"Error reading credentials file: {e}")
            sys.exit(1)
    
    # Check for credentials in config
    for model in config.get("models", {}):
        if "credentials" in config["models"][model]:
            credentials[model] = config["models"][model]["credentials"]
    
    # Check environment variables as fallback
    env_prefix = config.get("credentials", {}).get("env_prefix", "LLM_SCRAPER_")
    for model in ["chatgpt", "claude", "gemini"]:
        username_var = f"{env_prefix}{model.upper()}_USERNAME"
        password_var = f"{env_prefix}{model.upper()}_PASSWORD"
        
        if username_var in os.environ and password_var in os.environ:
            credentials[model] = {
                "username": os.environ[username_var],
                "password": os.environ[password_var]
            }
    
    return credentials

def load_batch_prompts(batch_file: str) -> List[str]:
    """
    Load batch prompts from a file.
    
    Args:
        batch_file: Path to batch file (JSON or CSV)
        
    Returns:
        List of prompts
    """
    if not os.path.exists(batch_file):
        logger.error(f"Batch file not found: {batch_file}")
        sys.exit(1)
        
    prompts = []
    
    try:
        # Determine file type from extension
        if batch_file.endswith('.json'):
            with open(batch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle different JSON formats
                if isinstance(data, list):
                    # If it's a list of strings
                    if all(isinstance(item, str) for item in data):
                        prompts = data
                    # If it's a list of dicts with a 'prompt' field
                    elif all(isinstance(item, dict) and 'prompt' in item for item in data):
                        prompts = [item['prompt'] for item in data]
                    else:
                        raise ValueError("JSON file must contain a list of strings or objects with 'prompt' field")
                elif isinstance(data, dict) and 'prompts' in data:
                    # If it's a dict with a 'prompts' field
                    prompts = data['prompts']
                else:
                    raise ValueError("JSON file format not recognized")
                    
        elif batch_file.endswith('.csv'):
            with open(batch_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Find prompt column
                prompt_col = None
                for i, col in enumerate(header):
                    if col.lower() in ['prompt', 'question', 'text', 'input']:
                        prompt_col = i
                        break
                
                if prompt_col is None:
                    # Assume first column
                    prompt_col = 0
                    
                # Read prompts from column
                for row in reader:
                    if len(row) > prompt_col:
                        prompts.append(row[prompt_col])
                        
        else:
            # Assume text file with one prompt per line
            with open(batch_file, 'r', encoding='utf-8') as f:
                prompts = [line.strip() for line in f if line.strip()]
    
    except Exception as e:
        logger.error(f"Error loading batch file: {e}")
        sys.exit(1)
        
    if not prompts:
        logger.error("No prompts found in batch file")
        sys.exit(1)
        
    return prompts

def get_scraper(model: str, args: argparse.Namespace, config: Dict[str, Any]) -> Any:
    """
    Get the appropriate scraper for the model.
    
    Args:
        model: Model identifier (chatgpt, claude, gemini)
        args: Command line arguments
        config: Configuration dictionary
        
    Returns:
        Initialized scraper instance
    """
    # Convert web/model format to just model name
    model_name = model.split('/')[-1] if '/' in model else model
    
    # Common parameters
    params = {
        "headless": args.headless,
        "timeout": args.timeout,
        "user_data_dir": args.user_data_dir,
        "debug": args.debug,
        "config": config,
    }
    
    if model_name == "chatgpt":
        return ChatGPTScraper(**params)
    elif model_name == "claude":
        return ClaudeScraper(**params)
    elif model_name == "gemini":
        return GeminiScraper(**params)
    else:
        logger.error(f"Unknown model: {model}")
        sys.exit(1)

def process_prompt(
    model: str, 
    prompt: str, 
    credentials: Dict[str, Dict[str, str]],
    processor: DataProcessor,
    args: argparse.Namespace,
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Process a single prompt with the specified model.
    
    Args:
        model: Model identifier
        prompt: Prompt text
        credentials: Credentials dictionary
        processor: DataProcessor instance
        args: Command line arguments
        config: Configuration dictionary
        
    Returns:
        Response data or None if failed
    """
    # Convert web/model format to just model name
    model_name = model.split('/')[-1] if '/' in model else model
    
    logger.info(f"Processing prompt with {model_name}")
    
    # Get model credentials
    model_creds = credentials.get(model_name)
    if not model_creds:
        logger.error(f"No credentials found for {model_name}")
        return None
    
    # Get scraper
    scraper = get_scraper(model, args, config)
    
    try:
        with scraper:
            # Login
            if not scraper.login(model_creds):
                logger.error(f"Failed to log in to {model_name}")
                return None
            
            # Start new conversation
            scraper.start_new_conversation()
            
            # Submit prompt
            if not scraper.submit_prompt(prompt):
                logger.error(f"Failed to submit prompt to {model_name}")
                return None
            
            # Wait for and extract response
            response = scraper.extract_response()
            
            if not response:
                logger.error(f"Failed to extract response from {model_name}")
                return None
            
            # Save the response
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{model_name}_{timestamp}.{args.output_format}"
            filepath = os.path.join(args.output_dir, filename)
            
            # Get response data
            data = scraper.save_response(prompt, response, filepath)
            
            logger.info(f"Successfully processed prompt with {model_name}")
            return data
    
    except Exception as e:
        logger.error(f"Error processing prompt with {model_name}: {e}")
        return None

def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.headless:
        config["browser"]["headless"] = True
    
    if args.timeout:
        config["browser"]["timeout"] = args.timeout
        
    if args.user_data_dir:
        config["browser"]["user_data_dir"] = args.user_data_dir
        
    if args.output_dir:
        config["output"]["directory"] = args.output_dir
        
    if args.output_format:
        config["output"]["format"] = args.output_format
    
    # Initialize data processor
    processor = DataProcessor(output_dir=config["output"]["directory"])
    
    # Load credentials
    credentials = load_credentials(args.credentials_file, config)
    
    # No model specified
    if not args.model:
        logger.error("No model specified. Use --model")
        sys.exit(1)
    
    # Process batch file
    if args.batch:
        prompts = load_batch_prompts(args.batch)
        logger.info(f"Loaded {len(prompts)} prompts from batch file")
        
        responses_by_prompt = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"Processing prompt {i+1}/{len(prompts)}")
            
            if args.model == "all":
                # Process with all models
                prompt_responses = []
                
                for model in ["web/chatgpt", "web/claude", "web/gemini"]:
                    response_data = process_prompt(
                        model, prompt, credentials, processor, args, config
                    )
                    
                    if response_data:
                        prompt_responses.append(response_data)
                    
                if args.compare and len(prompt_responses) > 1:
                    # Compare responses
                    comparison = processor.compare_responses(prompt_responses)
                    
                    # Save comparison
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    comparison_file = f"comparison_prompt_{i+1}_{timestamp}.json"
                    processor.save_comparison(comparison, os.path.join(args.output_dir, comparison_file))
                
                responses_by_prompt.append(prompt_responses)
            else:
                # Process with single model
                response_data = process_prompt(
                    args.model, prompt, credentials, processor, args, config
                )
                
                if response_data:
                    responses_by_prompt.append([response_data])
        
        logger.info(f"Processed {len(prompts)} prompts")
        return
    
    # Process single prompt
    prompt = load_prompt(args.prompt, args.prompt_file)
    
    if args.model == "all":
        # Process with all models
        responses = []
        
        for model in ["web/chatgpt", "web/claude", "web/gemini"]:
            response_data = process_prompt(
                model, prompt, credentials, processor, args, config
            )
            
            if response_data:
                responses.append(response_data)
        
        if args.compare and len(responses) > 1:
            # Compare responses
            comparison = processor.compare_responses(responses)
            
            # Save comparison
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            comparison_file = f"comparison_{timestamp}.json"
            processor.save_comparison(comparison, os.path.join(args.output_dir, comparison_file))
            
            logger.info(f"Comparison saved to {comparison_file}")
    else:
        # Process with single model
        process_prompt(
            args.model, prompt, credentials, processor, args, config
        )

if __name__ == "__main__":
    main()
