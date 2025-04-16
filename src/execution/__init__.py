"""
Module for initializing and managing the execution components.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd

from src.execution.order_executor import OrderExecutor
from src.execution.binance_executor import BinanceExecutor
from src.execution.paper_trading_executor import PaperTradingExecutor
from src.execution.position_manager import PositionManager
from src.risk_management.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class ExecutionModule:
    """
    Manages the execution components for the trading bot.
    """
    
    def __init__(self, config, risk_manager: RiskManager):
        """
        Initialize the execution module.
        
        Args:
            config: Configuration manager instance
            risk_manager: Risk manager instance
        """
        self.config = config
        self.risk_manager = risk_manager
        
        # Determine trading mode
        self.trading_mode = config.get('execution', 'mode', default='paper')
        
        # Initialize executor based on trading mode
        if self.trading_mode == 'live':
            self.executor = BinanceExecutor(config, risk_manager)
        else:
            self.executor = PaperTradingExecutor(config, risk_manager)
        
        # Initialize position manager
        self.position_manager = PositionManager(config, self.executor, risk_manager)
        
        logger.info(f"Execution module initialized in {self.trading_mode} mode")
    
    def execute_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute trading signals.
        
        Args:
            signals: List of trading signals
            
        Returns:
            List of executed positions
        """
        executed_positions = []
        
        for signal in signals:
            try:
                symbol = signal['symbol']
                signal_type = signal['type']
                price = signal.get('price')
                
                if signal_type == 'buy':
                    # Calculate position size
                    quantity = self.risk_manager.calculate_position_size(symbol, 'LONG', price)
                    
                    # Calculate stop loss and take profit
                    stop_loss = signal.get('stop_loss')
                    take_profit = signal.get('take_profit')
                    
                    # Open long position
                    position = self.position_manager.open_position(
                        symbol=symbol,
                        side='LONG',
                        quantity=quantity,
                        price=price,
                        stop_loss=stop_loss,
                        take_profit=take_profit
                    )
                    
                    executed_positions.append(position)
                    logger.info(f"Executed buy signal for {symbol} at {price}")
                    
                elif signal_type == 'sell':
                    # Calculate position size
                    quantity = self.risk_manager.calculate_position_size(symbol, 'SHORT', price)
                    
                    # Calculate stop loss and take profit
                    stop_loss = signal.get('stop_loss')
                    take_profit = signal.get('take_profit')
                    
                    # Open short position
                    position = self.position_manager.open_position(
                        symbol=symbol,
                        side='SHORT',
                        quantity=quantity,
                        price=price,
                        stop_loss=stop_loss,
                        take_profit=take_profit
                    )
                    
                    executed_positions.append(position)
                    logger.info(f"Executed sell signal for {symbol} at {price}")
                    
            except Exception as e:
                logger.error(f"Error executing signal for {signal.get('symbol')}: {e}")
        
        return executed_positions
    
    def execute_exit_signals(self, exit_signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute exit signals for open positions.
        
        Args:
            exit_signals: List of exit signals
            
        Returns:
            List of closed positions
        """
        closed_positions = []
        
        for signal in exit_signals:
            try:
                symbol = signal['symbol']
                position_id = signal.get('position_id')
                price = signal.get('price')
                
                # If position_id is provided, close that specific position
                if position_id:
                    position = self.position_manager.close_position(position_id, price)
                    closed_positions.append(position)
                    logger.info(f"Executed exit signal for position {position_id}")
                    
                # Otherwise, close all positions for the symbol
                else:
                    open_positions = self.position_manager.get_open_positions(symbol)
                    for pos in open_positions:
                        position = self.position_manager.close_position(pos['id'], price)
                        closed_positions.append(position)
                        logger.info(f"Executed exit signal for position {pos['id']}")
                    
            except Exception as e:
                logger.error(f"Error executing exit signal: {e}")
        
        return closed_positions
    
    def update_positions(self, current_prices: Dict[str, float]) -> None:
        """
        Update open positions with current prices.
        
        Args:
            current_prices: Dictionary mapping symbols to their current prices
        """
        open_positions = self.position_manager.get_open_positions()
        
        for position in open_positions:
            symbol = position['symbol']
            position_id = position['id']
            
            if symbol in current_prices:
                current_price = current_prices[symbol]
                
                try:
                    # Update position with current price
                    self.position_manager.update_position(position_id, current_price)
                    
                    # Update trailing stop if enabled
                    self.position_manager.update_trailing_stop(position_id, current_price)
                    
                except Exception as e:
                    logger.error(f"Error updating position {position_id}: {e}")
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Get account balance.
        
        Returns:
            Account balance information
        """
        return self.executor.get_account_balance()
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Returns:
            List of open positions
        """
        return self.position_manager.get_open_positions()
    
    def get_position_history(self) -> List[Dict[str, Any]]:
        """
        Get position history.
        
        Returns:
            List of closed positions
        """
        return self.position_manager.get_position_history()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        return self.position_manager.get_performance_metrics()
