"""
StorageManager handles persistent storage of conversations, settings, and other data.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Union, Any

# DO NOT CHANGE CODE: Core storage functionality
# TEMP: Current implementation works but will be refactored later

class StorageManager:
    def __init__(self, data_dir: str = None):
        """
        Initialize the StorageManager with the data directory.
        
        Args:
            data_dir: Directory to store data
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        self.conversations_dir = os.path.join(self.data_dir, "conversations")
        self.settings_path = os.path.join(self.data_dir, "settings.json")
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.conversations_dir, exist_ok=True)
        
        # Load settings if exists, otherwise create default
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from settings.json or create default settings."""
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
                self.settings = self._create_default_settings()
        else:
            self.settings = self._create_default_settings()
            self.save_settings()
    
    def _create_default_settings(self) -> Dict:
        """
        Create default settings.
        
        Returns:
            Dictionary with default settings
        """
        return {
            "default_model": None,
            "theme": "system",
            "code_listener": {
                "enabled": True,
                "auto_execute": False,
                "languages_allowed": ["python", "javascript", "bash"]
            },
            "ui": {
                "font_size": "medium",
                "show_timestamps": True,
                "show_model_info": True,
                "max_conversation_display": 10
            },
            "advanced": {
                "max_tokens": 2048,
                "temperature": 0.7,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        }
    
    def save_settings(self) -> bool:
        """
        Save settings to settings.json.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            return False
    
    def get_settings(self) -> Dict:
        """
        Get current settings.
        
        Returns:
            Dictionary with current settings
        """
        return self.settings
    
    def update_settings(self, settings: Dict) -> bool:
        """
        Update settings with new values.
        
        Args:
            settings: Dictionary with settings to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update settings recursively
            self._update_dict_recursive(self.settings, settings)
            return self.save_settings()
        except Exception as e:
            logging.error(f"Error updating settings: {e}")
            return False
    
    def _update_dict_recursive(self, target: Dict, source: Dict):
        """
        Update a dictionary recursively.
        
        Args:
            target: Dictionary to update
            source: Dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict_recursive(target[key], value)
            else:
                target[key] = value
    
    def save_conversation(self, conversation: Dict) -> bool:
        """
        Save a conversation to disk.
        
        Args:
            conversation: Conversation to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conversation_id = conversation.get("id")
            if not conversation_id:
                logging.error("Conversation has no ID")
                return False
            
            # Create file path
            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            
            # Save conversation
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2)
            
            return True
        except Exception as e:
            logging.error(f"Error saving conversation: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Load a conversation from disk.
        
        Args:
            conversation_id: ID of the conversation to load
            
        Returns:
            Conversation dictionary or None if not found
        """
        try:
            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
            
            return conversation
        except Exception as e:
            logging.error(f"Error loading conversation {conversation_id}: {e}")
            return None
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from disk.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            
            if not os.path.exists(file_path):
                return True  # Already deleted
            
            os.remove(file_path)
            return True
        except Exception as e:
            logging.error(f"Error deleting conversation {conversation_id}: {e}")
            return False
    
    def list_conversations(self) -> List[Dict]:
        """
        List all saved conversations.
        
        Returns:
            List of conversation dictionaries
        """
        conversations = []
        
        try:
            # Get all json files in conversations directory
            for filename in os.listdir(self.conversations_dir):
                if filename.endswith(".json"):
                    try:
                        file_path = os.path.join(self.conversations_dir, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            conversation = json.load(f)
                        conversations.append(conversation)
                    except Exception as e:
                        logging.error(f"Error loading conversation file {filename}: {e}")
        except Exception as e:
            logging.error(f"Error listing conversations: {e}")
        
        # Sort by updated_at timestamp (newest first)
        conversations.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        
        return conversations
    
    def create_backup(self) -> str:
        """
        Create a backup of all data.
        
        Returns:
            Path to the backup file
        """
        try:
            import shutil
            import datetime
            
            # Generate backup filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"llm_forge_backup_{timestamp}.zip"
            backup_path = os.path.join(self.data_dir, backup_filename)
            
            # Create zip archive
            shutil.make_archive(
                os.path.splitext(backup_path)[0],
                'zip',
                self.data_dir
            )
            
            return backup_path
        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            return ""
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore data from a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import shutil
            import tempfile
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup to temp directory
                shutil.unpack_archive(backup_path, temp_dir)
                
                # Copy conversations
                backup_conversations_dir = os.path.join(temp_dir, "conversations")
                if os.path.exists(backup_conversations_dir):
                    # Clear current conversations
                    shutil.rmtree(self.conversations_dir)
                    os.makedirs(self.conversations_dir, exist_ok=True)
                    
                    # Copy backup conversations
                    for filename in os.listdir(backup_conversations_dir):
                        src_path = os.path.join(backup_conversations_dir, filename)
                        dst_path = os.path.join(self.conversations_dir, filename)
                        shutil.copy2(src_path, dst_path)
                
                # Copy settings
                backup_settings_path = os.path.join(temp_dir, "settings.json")
                if os.path.exists(backup_settings_path):
                    shutil.copy2(backup_settings_path, self.settings_path)
                
            # Reload settings
            self._load_settings()
            
            return True
        except Exception as e:
            logging.error(f"Error restoring backup: {e}")
            return False
