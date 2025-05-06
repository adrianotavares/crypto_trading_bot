"""
Custom trading strategy implementation combining multiple indicators.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from src.strategy.strategy import Strategy
from src.strategy.indicator_calculator import IndicatorCalculator

logger = logging.getLogger(__name__)

class CustomStrategy(Strategy):
    """
    Custom trading strategy that combines multiple technical indicators.
    """
    
    def __init__(self, config):
        """
        Initialize the custom strategy.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.indicator_calculator = IndicatorCalculator()
        
        # Strategy parameters
        self.rsi_period = config.get('strategy', 'rsi_period', default=14)
        self.rsi_overbought = config.get('strategy', 'rsi_overbought', default=70)
        self.rsi_oversold = config.get('strategy', 'rsi_oversold', default=30)
        
        self.macd_fast = config.get('strategy', 'macd_fast', default=12)
        self.macd_slow = config.get('strategy', 'macd_slow', default=26)
        self.macd_signal = config.get('strategy', 'macd_signal', default=9)
        
        self.bb_period = config.get('strategy', 'bb_period', default=20)
        self.bb_std_dev = config.get('strategy', 'bb_std_dev', default=2.0)
        
        self.stoch_k_period = config.get('strategy', 'stoch_k_period', default=14)
        self.stoch_d_period = config.get('strategy', 'stoch_d_period', default=3)
        self.stoch_smooth_k = config.get('strategy', 'stoch_smooth_k', default=3)
        
        self.atr_period = config.get('strategy', 'atr_period', default=14)
        self.atr_multiplier = config.get('strategy', 'atr_multiplier', default=2.0)
        
        # Trailing stop loss parameters
        self.trailing_stop_pct = config.get('strategy', 'trailing_stop_pct', default=2.0)
        
        logger.info("Custom strategy initialized with parameters:")
        logger.info(f"RSI: period={self.rsi_period}, overbought={self.rsi_overbought}, oversold={self.rsi_oversold}")
        logger.info(f"MACD: fast={self.macd_fast}, slow={self.macd_slow}, signal={self.macd_signal}")
        logger.info(f"Bollinger Bands: period={self.bb_period}, std_dev={self.bb_std_dev}")
        logger.info(f"Stochastic: k_period={self.stoch_k_period}, d_period={self.stoch_d_period}, smooth_k={self.stoch_smooth_k}")
        logger.info(f"ATR: period={self.atr_period}, multiplier={self.atr_multiplier}")
        logger.info(f"Trailing stop: percentage={self.trailing_stop_pct}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        df = data.copy()
        
        # Calculate RSI
        df = self.indicator_calculator.add_rsi(
            df, 
            period=self.rsi_period, 
            overbought=self.rsi_overbought, 
            oversold=self.rsi_oversold
        )
        
        # Calculate MACD
        df = self.indicator_calculator.add_macd(
            df, 
            fast=self.macd_fast, 
            slow=self.macd_slow, 
            signal=self.macd_signal
        )
        
        # Calculate Bollinger Bands
        df = self.indicator_calculator.add_bollinger_bands(
            df, 
            period=self.bb_period, 
            std_dev=self.bb_std_dev
        )
        
        # Calculate Stochastic Oscillator
        df = self.indicator_calculator.add_stochastic(
            df, 
            k_period=self.stoch_k_period, 
            d_period=self.stoch_d_period, 
            smooth_k=self.stoch_smooth_k
        )
        
        # Calculate ATR for volatility measurement
        df = self.indicator_calculator.add_atr(
            df, 
            period=self.atr_period
        )
        
        # Calculate volume indicators
        df = self.indicator_calculator.add_volume_indicators(df)
        
        logger.info(f"Calculated indicators for {len(df)} data points")
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on indicators.
        
        Args:
            data: DataFrame with OHLCV data and indicators
            
        Returns:
            DataFrame with added signal columns
        """
        df = data.copy()
        
        # Initialize signal columns
        df['Buy_Signal'] = False
        df['Sell_Signal'] = False
        df['Signal_Strength'] = 0  # -5 to 5 scale, negative for sell, positive for buy
        
        # RSI signals
        df['Signal_Strength'] += np.where(df['RSI_Oversold'], 1, 0)  # Oversold condition (buy signal)
        df['Signal_Strength'] -= np.where(df['RSI_Overbought'], 1, 0)  # Overbought condition (sell signal)
        
        # MACD signals
        df['Signal_Strength'] += np.where(df['MACD_Bullish_Crossover'], 1, 0)  # Bullish crossover (buy signal)
        df['Signal_Strength'] -= np.where(df['MACD_Bearish_Crossover'], 1, 0)  # Bearish crossover (sell signal)
        
        # Bollinger Bands signals
        df['Signal_Strength'] += np.where(df['BB_Lower_Touch'], 1, 0)  # Price touches lower band (buy signal)
        df['Signal_Strength'] -= np.where(df['BB_Upper_Touch'], 1, 0)  # Price touches upper band (sell signal)
        
        # Stochastic signals
        df['Signal_Strength'] += np.where(df['Stoch_Bullish_Crossover'] & (df['Stoch_K'] < 30), 1, 0)  # Bullish crossover in oversold region
        df['Signal_Strength'] -= np.where(df['Stoch_Bearish_Crossover'] & (df['Stoch_K'] > 70), 1, 0)  # Bearish crossover in overbought region
        
        # Volume confirmation
        df['Signal_Strength'] += np.where(df['High_Volume'] & (df['Signal_Strength'] > 0), 1, 0)  # High volume confirms buy signal
        df['Signal_Strength'] -= np.where(df['High_Volume'] & (df['Signal_Strength'] < 0), 1, 0)  # High volume confirms sell signal
        
        # Generate final buy/sell signals based on signal strength
        df['Buy_Signal'] = df['Signal_Strength'] >= 3  # Strong buy signal
        df['Sell_Signal'] = df['Signal_Strength'] <= -3  # Strong sell signal
        
        logger.info(f"Generated signals: {df['Buy_Signal'].sum()} buy signals, {df['Sell_Signal'].sum()} sell signals")
        return df
    
    def get_entry_points(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Get entry points for trades.
        
        Args:
            data: DataFrame with OHLCV data, indicators, and signals
            
        Returns:
            List of entry points with relevant information
        """
        df = data.copy()
        entry_points = []
        
        # Find buy signals
        buy_signals = df[df['Buy_Signal']].copy()
        
        for idx, row in buy_signals.iterrows():
            entry_point = {
                'timestamp': idx,
                'symbol': row.get('symbol', 'Unknown'),
                'price': row['Close'],
                'type': 'buy',
                'signal_strength': row['Signal_Strength'],
                'stop_loss': self._calculate_stop_loss(row, 'buy'),
                'take_profit': self._calculate_take_profit(row, 'buy')
            }
            entry_points.append(entry_point)
        
        # Find sell signals (for short positions)
        sell_signals = df[df['Sell_Signal']].copy()
        
        for idx, row in sell_signals.iterrows():
            entry_point = {
                'timestamp': idx,
                'symbol': row.get('symbol', 'Unknown'),
                'price': row['Close'],
                'type': 'sell',
                'signal_strength': row['Signal_Strength'],
                'stop_loss': self._calculate_stop_loss(row, 'sell'),
                'take_profit': self._calculate_take_profit(row, 'sell')
            }
            entry_points.append(entry_point)
        
        logger.info(f"Found {len(entry_points)} entry points")
        return entry_points
    
    def get_exit_points(self, data: pd.DataFrame, position: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get exit points for trades.
        
        Args:
            data: DataFrame with OHLCV data, indicators, and signals
            position: Current position information
            
        Returns:
            List of exit points with relevant information
        """
        # Verifique se a chave 'type' existe no dicionário position
        if 'type' not in position:
            logger.error("Position object is missing the 'type' key")
            return []

        if 'price' not in position or 'timestamp' not in position:
            logger.error("Position object is missing required keys: 'price' or 'timestamp'")
            return []
    
        df = data.copy()
        exit_points = []
        
        position_type = position['type']
        entry_price = position['price']
        entry_time = position['timestamp']
        
        # Filter data to only include rows after entry
        if isinstance(entry_time, pd.Timestamp):
            df = df[df.index > entry_time]
        
        # If no data after entry, return empty list
        if len(df) == 0:
            return []
        
        # Calculate trailing stop loss
        if position_type == 'buy':
            # For long positions
            df['Trailing_Stop'] = self._calculate_trailing_stop_long(df, entry_price)
            
            # Exit when price crosses below trailing stop or opposite signal appears
            exit_condition = (df['Low'] < df['Trailing_Stop']) | df['Sell_Signal']
        else:
            # For short positions
            df['Trailing_Stop'] = self._calculate_trailing_stop_short(df, entry_price)
            
            # Exit when price crosses above trailing stop or opposite signal appears
            exit_condition = (df['High'] > df['Trailing_Stop']) | df['Buy_Signal']
        
        # Find exit points
        exit_signals = df[exit_condition].copy()
        
        for idx, row in exit_signals.iterrows():
            exit_reason = 'trailing_stop'
            if (position_type == 'buy' and row['Sell_Signal']) or (position_type == 'sell' and row['Buy_Signal']):
                exit_reason = 'signal_reversal'
            
            exit_point = {
                'timestamp': idx,
                'symbol': row.get('symbol', position.get('symbol', 'Unknown')),
                'price': row['Close'],
                'type': 'exit_' + position_type,
                'reason': exit_reason,
                'profit_pct': self._calculate_profit_percentage(entry_price, row['Close'], position_type)
            }
            exit_points.append(exit_point)
        
        logger.info(f"Found {len(exit_points)} exit points for position entered at {entry_time}")
        return exit_points
    
    def optimize_parameters(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Optimize strategy parameters.
        
        Args:
            data: DataFrame with OHLCV data
            **kwargs: Additional parameters for optimization
            
        Returns:
            Dictionary with optimized parameters
        """
        # In a real implementation, this would use a grid search or genetic algorithm
        # to find optimal parameters. For now, we'll return the current parameters.
        
        optimized_params = {
            'rsi_period': self.rsi_period,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'macd_fast': self.macd_fast,
            'macd_slow': self.macd_slow,
            'macd_signal': self.macd_signal,
            'bb_period': self.bb_period,
            'bb_std_dev': self.bb_std_dev,
            'stoch_k_period': self.stoch_k_period,
            'stoch_d_period': self.stoch_d_period,
            'stoch_smooth_k': self.stoch_smooth_k,
            'atr_period': self.atr_period,
            'atr_multiplier': self.atr_multiplier,
            'trailing_stop_pct': self.trailing_stop_pct
        }
        
        logger.info("Parameter optimization not implemented, returning current parameters")
        return optimized_params
    
    def _calculate_stop_loss(self, row: pd.Series, position_type: str) -> float:
        """
        Calculate initial stop loss price.
        
        Args:
            row: DataFrame row with OHLCV and indicator data
            position_type: Type of position ('buy' or 'sell')
            
        Returns:
            Stop loss price
        """
        atr = row.get(f'ATR_{self.atr_period}', 0)
        
        if position_type == 'buy':
            # For long positions, stop loss is below entry price
            return row['Close'] - (atr * self.atr_multiplier)
        else:
            # For short positions, stop loss is above entry price
            return row['Close'] + (atr * self.atr_multiplier)
    
    def _calculate_take_profit(self, row: pd.Series, position_type: str) -> float:
        """
        Calculate take profit price.
        
        Args:
            row: DataFrame row with OHLCV and indicator data
            position_type: Type of position ('buy' or 'sell')
            
        Returns:
            Take profit price
        """
        atr = row.get(f'ATR_{self.atr_period}', 0)
        
        if position_type == 'buy':
            # For long positions, take profit is above entry price
            return row['Close'] + (atr * self.atr_multiplier * 2)
        else:
            # For short positions, take profit is below entry price
            return row['Close'] - (atr * self.atr_multiplier * 2)
    
    def _calculate_trailing_stop_long(self, df: pd.DataFrame, entry_price: float) -> pd.Series:
        """
        Calculate trailing stop for long positions.
        
        Args:
            df: DataFrame with OHLCV data
            entry_price: Entry price for the position
            
        Returns:
            Series with trailing stop prices
        """
        # Initialize trailing stop at entry price minus percentage
        initial_stop = entry_price * (1 - self.trailing_stop_pct / 100)
        
        # Calculate highest high since entry
        highest_high = df['High'].cummax()
        
        # Calculate trailing stop as highest high minus percentage
        trailing_stop = highest_high * (1 - self.trailing_stop_pct / 100)
        
        # Trailing stop can only increase, never decrease
        trailing_stop = trailing_stop.cummax()
        
        # Ensure trailing stop is at least the initial stop
        trailing_stop = trailing_stop.clip(lower=initial_stop)
        
        return trailing_stop
    
    def _calculate_trailing_stop_short(self, df: pd.DataFrame, entry_price: float) -> pd.Series:
        """
        Calculate trailing stop for short positions.
        
        Args:
            df: DataFrame with OHLCV data
            entry_price: Entry price for the position
            
        Returns:
            Series with trailing stop prices
        """
        # Initialize trailing stop at entry price plus percentage
        initial_stop = entry_price * (1 + self.trailing_stop_pct / 100)
        
        # Calculate lowest low since entry
        lowest_low = df['Low'].cummin()
        
        # Calculate trailing stop as lowest low plus percentage
        trailing_stop = lowest_low * (1 + self.trailing_stop_pct / 100)
        
        # Trailing stop can only decrease, never increase
        trailing_stop = trailing_stop.cummin()
        
        # Ensure trailing stop is at most the initial stop
        trailing_stop = trailing_stop.clip(upper=initial_stop)
        
        return trailing_stop
    
    def _calculate_profit_percentage(self, entry_price: float, exit_price: float, position_type: str) -> float:
        """
        Calculate profit percentage for a trade.
        
        Args:
            entry_price: Entry price for the position
            exit_price: Exit price for the position
            position_type: Type of position ('buy' or 'sell')
            
        Returns:
            Profit percentage
        """
        if position_type == 'buy':
            # For long positions
            return ((exit_price - entry_price) / entry_price) * 100
        else:
            # For short positions
            return ((entry_price - exit_price) / entry_price) * 100
