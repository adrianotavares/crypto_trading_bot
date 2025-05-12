"""
Logger setup for the trading bot.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path


class ColorFormatter(logging.Formatter):
    # Define ANSI escape codes for colors
    COLORS = {
        "INFO": "\033[92m",   # Green
        "ERROR": "\033[91m",  # Red
        "WARNING": "\033[93m", # Yellow
        "DEBUG": "\033[94m",  # Blue
        "RESET": "\033[0m"    # Reset to default
    }

    def format(self, record):
        # Apply color based on the log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        message = super().format(record)
        return f"{color}{message}{self.COLORS['RESET']}"

def setup_logger(log_level, log_to_file):
    """
    Set up the logger for the trading bot.
    
    Args:
        log_level: Logging level
        log_to_file: Whether to log to file
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # if DEBUG format complete else only messages
    if log_level == "DEBUG":
        logger.setLevel(logging.DEBUG)
        formatter = ColorFormatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    else:
        logger.setLevel(logging.INFO)
        formatter = ColorFormatter('%(levelname)s - %(message)s')
    
    # Create console handler
    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)
    
    # Create console handler with color formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if needed
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent.parent / "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        log_file = log_dir / "trading_bot.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
        logger.addHandler(file_handler)
    
    return logger
