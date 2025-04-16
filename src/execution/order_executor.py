"""
Base interface for order execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd


class OrderExecutor(ABC):
    """
    Abstract base class for order execution.
    """
    
    @abstractmethod
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: Optional[float] = None,
                   stop_price: Optional[float] = None,
                   time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place an order on the exchange.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('BUY' or 'SELL')
            order_type: Order type ('MARKET', 'LIMIT', 'STOP_LOSS', 'STOP_LOSS_LIMIT', etc.)
            quantity: Order quantity
            price: Order price (required for limit orders)
            stop_price: Stop price (required for stop loss orders)
            time_in_force: Time in force ('GTC', 'IOC', 'FOK')
            
        Returns:
            Order information
        """
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Cancellation information
        """
        pass
    
    @abstractmethod
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Get information about an order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Order information
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders.
        
        Args:
            symbol: Trading pair symbol (optional)
            
        Returns:
            List of open orders
        """
        pass
    
    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance.
        
        Returns:
            Dictionary mapping assets to their balances
        """
        pass
    
    @abstractmethod
    def place_trailing_stop_order(self, symbol: str, side: str, quantity: float, 
                                 activation_price: float, callback_rate: float) -> Dict[str, Any]:
        """
        Place a trailing stop order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            activation_price: Activation price for the trailing stop
            callback_rate: Callback rate in percentage
            
        Returns:
            Order information
        """
        pass
