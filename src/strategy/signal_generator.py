"""
Signal generator for trading strategies.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class SignalGenerator:
    """
    Generates trading signals based on strategy analysis.
    """
    
    def __init__(self, config):
        """
        Initialize the signal generator.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.signal_threshold = config.get('strategy', 'signal_threshold', default=3)
        logger.info(f"Signal generator initialized with threshold: {self.signal_threshold}")
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on indicator values.
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            DataFrame with added signal columns
        """
        df = df.copy()
        
        # Initialize signal columns
        df['Buy_Signal'] = False
        df['Sell_Signal'] = False
        df['Signal_Strength'] = 0  # Scale from -5 to 5
        
        # Calculate signal strength based on indicators
        self._calculate_signal_strength(df)
        
        # Generate final signals based on signal strength
        df['Buy_Signal'] = df['Signal_Strength'] >= self.signal_threshold
        df['Sell_Signal'] = df['Signal_Strength'] <= -self.signal_threshold
        
        # Add signal metadata
        df['Signal_Type'] = np.where(df['Buy_Signal'], 'buy', 
                                    np.where(df['Sell_Signal'], 'sell', 'neutral'))
        
        logger.info(f"Generated signals: {df['Buy_Signal'].sum()} buy, {df['Sell_Signal'].sum()} sell")
        return df
    
    def _calculate_signal_strength(self, df: pd.DataFrame) -> None:
        """
        Calculate signal strength based on various indicators.
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            None (modifies df in-place)
        """
        # RSI signals
        if 'RSI_14' in df.columns:
            df['Signal_Strength'] += np.where(df['RSI_14'] < 30, 1, 0)  # Oversold (buy)
            df['Signal_Strength'] -= np.where(df['RSI_14'] > 70, 1, 0)  # Overbought (sell)
        
        # MACD signals
        if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
            # Bullish crossover (MACD crosses above signal line)
            bullish_crossover = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
            df['Signal_Strength'] += np.where(bullish_crossover, 1, 0)
            
            # Bearish crossover (MACD crosses below signal line)
            bearish_crossover = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
            df['Signal_Strength'] -= np.where(bearish_crossover, 1, 0)
        
        # Bollinger Bands signals
        if all(col in df.columns for col in ['BB_Lower', 'BB_Upper', 'Close']):
            # Price touches lower band (potential buy)
            df['Signal_Strength'] += np.where(df['Low'] <= df['BB_Lower'], 1, 0)
            
            # Price touches upper band (potential sell)
            df['Signal_Strength'] -= np.where(df['High'] >= df['BB_Upper'], 1, 0)
        
        # Moving Average signals
        for ma_pair in [('SMA_20', 'SMA_50'), ('EMA_20', 'EMA_50')]:
            short_ma, long_ma = ma_pair
            if all(col in df.columns for col in [short_ma, long_ma]):
                # Bullish crossover (short MA crosses above long MA)
                ma_bullish = (df[short_ma] > df[long_ma]) & (df[short_ma].shift(1) <= df[long_ma].shift(1))
                df['Signal_Strength'] += np.where(ma_bullish, 1, 0)
                
                # Bearish crossover (short MA crosses below long MA)
                ma_bearish = (df[short_ma] < df[long_ma]) & (df[short_ma].shift(1) >= df[long_ma].shift(1))
                df['Signal_Strength'] -= np.where(ma_bearish, 1, 0)
        
        # Stochastic signals
        if all(col in df.columns for col in ['Stoch_K', 'Stoch_D']):
            # Bullish crossover in oversold region
            stoch_bullish = (df['Stoch_K'] > df['Stoch_D']) & (df['Stoch_K'].shift(1) <= df['Stoch_D'].shift(1)) & (df['Stoch_K'] < 30)
            df['Signal_Strength'] += np.where(stoch_bullish, 1, 0)
            
            # Bearish crossover in overbought region
            stoch_bearish = (df['Stoch_K'] < df['Stoch_D']) & (df['Stoch_K'].shift(1) >= df['Stoch_D'].shift(1)) & (df['Stoch_K'] > 70)
            df['Signal_Strength'] -= np.where(stoch_bearish, 1, 0)
        
        # Volume confirmation
        if all(col in df.columns for col in ['Volume', 'Volume_SMA_20']):
            high_volume = df['Volume'] > (df['Volume_SMA_20'] * 1.5)
            
            # High volume confirms existing signals
            df['Signal_Strength'] += np.where(high_volume & (df['Signal_Strength'] > 0), 1, 0)
            df['Signal_Strength'] -= np.where(high_volume & (df['Signal_Strength'] < 0), 1, 0)
    
    def filter_signals(self, df: pd.DataFrame, min_strength: int = None) -> pd.DataFrame:
        """
        Filter signals based on strength or other criteria.
        
        Args:
            df: DataFrame with signals
            min_strength: Minimum absolute signal strength to consider
            
        Returns:
            Filtered DataFrame with only significant signals
        """
        if min_strength is None:
            min_strength = self.signal_threshold
        
        # Filter for rows with significant signals
        mask = (df['Buy_Signal'] | df['Sell_Signal'])
        
        if min_strength > 0:
            mask = mask & (df['Signal_Strength'].abs() >= min_strength)
        
        filtered_df = df[mask].copy()
        
        logger.info(f"Filtered signals: {len(filtered_df)} significant signals")
        return filtered_df
