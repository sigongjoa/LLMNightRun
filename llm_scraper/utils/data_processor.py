"""
Data processing utilities for LLM Scraper.
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import csv
import pandas as pd
from pathlib import Path

from .logger import setup_logger

logger = setup_logger(__name__)

class DataProcessor:
    """
    Process and format data from LLM scraping operations.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the data processor.
        
        Args:
            output_dir: Directory to store output files
        """
        self.output_dir = output_dir or os.path.join(os.getcwd(), "output")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def save_response(
        self, 
        prompt: str, 
        response: str, 
        metadata: Dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None
    ) -> str:
        """
        Save a response to a file.
        
        Args:
            prompt: The prompt text
            response: The LLM's response
            metadata: Dictionary of metadata
            format: Output format (json, csv, md, txt)
            filename: Optional custom filename
            
        Returns:
            Path to the saved file
        """
        # Create data structure
        data = {
            "prompt": prompt,
            "response": response,
            "metadata": metadata,
        }
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = metadata.get("model", "unknown")
            platform = metadata.get("platform", "unknown")
            filename = f"{platform}_{model_name}_{timestamp}"
            
        # Ensure filename has correct extension
        if not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
            
        filepath = os.path.join(self.output_dir, filename)
        
        # Save in specified format
        if format == "json":
            self._save_json(data, filepath)
        elif format == "csv":
            self._save_csv(data, filepath)
        elif format == "md":
            self._save_markdown(data, filepath)
        elif format == "txt":
            self._save_text(data, filepath)
        else:
            logger.warning(f"Unsupported format: {format}, defaulting to JSON")
            filepath = filepath.replace(f".{format}", ".json")
            self._save_json(data, filepath)
            
        logger.info(f"Saved data to {filepath}")
        return filepath
    
    def _save_json(self, data: Dict[str, Any], filepath: str) -> None:
        """
        Save data as JSON.
        
        Args:
            data: The data to save
            filepath: Path to save the file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            raise
    
    def _save_csv(self, data: Dict[str, Any], filepath: str) -> None:
        """
        Save data as CSV.
        
        Args:
            data: The data to save
            filepath: Path to save the file
        """
        try:
            # Flatten metadata into columns
            row = {
                "prompt": data["prompt"],
                "response": data["response"],
            }
            
            # Add metadata fields
            for key, value in data["metadata"].items():
                row[f"metadata_{key}"] = value
                
            # Write to CSV
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writeheader()
                writer.writerow(row)
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            raise
    
    def _save_markdown(self, data: Dict[str, Any], filepath: str) -> None:
        """
        Save data as Markdown.
        
        Args:
            data: The data to save
            filepath: Path to save the file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write metadata
                f.write("# LLM Response\n\n")
                f.write("## Metadata\n\n")
                
                for key, value in data["metadata"].items():
                    f.write(f"- **{key}**: {value}\n")
                    
                # Write prompt and response
                f.write("\n## Prompt\n\n")
                f.write(data["prompt"])
                
                f.write("\n\n## Response\n\n")
                f.write(data["response"])
        except Exception as e:
            logger.error(f"Error saving Markdown: {e}")
            raise
    
    def _save_text(self, data: Dict[str, Any], filepath: str) -> None:
        """
        Save data as plain text.
        
        Args:
            data: The data to save
            filepath: Path to save the file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write metadata
                f.write("=== LLM Response ===\n\n")
                f.write("=== Metadata ===\n")
                
                for key, value in data["metadata"].items():
                    f.write(f"{key}: {value}\n")
                    
                # Write prompt and response
                f.write("\n=== Prompt ===\n\n")
                f.write(data["prompt"])
                
                f.write("\n\n=== Response ===\n\n")
                f.write(data["response"])
        except Exception as e:
            logger.error(f"Error saving text: {e}")
            raise
    
    def load_responses(self, directory: str = None, format: str = "json") -> List[Dict[str, Any]]:
        """
        Load responses from files in a directory.
        
        Args:
            directory: Directory containing response files
            format: File format to load
            
        Returns:
            List of response data dictionaries
        """
        directory = directory or self.output_dir
        
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return []
            
        responses = []
        
        if format == "json":
            # Find all JSON files
            json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
            
            for file in json_files:
                try:
                    with open(os.path.join(directory, file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        responses.append(data)
                except Exception as e:
                    logger.error(f"Error loading {file}: {e}")
        
        elif format == "csv":
            # Find all CSV files
            csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
            
            for file in csv_files:
                try:
                    df = pd.read_csv(os.path.join(directory, file), encoding='utf-8')
                    
                    # Convert each row to dictionary
                    for _, row in df.iterrows():
                        data = row.to_dict()
                        
                        # Reorganize metadata
                        metadata = {}
                        regular_fields = []
                        
                        for key, value in data.items():
                            if key.startswith("metadata_"):
                                meta_key = key.replace("metadata_", "")
                                metadata[meta_key] = value
                            else:
                                regular_fields.append(key)
                                
                        response_data = {
                            "prompt": data.get("prompt", ""),
                            "response": data.get("response", ""),
                            "metadata": metadata
                        }
                        
                        responses.append(response_data)
                except Exception as e:
                    logger.error(f"Error loading {file}: {e}")
        else:
            logger.warning(f"Loading format {format} not supported")
            
        return responses
    
    def compare_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple responses, typically for the same prompt across different models.
        
        Args:
            responses: List of response data dictionaries
            
        Returns:
            Dictionary with comparison metrics and analysis
        """
        if not responses:
            return {"error": "No responses to compare"}
            
        # Extract key information
        comparison = {
            "prompt": responses[0]["prompt"],
            "responses": [],
            "metadata": {
                "comparison_time": datetime.now().isoformat(),
                "num_responses": len(responses)
            },
            "metrics": {}
        }
        
        # Process each response
        for response in responses:
            model_info = {
                "model": response["metadata"].get("model", "unknown"),
                "platform": response["metadata"].get("platform", "unknown"),
                "response_text": response["response"],
                "timestamp": response["metadata"].get("timestamp", "unknown")
            }
            
            comparison["responses"].append(model_info)
            
        # Calculate basic metrics
        # Word count
        for resp in comparison["responses"]:
            resp["word_count"] = len(resp["response_text"].split())
            resp["char_count"] = len(resp["response_text"])
            
        # Calculate averages
        avg_word_count = sum(r["word_count"] for r in comparison["responses"]) / len(comparison["responses"])
        comparison["metrics"]["avg_word_count"] = avg_word_count
        
        # Find min and max length responses
        min_words = min(comparison["responses"], key=lambda x: x["word_count"])
        max_words = max(comparison["responses"], key=lambda x: x["word_count"])
        
        comparison["metrics"]["min_words"] = {
            "model": min_words["model"],
            "platform": min_words["platform"],
            "word_count": min_words["word_count"]
        }
        
        comparison["metrics"]["max_words"] = {
            "model": max_words["model"],
            "platform": max_words["platform"],
            "word_count": max_words["word_count"]
        }
        
        return comparison
    
    def save_comparison(self, comparison: Dict[str, Any], filepath: str = None) -> str:
        """
        Save a comparison of multiple responses.
        
        Args:
            comparison: Comparison data dictionary
            filepath: Path to save the file
            
        Returns:
            Path to the saved file
        """
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.output_dir, f"comparison_{timestamp}.json")
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved comparison to {filepath}")
        except Exception as e:
            logger.error(f"Error saving comparison: {e}")
            raise
            
        return filepath
