"""
Logger setup for the trading bot.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

def setup_logger(log_level=logging.INFO, log_to_file=True):
    """
    Set up the logger for the trading bot.
    
    Args:
        log_level: Logging level
        log_to_file: Whether to log to file
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
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
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
