"""
Module for initializing and managing the data collection components.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import time
from datetime import datetime, timedelta

from src.data_collection.binance_data_provider import BinanceDataProvider
from src.data_collection.data_preprocessor import DataPreprocessor

logger = logging.getLogger(__name__)

class DataCollectionModule:
    """
    Manages the data collection components for the trading bot.
    """
    
    def __init__(self, config):
        """
        Initialize the data collection module.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.data_provider = BinanceDataProvider(config)
        self.preprocessor = DataPreprocessor()
        logger.info("Data collection module initialized")
    
    def get_top_trading_pairs(self, limit: int = 10) -> List[str]:
        """
        Get top trading pairs by market cap.
        
        Args:
            limit: Number of pairs to return
            
        Returns:
            List of trading pair symbols
        """
        try:
            # Get top cryptocurrencies
            top_cryptos = self.data_provider.get_top_cryptocurrencies(limit=limit)
            
            # Extract symbols
            symbols = [crypto['symbol'] for crypto in top_cryptos]
            
            logger.info(f"Retrieved top {len(symbols)} trading pairs")
            return symbols
        except Exception as e:
            logger.error(f"Error getting top trading pairs: {e}")
            return []
    
    def get_historical_data_for_pairs(self, trading_pairs: List[str], 
                                     interval: str = '1h', days: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple trading pairs.
        
        Args:
            trading_pairs: List of trading pair symbols
            interval: Candlestick interval
            days: Number of days of historical data
            
        Returns:
            Dictionary mapping symbols to their historical data DataFrames
        """
        historical_data = {}
        
        for symbol in trading_pairs:
            try:
                # Get historical data
                data = self.data_provider.get_historical_data(
                    symbol=symbol,
                    interval=interval,
                    limit=days * 24  # Approximate number of candles
                )
                
                # Preprocess data
                if not data.empty:
                    # Calculate returns
                    data = self.preprocessor.calculate_returns(data)
                    
                    # Add to result
                    historical_data[symbol] = data
                    
                    logger.info(f"Retrieved and preprocessed {len(data)} candles for {symbol}")
                else:
                    logger.warning(f"Empty data for {symbol}")
                
                # Add a small delay to avoid rate limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error getting historical data for {symbol}: {e}")
        
        return historical_data
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dictionary mapping symbols to their current prices
        """
        try:
            # Get ticker data
            ticker_data = self.data_provider.get_ticker_data(symbols=symbols)
            
            # Extract prices
            prices = {}
            for symbol, data in ticker_data.items():
                if 'lastPrice' in data:
                    prices[symbol] = float(data['lastPrice'])
            
            logger.info(f"Retrieved current prices for {len(prices)} symbols")
            return prices
        except Exception as e:
            logger.error(f"Error getting current prices: {e}")
            return {}
    
    def save_historical_data(self, data: Dict[str, pd.DataFrame], base_dir: str = None) -> None:
        """
        Save historical data to CSV files.
        
        Args:
            data: Dictionary mapping symbols to their historical data DataFrames
            base_dir: Base directory to save files (optional)
        """
        if base_dir is None:
            base_dir = self.config.get('data', 'historical_dir', 
                                      default='data/historical')
        
        try:
            import os
            from pathlib import Path
            
            # Create directory if it doesn't exist
            os.makedirs(base_dir, exist_ok=True)
            
            # Save each DataFrame to a CSV file
            for symbol, df in data.items():
                # Create filename
                timestamp = datetime.now().strftime('%Y%m%d')
                filename = f"{symbol}_{timestamp}.csv"
                filepath = Path(base_dir) / filename
                
                # Save to CSV
                df.to_csv(filepath)
                logger.info(f"Saved historical data for {symbol} to {filepath}")
                
        except Exception as e:
            logger.error(f"Error saving historical data: {e}")
    
    def load_historical_data(self, symbols: List[str], base_dir: str = None) -> Dict[str, pd.DataFrame]:
        """
        Load historical data from CSV files.
        
        Args:
            symbols: List of trading pair symbols
            base_dir: Base directory to load files from (optional)
            
        Returns:
            Dictionary mapping symbols to their historical data DataFrames
        """
        if base_dir is None:
            base_dir = self.config.get('data', 'historical_dir', 
                                      default='data/historical')
        
        try:
            import os
            from pathlib import Path
            import glob
            
            # Check if directory exists
            if not os.path.exists(base_dir):
                logger.warning(f"Historical data directory {base_dir} does not exist")
                return {}
            
            # Load data for each symbol
            data = {}
            for symbol in symbols:
                # Find the latest file for this symbol
                pattern = f"{symbol}_*.csv"
                files = glob.glob(str(Path(base_dir) / pattern))
                
                if files:
                    # Sort by filename (which includes timestamp)
                    latest_file = sorted(files)[-1]
                    
                    # Load from CSV
                    df = pd.read_csv(latest_file, index_col=0, parse_dates=True)
                    data[symbol] = df
                    logger.info(f"Loaded historical data for {symbol} from {latest_file}")
                else:
                    logger.warning(f"No historical data found for {symbol}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return {}
