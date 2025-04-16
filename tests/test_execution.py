"""
Test script for the execution module.
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
from src.strategy.custom_strategy import CustomStrategy
from src.risk_management.risk_manager import RiskManager
from src.execution.paper_trading_executor import PaperTradingExecutor
from src.execution.position_manager import PositionManager

def test_execution():
    """
    Test the execution module.
    """
    # Setup logging
    setup_logger(log_level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting execution test...")

    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    config = ConfigManager(config_path)
    
    # Initialize components
    data_provider = BinanceDataProvider(config)
    risk_manager = RiskManager(config)
    paper_trading_executor = PaperTradingExecutor(config, risk_manager)
    position_manager = PositionManager(config, paper_trading_executor, risk_manager)
    
    # Test paper trading executor
    try:
        logger.info("Testing paper trading executor...")
        
        # Get account balance
        balance = paper_trading_executor.get_account_balance()
        logger.info(f"Paper trading account balance: {balance}")
        
        # Place a test order
        test_symbol = "BTCUSDT"
        test_quantity = 0.01
        test_price = 50000.0  # Placeholder price
        
        order = paper_trading_executor.place_order(
            symbol=test_symbol,
            side="BUY",
            order_type="MARKET",
            quantity=test_quantity,
            price=test_price
        )
        
        logger.info(f"Placed test order: {order}")
        
        # Get open orders
        open_orders = paper_trading_executor.get_open_orders()
        logger.info(f"Open orders: {open_orders}")
        
        # Test trailing stop order
        trailing_order = paper_trading_executor.place_trailing_stop_order(
            symbol=test_symbol,
            side="SELL",
            quantity=test_quantity,
            activation_price=test_price * 1.05,
            callback_rate=1.0
        )
        
        logger.info(f"Placed trailing stop order: {trailing_order}")
        
        # Cancel the trailing stop order
        if trailing_order:
            cancel_result = paper_trading_executor.cancel_order(
                symbol=test_symbol,
                order_id=trailing_order['orderId']
            )
            logger.info(f"Cancelled trailing stop order: {cancel_result}")
        
        logger.info("Paper trading executor test passed")
    except Exception as e:
        logger.error(f"Error in paper trading executor: {e}")
        return False
    
    # Test position manager
    try:
        logger.info("Testing position manager...")
        
        # Open a test position
        position = position_manager.open_position(
            symbol=test_symbol,
            side="LONG",
            quantity=test_quantity,
            price=test_price,
            stop_loss=test_price * 0.95,
            take_profit=test_price * 1.05
        )
        
        logger.info(f"Opened test position: {position}")
        
        # Get open positions
        open_positions = position_manager.get_open_positions()
        logger.info(f"Open positions: {open_positions}")
        
        # Update position with current price
        if open_positions:
            position_id = open_positions[0]['id']
            updated_position = position_manager.update_position(
                position_id=position_id,
                current_price=test_price * 1.02  # Simulate price increase
            )
            logger.info(f"Updated position: {updated_position}")
            
            # Enable trailing stop
            trailing_position = position_manager.enable_trailing_stop(
                position_id=position_id,
                activation_price=test_price * 1.03,
                callback_rate=1.0
            )
            logger.info(f"Enabled trailing stop: {trailing_position}")
            
            # Update trailing stop
            updated_trailing = position_manager.update_trailing_stop(
                position_id=position_id,
                current_price=test_price * 1.04  # Simulate further price increase
            )
            logger.info(f"Updated trailing stop: {updated_trailing}")
            
            # Close the position
            closed_position = position_manager.close_position(
                position_id=position_id,
                price=test_price * 1.03  # Simulate exit price
            )
            logger.info(f"Closed position: {closed_position}")
        
        # Get position history
        position_history = position_manager.get_position_history()
        logger.info(f"Position history: {position_history}")
        
        # Get performance metrics
        metrics = position_manager.get_performance_metrics()
        logger.info(f"Performance metrics: {metrics}")
        
        logger.info("Position manager test passed")
    except Exception as e:
        logger.error(f"Error in position manager: {e}")
        return False
    
    # Test risk manager
    try:
        logger.info("Testing risk manager...")
        
        # Calculate position size
        position_size = risk_manager.calculate_position_size(
            symbol=test_symbol,
            side="LONG",
            price=test_price
        )
        logger.info(f"Calculated position size: {position_size}")
        
        # Check order
        order_check = risk_manager.check_order(
            symbol=test_symbol,
            side="BUY",
            quantity=test_quantity,
            price=test_price
        )
        logger.info(f"Order check result: {order_check}")
        
        # Calculate stop loss
        stop_loss = risk_manager.calculate_stop_loss(
            entry_price=test_price,
            side="LONG"
        )
        logger.info(f"Calculated stop loss: {stop_loss}")
        
        # Update trailing stop
        updated_stop = risk_manager.update_trailing_stop(
            entry_price=test_price,
            current_price=test_price * 1.05,
            current_stop=stop_loss,
            side="LONG"
        )
        logger.info(f"Updated trailing stop: {updated_stop}")
        
        logger.info("Risk manager test passed")
    except Exception as e:
        logger.error(f"Error in risk manager: {e}")
        return False
    
    logger.info("All execution tests passed!")
    return True

if __name__ == "__main__":
    test_execution()
