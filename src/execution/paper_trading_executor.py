"""
Paper trading implementation of the order executor.
"""

import logging
import time
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from src.execution.order_executor import OrderExecutor
from src.risk_management.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class PaperTradingExecutor(OrderExecutor):
    """
    Implementation of OrderExecutor for paper trading.
    """
    
    def __init__(self, config, risk_manager: RiskManager):
        """
        Initialize the paper trading executor.
        
        Args:
            config: Configuration manager instance
            risk_manager: Risk manager instance
        """
        self.config = config
        self.risk_manager = risk_manager
        
        # Initialize paper trading state
        self.initial_balance = config.get('paper_trading', 'initial_balance', default=10000.0)
        self.balances = {'USDT': self.initial_balance}
        self.orders = []
        self.positions = []
        
        # Load state if exists
        self.state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      'data', 'paper_trading_state.json')
        self._load_state()
        
        logger.info(f"Paper trading executor initialized with balance: {self.balances}")
    
    def _load_state(self):
        """
        Load paper trading state from file.
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.balances = state.get('balances', {'USDT': self.initial_balance})
                    self.orders = state.get('orders', [])
                    self.positions = state.get('positions', [])
                logger.info(f"Loaded paper trading state from {self.state_file}")
            except Exception as e:
                logger.error(f"Error loading paper trading state: {e}")
    
    def _save_state(self):
        """
        Save paper trading state to file.
        """
        try:
            state = {
                'balances': self.balances,
                'orders': self.orders,
                'positions': self.positions
            }
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"Saved paper trading state to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving paper trading state: {e}")
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: Optional[float] = None,
                   stop_price: Optional[float] = None,
                   time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place a paper trading order.
        
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
        # Check with risk manager if this order is allowed
        if not self.risk_manager.check_order(symbol, side, quantity, price):
            logger.warning(f"Order rejected by risk manager: {side} {quantity} {symbol} at {price}")
            raise ValueError("Order rejected by risk manager")
        
        # Generate order ID
        order_id = f"paper_{int(time.time() * 1000)}"
        
        # Get current price if not provided (for market orders)
        if price is None and order_type == 'MARKET':
            # In a real implementation, we would get the current market price
            # For now, we'll use a placeholder
            price = 100.0  # Placeholder
        
        # Create order object
        order = {
            'orderId': order_id,
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'price': price,
            'stopPrice': stop_price,
            'timeInForce': time_in_force,
            'status': 'NEW',
            'time': int(time.time() * 1000),
            'updateTime': int(time.time() * 1000)
        }
        
        # For market orders, execute immediately
        if order_type == 'MARKET':
            self._execute_order(order)
        else:
            # Add to open orders
            self.orders.append(order)
        
        # Save state
        self._save_state()
        
        logger.info(f"Placed paper trading {side} {order_type} order for {quantity} {symbol}: {order_id}")
        return order
    
    def _execute_order(self, order: Dict[str, Any]) -> None:
        """
        Execute a paper trading order.
        
        Args:
            order: Order information
        """
        symbol = order['symbol']
        side = order['side']
        quantity = float(order['quantity'])
        price = float(order['price'])
        
        # Extract base and quote assets from symbol (e.g., 'BTCUSDT' -> 'BTC', 'USDT')
        base_asset = symbol[:-4]  # Assuming all symbols end with 'USDT'
        quote_asset = 'USDT'
        
        # Update balances
        if side == 'BUY':
            # Check if we have enough quote asset
            cost = quantity * price
            if quote_asset not in self.balances or self.balances[quote_asset] < cost:
                logger.warning(f"Insufficient balance for {side} {quantity} {symbol} at {price}")
                order['status'] = 'REJECTED'
                return
            
            # Update balances
            self.balances[quote_asset] -= cost
            self.balances[base_asset] = self.balances.get(base_asset, 0) + quantity
            
            # Add to positions
            self.positions.append({
                'symbol': symbol,
                'side': 'LONG',
                'quantity': quantity,
                'entry_price': price,
                'entry_time': order['time'],
                'current_price': price
            })
            
        elif side == 'SELL':
            # Check if we have enough base asset
            if base_asset not in self.balances or self.balances[base_asset] < quantity:
                logger.warning(f"Insufficient balance for {side} {quantity} {symbol} at {price}")
                order['status'] = 'REJECTED'
                return
            
            # Update balances
            self.balances[base_asset] -= quantity
            self.balances[quote_asset] = self.balances.get(quote_asset, 0) + (quantity * price)
            
            # Add to positions
            self.positions.append({
                'symbol': symbol,
                'side': 'SHORT',
                'quantity': quantity,
                'entry_price': price,
                'entry_time': order['time'],
                'current_price': price
            })
        
        # Update order status
        order['status'] = 'FILLED'
        order['updateTime'] = int(time.time() * 1000)
        
        logger.info(f"Executed paper trading {side} order for {quantity} {symbol} at {price}")
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel a paper trading order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Cancellation information
        """
        # Find the order
        for i, order in enumerate(self.orders):
            if order['orderId'] == order_id and order['symbol'] == symbol:
                # Update order status
                order['status'] = 'CANCELED'
                order['updateTime'] = int(time.time() * 1000)
                
                # Remove from open orders
                self.orders.pop(i)
                
                # Save state
                self._save_state()
                
                logger.info(f"Cancelled paper trading order {order_id} for {symbol}")
                return order
        
        logger.warning(f"Order {order_id} for {symbol} not found")
        raise ValueError(f"Order {order_id} for {symbol} not found")
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Get information about a paper trading order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Order information
        """
        # Find the order
        for order in self.orders:
            if order['orderId'] == order_id and order['symbol'] == symbol:
                logger.info(f"Retrieved paper trading order {order_id} for {symbol}")
                return order
        
        logger.warning(f"Order {order_id} for {symbol} not found")
        raise ValueError(f"Order {order_id} for {symbol} not found")
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open paper trading orders.
        
        Args:
            symbol: Trading pair symbol (optional)
            
        Returns:
            List of open orders
        """
        if symbol:
            open_orders = [order for order in self.orders if order['symbol'] == symbol and order['status'] == 'NEW']
        else:
            open_orders = [order for order in self.orders if order['status'] == 'NEW']
        
        logger.info(f"Retrieved {len(open_orders)} open paper trading orders")
        return open_orders
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get paper trading account balance.
        
        Returns:
            Dictionary mapping assets to their balances
        """
        logger.info(f"Retrieved paper trading account balance: {self.balances}")
        return self.balances
    
    def place_trailing_stop_order(self, symbol: str, side: str, quantity: float, 
                                 activation_price: float, callback_rate: float) -> Dict[str, Any]:
        """
        Place a paper trading trailing stop order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            activation_price: Activation price for the trailing stop
            callback_rate: Callback rate in percentage
            
        Returns:
            Order information
        """
        # Check with risk manager if this order is allowed
        if not self.risk_manager.check_order(symbol, side, quantity, activation_price):
            logger.warning(f"Order rejected by risk manager: {side} {quantity} {symbol} at {activation_price}")
            raise ValueError("Order rejected by risk manager")
        
        # Generate order ID
        order_id = f"paper_trailing_{int(time.time() * 1000)}"
        
        # Create order object
        order = {
            'orderId': order_id,
            'symbol': symbol,
            'side': side,
            'type': 'TRAILING_STOP_MARKET',
            'quantity': quantity,
            'activationPrice': activation_price,
            'callbackRate': callback_rate,
            'status': 'NEW',
            'time': int(time.time() * 1000),
            'updateTime': int(time.time() * 1000)
        }
        
        # Add to open orders
        self.orders.append(order)
        
        # Save state
        self._save_state()
        
        logger.info(f"Placed paper trading trailing stop {side} order for {quantity} {symbol}: {order_id}")
        return order
    
    def update_positions(self, current_prices: Dict[str, float]) -> None:
        """
        Update paper trading positions with current prices.
        
        Args:
            current_prices: Dictionary mapping symbols to their current prices
        """
        for position in self.positions:
            symbol = position['symbol']
            if symbol in current_prices:
                position['current_price'] = current_prices[symbol]
        
        # Save state
        self._save_state()
        
        logger.info(f"Updated {len(self.positions)} paper trading positions with current prices")
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all paper trading positions.
        
        Returns:
            List of positions
        """
        logger.info(f"Retrieved {len(self.positions)} paper trading positions")
        return self.positions
    
    def close_position(self, position_index: int) -> Dict[str, Any]:
        """
        Close a paper trading position.
        
        Args:
            position_index: Index of the position to close
            
        Returns:
            Position information
        """
        if position_index < 0 or position_index >= len(self.positions):
            logger.warning(f"Position index {position_index} out of range")
            raise ValueError(f"Position index {position_index} out of range")
        
        position = self.positions[position_index]
        symbol = position['symbol']
        side = 'SELL' if position['side'] == 'LONG' else 'BUY'
        quantity = position['quantity']
        current_price = position['current_price']
        
        # Place a market order to close the position
        self.place_order(
            symbol=symbol,
            side=side,
            order_type='MARKET',
            quantity=quantity,
            price=current_price
        )
        
        # Calculate profit/loss
        entry_price = position['entry_price']
        if position['side'] == 'LONG':
            pnl = (current_price - entry_price) * quantity
        else:
            pnl = (entry_price - current_price) * quantity
        
        # Add profit/loss information to position
        position['exit_price'] = current_price
        position['exit_time'] = int(time.time() * 1000)
        position['pnl'] = pnl
        position['pnl_percent'] = (pnl / (entry_price * quantity)) * 100
        position['status'] = 'CLOSED'
        
        # Remove from active positions
        self.positions.pop(position_index)
        
        # Save state
        self._save_state()
        
        logger.info(f"Closed paper trading position for {quantity} {symbol} with PnL: {pnl}")
        return position
