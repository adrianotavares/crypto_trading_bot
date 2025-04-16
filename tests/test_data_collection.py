"""
Test script for the data collection module.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.config_manager import ConfigManager
from src.logging.logger import setup_logger
from src.data_collection.binance_data_provider import BinanceDataProvider
from src.data_collection.data_preprocessor import DataPreprocessor

def test_data_collection():
    """
    Test the data collection module.
    """
    # Setup logging
    setup_logger(log_level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting data collection test...")

    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    config = ConfigManager(config_path)
    
    # Initialize components
    data_provider = BinanceDataProvider(config)
    preprocessor = DataPreprocessor()
    
    # Test getting top cryptocurrencies
    try:
        logger.info("Testing get_top_cryptocurrencies...")
        top_cryptos = data_provider.get_top_cryptocurrencies(limit=10)
        logger.info(f"Top cryptocurrencies: {[crypto['symbol'] for crypto in top_cryptos]}")
        
        if not top_cryptos:
            logger.error("Failed to get top cryptocurrencies")
            return False
        
        logger.info("get_top_cryptocurrencies test passed")
    except Exception as e:
        logger.error(f"Error in get_top_cryptocurrencies: {e}")
        return False
    
    # Test getting historical data
    try:
        logger.info("Testing get_historical_data...")
        symbol = top_cryptos[0]['symbol']
        historical_data = data_provider.get_historical_data(
            symbol=symbol,
            interval='1h',
            limit=100
        )
        
        logger.info(f"Historical data for {symbol}: {len(historical_data)} candles")
        logger.info(f"Columns: {historical_data.columns.tolist()}")
        logger.info(f"Sample data:\n{historical_data.head()}")
        
        if historical_data.empty:
            logger.error("Failed to get historical data")
            return False
        
        logger.info("get_historical_data test passed")
    except Exception as e:
        logger.error(f"Error in get_historical_data: {e}")
        return False
    
    # Test data preprocessing
    try:
        logger.info("Testing data preprocessing...")
        
        # Calculate returns
        data_with_returns = preprocessor.calculate_returns(historical_data)
        logger.info(f"Data with returns: {data_with_returns.columns.tolist()}")
        
        # Normalize data
        normalized_data = preprocessor.normalize_data(historical_data)
        logger.info(f"Normalized data: {normalized_data.columns.tolist()}")
        
        logger.info("Data preprocessing test passed")
    except Exception as e:
        logger.error(f"Error in data preprocessing: {e}")
        return False
    
    # Test getting ticker data
    try:
        logger.info("Testing get_ticker_data...")
        symbols = [crypto['symbol'] for crypto in top_cryptos[:3]]
        ticker_data = data_provider.get_ticker_data(symbols=symbols)
        
        logger.info(f"Ticker data for {symbols}: {len(ticker_data)} symbols")
        
        if not ticker_data:
            logger.error("Failed to get ticker data")
            return False
        
        logger.info("get_ticker_data test passed")
    except Exception as e:
        logger.error(f"Error in get_ticker_data: {e}")
        return False
    
    logger.info("All data collection tests passed!")
    return True

if __name__ == "__main__":
    test_data_collection()
