"""
Configuration manager for the trading bot.
"""

import os
import logging
import yaml
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages configuration settings for the trading bot.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = {}
        
        # Load configuration
        self._load_config()
        
        logger.info(f"Configuration loaded from {config_path}")
    
    def _load_config(self) -> None:
        """
        Load configuration from file.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self.config = {}
        else:
            logger.warning(f"Configuration file not found: {self.config_path}")
            self.config = {}
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Configuration value
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def save(self) -> None:
        """
        Save configuration to file.
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configuration settings.
        
        Returns:
            All configuration settings
        """
        return self.config
