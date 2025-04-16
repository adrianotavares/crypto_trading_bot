"""
Base strategy interface for implementing trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd


class Strategy(ABC):
    """
    Abstract base class for trading strategies.
    """
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on indicators.
        
        Args:
            data: DataFrame with OHLCV data and indicators
            
        Returns:
            DataFrame with added signal columns
        """
        pass
    
    @abstractmethod
    def get_entry_points(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Get entry points for trades.
        
        Args:
            data: DataFrame with OHLCV data, indicators, and signals
            
        Returns:
            List of entry points with relevant information
        """
        pass
    
    @abstractmethod
    def get_exit_points(self, data: pd.DataFrame, position: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get exit points for trades.
        
        Args:
            data: DataFrame with OHLCV data, indicators, and signals
            position: Current position information
            
        Returns:
            List of exit points with relevant information
        """
        pass
    
    @abstractmethod
    def optimize_parameters(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Optimize strategy parameters.
        
        Args:
            data: DataFrame with OHLCV data
            **kwargs: Additional parameters for optimization
            
        Returns:
            Dictionary with optimized parameters
        """
        pass
