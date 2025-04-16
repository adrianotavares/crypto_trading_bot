"""
Module for initializing and managing the strategy components.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd

from src.strategy.indicator_calculator import IndicatorCalculator
from src.strategy.custom_strategy import CustomStrategy
from src.strategy.signal_generator import SignalGenerator

logger = logging.getLogger(__name__)

class StrategyModule:
    """
    Manages the strategy components for the trading bot.
    """
    
    def __init__(self, config):
        """
        Initialize the strategy module.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.indicator_calculator = IndicatorCalculator()
        self.custom_strategy = CustomStrategy(config)
        self.signal_generator = SignalGenerator(config)
        logger.info("Strategy module initialized")
    
    def analyze_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Analyze market data and generate trading signals.
        
        Args:
            data: Dictionary mapping symbols to their historical data DataFrames
            
        Returns:
            Dictionary mapping symbols to DataFrames with added indicators and signals
        """
        results = {}
        
        for symbol, df in data.items():
            try:
                # Calculate indicators
                df_with_indicators = self.custom_strategy.calculate_indicators(df)
                
                # Generate signals
                df_with_signals = self.custom_strategy.generate_signals(df_with_indicators)
                
                # Store results
                results[symbol] = df_with_signals
                
                logger.info(f"Analyzed data for {symbol}: {len(df)} candles, " +
                           f"{df_with_signals['Buy_Signal'].sum()} buy signals, " +
                           f"{df_with_signals['Sell_Signal'].sum()} sell signals")
                
            except Exception as e:
                logger.error(f"Error analyzing data for {symbol}: {e}")
        
        return results
    
    def get_trading_opportunities(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Get current trading opportunities based on analyzed data.
        
        Args:
            data: Dictionary mapping symbols to DataFrames with indicators and signals
            
        Returns:
            List of trading opportunities
        """
        opportunities = []
        
        for symbol, df in data.items():
            try:
                # Get the latest data point
                latest = df.iloc[-1].copy()
                
                # Check if there's a signal
                if latest['Buy_Signal'] or latest['Sell_Signal']:
                    signal_type = 'buy' if latest['Buy_Signal'] else 'sell'
                    
                    opportunity = {
                        'symbol': symbol,
                        'timestamp': latest.name,
                        'price': latest['Close'],
                        'type': signal_type,
                        'signal_strength': latest['Signal_Strength'],
                        'indicators': {
                            'rsi': latest.get('RSI_14', None),
                            'macd': latest.get('MACD', None),
                            'macd_signal': latest.get('MACD_Signal', None),
                            'bb_width': latest.get('BB_Width', None)
                        }
                    }
                    
                    # Calculate stop loss and take profit
                    if signal_type == 'buy':
                        opportunity['stop_loss'] = self.custom_strategy._calculate_stop_loss(latest, 'buy')
                        opportunity['take_profit'] = self.custom_strategy._calculate_take_profit(latest, 'buy')
                    else:
                        opportunity['stop_loss'] = self.custom_strategy._calculate_stop_loss(latest, 'sell')
                        opportunity['take_profit'] = self.custom_strategy._calculate_take_profit(latest, 'sell')
                    
                    opportunities.append(opportunity)
                    
                    logger.info(f"Found {signal_type} opportunity for {symbol} at {latest['Close']}")
                
            except Exception as e:
                logger.error(f"Error getting trading opportunities for {symbol}: {e}")
        
        return opportunities
    
    def get_exit_signals(self, data: Dict[str, pd.DataFrame], positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get exit signals for current positions.
        
        Args:
            data: Dictionary mapping symbols to DataFrames with indicators and signals
            positions: List of current positions
            
        Returns:
            List of exit signals
        """
        exit_signals = []
        
        for position in positions:
            symbol = position['symbol']
            
            if symbol in data:
                df = data[symbol]
                
                try:
                    # Get exit points for this position
                    exit_points = self.custom_strategy.get_exit_points(df, position)
                    
                    # If there are exit points, add them to the list
                    if exit_points:
                        exit_signals.extend(exit_points)
                        
                        logger.info(f"Found exit signal for {symbol} position entered at {position['timestamp']}")
                    
                except Exception as e:
                    logger.error(f"Error getting exit signals for {symbol}: {e}")
        
        return exit_signals
    
    def optimize_strategy(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Optimize strategy parameters based on historical data.
        
        Args:
            data: Dictionary mapping symbols to their historical data DataFrames
            
        Returns:
            Dictionary with optimized parameters
        """
        # Combine all data for optimization
        combined_data = pd.concat([df for df in data.values()], axis=0)
        
        # Optimize parameters
        optimized_params = self.custom_strategy.optimize_parameters(combined_data)
        
        logger.info(f"Optimized strategy parameters: {optimized_params}")
        return optimized_params
