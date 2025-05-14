"""
Data preprocessor for cleaning and preparing market data.
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """
    Handles data cleaning and preparation for analysis.
    """
    
    def __init__(self):
        """
        Initialize the data preprocessor.
        """
        logger.debug("Data preprocessor initialized")
    
    def preprocess_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess OHLCV (Open, High, Low, Close, Volume) data.
        
        Args:
            df: DataFrame with raw OHLCV data from Binance
            
        Returns:
            Preprocessed DataFrame
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Convert types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                          'quote_asset_volume', 'taker_buy_base_asset_volume', 
                          'taker_buy_quote_asset_volume']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
        
        # Drop unnecessary columns
        columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
        extra_columns = [col for col in df.columns if col not in columns_to_keep and col != 'timestamp']
        if extra_columns:
            df.drop(columns=extra_columns, inplace=True)
        
        # Rename columns to standard format
        df.columns = [col.capitalize() for col in df.columns]
        
        # Handle missing values
        df.dropna(inplace=True)
        
        # Check for and remove duplicate indices
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        logger.debug(f"Preprocessed OHLCV data: {df.shape[0]} rows, {df.shape[1]} columns")
        return df
    
    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate percentage and logarithmic returns.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional return columns
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Calculate percentage returns
        if 'Close' in df.columns:
            df['Returns'] = df['Close'].pct_change() * 100
            df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Drop NaN values created by the returns calculation
        df.dropna(inplace=True)
        
        logger.debug("Calculated returns for price data")
        return df
    
    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize data to a 0-1 scale.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with normalized values
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Normalize OHLC data
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                df[f'{col}_Norm'] = (df[col] - min_val) / (max_val - min_val)
        
        logger.debug("Normalized price data")
        return df
