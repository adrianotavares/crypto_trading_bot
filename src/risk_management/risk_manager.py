"""
Risk management module for the trading bot.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Manages risk for trading operations.
    """
    
    def __init__(self, config):
        """
        Initialize the risk manager.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        
        # Risk parameters
        self.max_position_size = config.get('risk', 'max_position_size', default=0.05)  # 5% of account
        self.max_open_positions = config.get('risk', 'max_open_positions', default=5)
        self.max_daily_loss = config.get('risk', 'max_daily_loss', default=0.03)  # 3% of account
        self.trailing_stop_pct = config.get('risk', 'trailing_stop_pct', default=0.02)  # 2%
        
        logger.info("Risk manager initialized with parameters:")
        logger.info(f"Max position size: {self.max_position_size * 100}% of account")
        logger.info(f"Max open positions: {self.max_open_positions}")
        logger.info(f"Max daily loss: {self.max_daily_loss * 100}% of account")
        logger.info(f"Trailing stop percentage: {self.trailing_stop_pct * 100}%")
    
    def calculate_position_size(self, symbol: str, side: str, price: Optional[float] = None) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            symbol: Trading pair symbol
            side: Position side ('LONG' or 'SHORT')
            price: Current price (optional)
            
        Returns:
            Position size
        """
        # Get account balance
        account_balance = self.config.get('paper_trading', 'initial_balance', default=10000.0)
        
        # Calculate position size based on max_position_size
        position_size = account_balance * self.max_position_size
        
        # Convert to quantity based on price
        if price:
            quantity = position_size / price
        else:
            # If price is not provided, use a placeholder
            quantity = position_size / 100.0
        
        logger.info(f"Calculated position size for {symbol}: {quantity}")
        return quantity
    
    def check_order(self, symbol: str, side: str, quantity: float, price: Optional[float] = None) -> bool:
        """
        Check if an order is allowed based on risk parameters.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Order price (optional)
            
        Returns:
            Whether the order is allowed
        """
        # Check if we have too many open positions
        open_positions = self.config.get('execution', 'open_positions', default=0)
        if open_positions >= self.max_open_positions:
            logger.warning(f"Order rejected: Max open positions ({self.max_open_positions}) reached")
            return False
        
        # Check if we've hit the daily loss limit
        daily_pnl = self.config.get('execution', 'daily_pnl', default=0.0)
        account_balance = self.config.get('paper_trading', 'initial_balance', default=10000.0)
        max_loss_amount = account_balance * self.max_daily_loss
        
        if daily_pnl < -max_loss_amount:
            logger.warning(f"Order rejected: Daily loss limit ({self.max_daily_loss * 100}% of account) reached")
            return False
        
        # Calculate order value
        if price:
            order_value = quantity * price
            
            # Check if order size exceeds max position size
            max_position_value = account_balance * self.max_position_size
            if order_value > max_position_value:
                logger.warning(f"Order rejected: Position size ({order_value}) exceeds max ({max_position_value})")
                return False
        
        logger.info(f"Order approved: {side} {quantity} {symbol}")
        return True
    
    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """
        Calculate stop loss price based on risk parameters.
        
        Args:
            entry_price: Entry price
            side: Position side ('LONG' or 'SHORT')
            
        Returns:
            Stop loss price
        """
        if side == 'LONG':
            stop_loss = entry_price * (1 - self.trailing_stop_pct)
        else:
            stop_loss = entry_price * (1 + self.trailing_stop_pct)
        
        logger.info(f"Calculated stop loss for {side} position at {entry_price}: {stop_loss}")
        return stop_loss
    
    def update_trailing_stop(self, entry_price: float, current_price: float, 
                            current_stop: float, side: str) -> float:
        """
        Update trailing stop price based on current price.
        
        Args:
            entry_price: Entry price
            current_price: Current price
            current_stop: Current stop loss price
            side: Position side ('LONG' or 'SHORT')
            
        Returns:
            Updated stop loss price
        """
        if side == 'LONG':
            # For long positions, stop loss moves up as price increases
            new_stop = current_price * (1 - self.trailing_stop_pct)
            
            # Only update if new stop is higher than current stop
            if new_stop > current_stop:
                logger.info(f"Updated trailing stop for LONG position: {current_stop} -> {new_stop}")
                return new_stop
            
        else:
            # For short positions, stop loss moves down as price decreases
            new_stop = current_price * (1 + self.trailing_stop_pct)
            
            # Only update if new stop is lower than current stop
            if new_stop < current_stop:
                logger.info(f"Updated trailing stop for SHORT position: {current_stop} -> {new_stop}")
                return new_stop
        
        return current_stop
