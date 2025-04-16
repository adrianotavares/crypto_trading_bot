"""
Test script for the strategy module.
"""

import os
import sys
import logging
import time
from pathlib import Path
import pandas as pd

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.config_manager import ConfigManager
from src.logging.logger import setup_logger
from src.data_collection.binance_data_provider import BinanceDataProvider
from src.strategy.indicator_calculator import IndicatorCalculator
from src.strategy.custom_strategy import CustomStrategy
from src.strategy.signal_generator import SignalGenerator

def test_strategy():
    """
    Test the strategy module.
    """
    # Setup logging
    setup_logger(log_level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting strategy test...")

    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    config = ConfigManager(config_path)
    
    # Initialize components
    data_provider = BinanceDataProvider(config)
    indicator_calculator = IndicatorCalculator()
    custom_strategy = CustomStrategy(config)
    signal_generator = SignalGenerator(config)
    
    # Get historical data for testing
    try:
        logger.info("Getting historical data for testing...")
        
        # Get top cryptocurrencies
        top_cryptos = data_provider.get_top_cryptocurrencies(limit=3)
        symbols = [crypto['symbol'] for crypto in top_cryptos]
        
        # Get historical data for each symbol
        historical_data = {}
        for symbol in symbols:
            data = data_provider.get_historical_data(
                symbol=symbol,
                interval='1h',
                limit=200
            )
            historical_data[symbol] = data
            logger.info(f"Retrieved {len(data)} candles for {symbol}")
        
        if not historical_data:
            logger.error("Failed to get historical data")
            return False
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return False
    
    # Test indicator calculation
    try:
        logger.info("Testing indicator calculation...")
        
        for symbol, data in historical_data.items():
            # Calculate indicators
            data_with_indicators = indicator_calculator.add_all_indicators(data)
            
            logger.info(f"Calculated indicators for {symbol}: {data_with_indicators.columns.tolist()}")
            
            # Check if indicators were calculated
            expected_indicators = ['SMA_20', 'EMA_20', 'RSI_14', 'MACD', 'BB_Upper', 'Stoch_K', 'ATR_14']
            for indicator in expected_indicators:
                if indicator not in data_with_indicators.columns:
                    logger.error(f"Indicator {indicator} not found in calculated indicators")
                    return False
            
            logger.info(f"Indicator calculation for {symbol} passed")
        
        logger.info("All indicator calculations passed")
    except Exception as e:
        logger.error(f"Error in indicator calculation: {e}")
        return False
    
    # Test strategy signal generation
    try:
        logger.info("Testing strategy signal generation...")
        
        for symbol, data in historical_data.items():
            # Calculate indicators
            data_with_indicators = custom_strategy.calculate_indicators(data)
            
            # Generate signals
            data_with_signals = custom_strategy.generate_signals(data_with_indicators)
            
            # Check if signals were generated
            if 'Buy_Signal' not in data_with_signals.columns or 'Sell_Signal' not in data_with_signals.columns:
                logger.error(f"Signals not found in generated signals for {symbol}")
                return False
            
            # Count signals
            buy_signals = data_with_signals['Buy_Signal'].sum()
            sell_signals = data_with_signals['Sell_Signal'].sum()
            
            logger.info(f"Generated signals for {symbol}: {buy_signals} buy, {sell_signals} sell")
            
            # Get entry points
            entry_points = custom_strategy.get_entry_points(data_with_signals)
            logger.info(f"Found {len(entry_points)} entry points for {symbol}")
            
            # Test exit points for a sample position
            if entry_points:
                sample_position = entry_points[0]
                exit_points = custom_strategy.get_exit_points(data_with_signals, sample_position)
                logger.info(f"Found {len(exit_points)} exit points for sample position")
            
            logger.info(f"Strategy signal generation for {symbol} passed")
        
        logger.info("All strategy signal generation tests passed")
    except Exception as e:
        logger.error(f"Error in strategy signal generation: {e}")
        return False
    
    # Test signal generator
    try:
        logger.info("Testing signal generator...")
        
        for symbol, data in historical_data.items():
            # Calculate indicators
            data_with_indicators = indicator_calculator.add_all_indicators(data)
            
            # Generate signals
            data_with_signals = signal_generator.generate_signals(data_with_indicators)
            
            # Filter signals
            filtered_signals = signal_generator.filter_signals(data_with_signals)
            
            logger.info(f"Generated and filtered signals for {symbol}: {len(filtered_signals)} significant signals")
            
            logger.info(f"Signal generator test for {symbol} passed")
        
        logger.info("All signal generator tests passed")
    except Exception as e:
        logger.error(f"Error in signal generator: {e}")
        return False
    
    logger.info("All strategy tests passed!")
    return True

if __name__ == "__main__":
    test_strategy()
