"""
Integration test for the complete trading bot.
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
from src.data_collection import DataCollectionModule
from src.strategy import StrategyModule
from src.risk_management.risk_manager import RiskManager
from src.execution import ExecutionModule

def test_integration():
    """
    Integration test for the complete trading bot.
    """
    # Setup logging
    setup_logger(log_level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting integration test...")

    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    config = ConfigManager(config_path)
    
    # Initialize components
    risk_manager = RiskManager(config)
    data_collection = DataCollectionModule(config)
    strategy = StrategyModule(config)
    execution = ExecutionModule(config, risk_manager)
    
    # Test complete workflow
    try:
        logger.info("Testing complete trading workflow...")
        
        # Step 1: Get top trading pairs
        trading_pairs = data_collection.get_top_trading_pairs(limit=3)
        logger.info(f"Top trading pairs: {trading_pairs}")
        
        # Step 2: Get historical data for pairs
        historical_data = data_collection.get_historical_data_for_pairs(
            trading_pairs=trading_pairs,
            interval='1h',
            days=7
        )
        logger.info(f"Retrieved historical data for {len(historical_data)} pairs")
        
        # Step 3: Analyze data and generate signals
        analyzed_data = strategy.analyze_data(historical_data)
        logger.info(f"Analyzed data for {len(analyzed_data)} pairs")
        
        # Step 4: Get trading opportunities
        opportunities = strategy.get_trading_opportunities(analyzed_data)
        logger.info(f"Found {len(opportunities)} trading opportunities")
        
        # Step 5: Execute signals (paper trading)
        if opportunities:
            executed_positions = execution.execute_signals(opportunities)
            logger.info(f"Executed {len(executed_positions)} positions")
            
            # Step 6: Update positions with current prices
            current_prices = {pair: historical_data[pair].iloc[-1]['Close'] for pair in trading_pairs if pair in historical_data}
            execution.update_positions(current_prices)
            logger.info("Updated positions with current prices")
            
            # Step 7: Get exit signals
            exit_signals = strategy.get_exit_signals(analyzed_data, executed_positions)
            logger.info(f"Found {len(exit_signals)} exit signals")
            
            # Step 8: Execute exit signals
            if exit_signals:
                closed_positions = execution.execute_exit_signals(exit_signals)
                logger.info(f"Closed {len(closed_positions)} positions")
        
        # Step 9: Get performance metrics
        metrics = execution.get_performance_metrics()
        logger.info(f"Performance metrics: {metrics}")
        
        logger.info("Complete trading workflow test passed")
    except Exception as e:
        logger.error(f"Error in complete trading workflow: {e}")
        return False
    
    logger.info("Integration test passed!")
    return True

if __name__ == "__main__":
    test_integration()
