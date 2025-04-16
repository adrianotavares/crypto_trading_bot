"""
Base interface for market data providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    """
    
    @abstractmethod
    def get_top_cryptocurrencies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top cryptocurrencies by market cap.
        
        Args:
            limit: Number of cryptocurrencies to return
            
        Returns:
            List of dictionaries containing cryptocurrency information
        """
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, interval: str, 
                           start_time: Optional[str] = None, 
                           end_time: Optional[str] = None,
                           limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get historical OHLCV data for a specific cryptocurrency.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1h', '1d')
            start_time: Start time in ISO format
            end_time: End time in ISO format
            limit: Maximum number of candles to return
            
        Returns:
            DataFrame with historical data
        """
        pass
    
    @abstractmethod
    def get_ticker_data(self, symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get current ticker data for specified symbols.
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dictionary mapping symbols to their ticker data
        """
        pass
    
    @abstractmethod
    def setup_websocket(self, symbols: List[str], interval: str, callback) -> Any:
        """
        Set up a websocket connection for real-time data.
        
        Args:
            symbols: List of trading pair symbols
            interval: Time interval for kline data
            callback: Callback function to handle incoming data
            
        Returns:
            Websocket connection object
        """
        pass
