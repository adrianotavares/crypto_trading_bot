"""
Calculator for technical indicators used in trading strategies.
"""

import logging
import pandas as pd
import pandas_ta as ta
import numpy as np

logger = logging.getLogger(__name__)

class IndicatorCalculator:
    """
    Calculates technical indicators for trading strategies.
    """
    
    def __init__(self):
        """
        Initialize the indicator calculator.
        """
        logger.info("Indicator calculator initialized")
    
    def add_moving_averages(self, df: pd.DataFrame, short_period: int = 20, 
                           medium_period: int = 50, long_period: int = 200) -> pd.DataFrame:
        """
        Add simple moving averages to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            short_period: Period for short-term SMA
            medium_period: Period for medium-term SMA
            long_period: Period for long-term SMA
            
        Returns:
            DataFrame with added moving average columns
        """
        df = df.copy()
        
        # Calculate SMAs
        df[f'SMA_{short_period}'] = ta.sma(df['Close'], length=short_period)
        df[f'SMA_{medium_period}'] = ta.sma(df['Close'], length=medium_period)
        df[f'SMA_{long_period}'] = ta.sma(df['Close'], length=long_period)
        
        # Calculate EMAs
        df[f'EMA_{short_period}'] = ta.ema(df['Close'], length=short_period)
        df[f'EMA_{medium_period}'] = ta.ema(df['Close'], length=medium_period)
        df[f'EMA_{long_period}'] = ta.ema(df['Close'], length=long_period)
        
        logger.info("Added moving averages to DataFrame")
        return df
    
    def add_rsi(self, df: pd.DataFrame, period: int = 14, 
               overbought: int = 70, oversold: int = 30) -> pd.DataFrame:
        """
        Add Relative Strength Index (RSI) to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            period: Period for RSI calculation
            overbought: Overbought threshold
            oversold: Oversold threshold
            
        Returns:
            DataFrame with added RSI columns
        """
        df = df.copy()
        
        # Calculate RSI
        df[f'RSI_{period}'] = ta.rsi(df['Close'], length=period)
        
        # Add overbought/oversold indicators
        df['RSI_Overbought'] = df[f'RSI_{period}'] > overbought
        df['RSI_Oversold'] = df[f'RSI_{period}'] < oversold
        
        logger.info("Added RSI to DataFrame")
        return df
    
    def add_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, 
                signal: int = 9) -> pd.DataFrame:
        """
        Add Moving Average Convergence Divergence (MACD) to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            fast: Fast period
            slow: Slow period
            signal: Signal period
            
        Returns:
            DataFrame with added MACD columns
        """
        df = df.copy()
        
        # Calculate MACD
        macd = ta.macd(df['Close'], fast=fast, slow=slow, signal=signal)
        
        # Add MACD columns to the DataFrame
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_Signal'] = macd['MACDs_12_26_9']
        df['MACD_Histogram'] = macd['MACDh_12_26_9']
        
        # Add MACD crossover signals
        df['MACD_Bullish_Crossover'] = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        df['MACD_Bearish_Crossover'] = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        
        logger.info("Added MACD to DataFrame")
        return df
    
    def add_bollinger_bands(self, df: pd.DataFrame, period: int = 20, 
                           std_dev: float = 2.0) -> pd.DataFrame:
        """
        Add Bollinger Bands to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            period: Period for moving average
            std_dev: Number of standard deviations
            
        Returns:
            DataFrame with added Bollinger Bands columns
        """
        df = df.copy()
        
        # Calculate Bollinger Bands
        bbands = ta.bbands(df['Close'], length=period, std=std_dev)
        
        # Add Bollinger Bands columns to the DataFrame
        df['BB_Upper'] = bbands['BBU_20_2.0']
        df['BB_Middle'] = bbands['BBM_20_2.0']
        df['BB_Lower'] = bbands['BBL_20_2.0']
        
        # Calculate Bollinger Band width
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Add Bollinger Band signals
        df['BB_Squeeze'] = df['BB_Width'] < df['BB_Width'].rolling(window=50).mean()
        df['BB_Upper_Touch'] = df['High'] >= df['BB_Upper']
        df['BB_Lower_Touch'] = df['Low'] <= df['BB_Lower']
        
        logger.info("Added Bollinger Bands to DataFrame")
        return df
    
    def add_stochastic(self, df: pd.DataFrame, k_period: int = 14, 
                      d_period: int = 3, smooth_k: int = 3) -> pd.DataFrame:
        """
        Add Stochastic Oscillator to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            k_period: K period
            d_period: D period
            smooth_k: K smoothing period
            
        Returns:
            DataFrame with added Stochastic Oscillator columns
        """
        df = df.copy()
        
        # Calculate Stochastic Oscillator
        stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=k_period, d=d_period, smooth_k=smooth_k)
        
        # Add Stochastic Oscillator columns to the DataFrame
        df['Stoch_K'] = stoch[f'STOCHk_{k_period}_{d_period}_{smooth_k}']
        df['Stoch_D'] = stoch[f'STOCHd_{k_period}_{d_period}_{smooth_k}']
        
        # Add Stochastic crossover signals
        df['Stoch_Bullish_Crossover'] = (df['Stoch_K'] > df['Stoch_D']) & (df['Stoch_K'].shift(1) <= df['Stoch_D'].shift(1))
        df['Stoch_Bearish_Crossover'] = (df['Stoch_K'] < df['Stoch_D']) & (df['Stoch_K'].shift(1) >= df['Stoch_D'].shift(1))
        
        logger.info("Added Stochastic Oscillator to DataFrame")
        return df
    
    def add_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Add Average True Range (ATR) to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            period: Period for ATR calculation
            
        Returns:
            DataFrame with added ATR column
        """
        df = df.copy()
        
        # Calculate ATR
        df[f'ATR_{period}'] = ta.atr(df['High'], df['Low'], df['Close'], length=period)
        
        logger.info("Added ATR to DataFrame")
        return df
    
    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add volume-based indicators to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added volume indicator columns
        """
        df = df.copy()
        
        # Calculate On-Balance Volume (OBV)
        df['OBV'] = ta.obv(df['Close'], df['Volume'])
        
        # Calculate Volume Moving Average
        df['Volume_SMA_20'] = ta.sma(df['Volume'], length=20)
        
        # Calculate Volume Relative to Moving Average
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
        
        # High volume signals
        df['High_Volume'] = df['Volume_Ratio'] > 1.5
        
        logger.info("Added volume indicators to DataFrame")
        return df
    
    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with all indicator columns
        """
        df = df.copy()
        
        # Add all indicators
        df = self.add_moving_averages(df)
        df = self.add_rsi(df)
        df = self.add_macd(df)
        df = self.add_bollinger_bands(df)
        df = self.add_stochastic(df)
        df = self.add_atr(df)
        df = self.add_volume_indicators(df)
        
        logger.info("Added all indicators to DataFrame")
        return df
