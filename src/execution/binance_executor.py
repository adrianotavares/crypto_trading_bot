"""
Binance implementation of the order executor.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException

from src.execution.order_executor import OrderExecutor
from src.risk_management.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class BinanceExecutor(OrderExecutor):
    """
    Implementation of OrderExecutor for Binance exchange.
    """
    
    def __init__(self, config, risk_manager: RiskManager):
        """
        Initialize the Binance executor.
        
        Args:
            config: Configuration manager instance
            risk_manager: Risk manager instance
        """
        self.config = config
        self.risk_manager = risk_manager
        
        # Get API credentials
        self.api_key = config.get('binance', 'api_key', default='')
        self.api_secret = config.get('binance', 'api_secret', default='')
        self.testnet = config.get('binance', 'testnet', default=False)
        
        # Initialize Binance client
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        
        # Set trading mode
        self.trading_mode = config.get('execution', 'mode', default='paper')
        
        logger.info(f"Binance executor initialized in {self.trading_mode} mode")
        
        # Validate API connection
        if self.trading_mode == 'live' and (not self.api_key or not self.api_secret):
            logger.error("API credentials not provided for live trading")
            raise ValueError("API credentials required for live trading")
        
        if self.trading_mode == 'live':
            try:
                self.client.get_account()
                logger.info("Successfully connected to Binance API")
            except BinanceAPIException as e:
                logger.error(f"Failed to connect to Binance API: {e}")
                raise
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: Optional[float] = None,
                   stop_price: Optional[float] = None,
                   time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place an order on Binance.
        
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
        # Check if we're in paper trading mode
        if self.trading_mode == 'paper':
            logger.info(f"Paper trading: Would place {side} {order_type} order for {quantity} {symbol}")
            
            # Simulate order response
            order_id = f"paper_{int(time.time() * 1000)}"
            return {
                'symbol': symbol,
                'orderId': order_id,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'price': price,
                'stopPrice': stop_price,
                'status': 'FILLED',  # Assume immediate fill for paper trading
                'time': int(time.time() * 1000)
            }
        
        # Check with risk manager if this order is allowed
        if not self.risk_manager.check_order(symbol, side, quantity, price):
            logger.warning(f"Order rejected by risk manager: {side} {quantity} {symbol} at {price}")
            raise ValueError("Order rejected by risk manager")
        
        try:
            # Prepare order parameters
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            
            # Add price for limit orders
            if order_type in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']:
                if price is None:
                    raise ValueError(f"Price is required for {order_type} orders")
                params['price'] = price
                params['timeInForce'] = time_in_force
            
            # Add stop price for stop orders
            if order_type in ['STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT']:
                if stop_price is None:
                    raise ValueError(f"Stop price is required for {order_type} orders")
                params['stopPrice'] = stop_price
            
            # Place the order
            order = self.client.create_order(**params)
            
            logger.info(f"Placed {side} {order_type} order for {quantity} {symbol}: {order['orderId']}")
            return order
            
        except BinanceAPIException as e:
            logger.error(f"Error placing order on Binance: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order on Binance.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Cancellation information
        """
        # Check if we're in paper trading mode
        if self.trading_mode == 'paper':
            logger.info(f"Paper trading: Would cancel order {order_id} for {symbol}")
            
            # Simulate cancellation response
            return {
                'symbol': symbol,
                'orderId': order_id,
                'status': 'CANCELED',
                'time': int(time.time() * 1000)
            }
        
        try:
            # Cancel the order
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            
            logger.info(f"Cancelled order {order_id} for {symbol}")
            return result
            
        except BinanceAPIException as e:
            logger.error(f"Error cancelling order on Binance: {e}")
            raise
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Get information about an order on Binance.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Order information
        """
        # Check if we're in paper trading mode
        if self.trading_mode == 'paper':
            logger.info(f"Paper trading: Would get order {order_id} for {symbol}")
            
            # Simulate order information
            return {
                'symbol': symbol,
                'orderId': order_id,
                'status': 'FILLED',  # Assume filled for paper trading
                'time': int(time.time() * 1000)
            }
        
        try:
            # Get the order
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            
            logger.info(f"Retrieved order {order_id} for {symbol}: {order['status']}")
            return order
            
        except BinanceAPIException as e:
            logger.error(f"Error getting order from Binance: {e}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders on Binance.
        
        Args:
            symbol: Trading pair symbol (optional)
            
        Returns:
            List of open orders
        """
        # Check if we're in paper trading mode
        if self.trading_mode == 'paper':
            logger.info(f"Paper trading: Would get open orders for {symbol if symbol else 'all symbols'}")
            
            # Simulate empty open orders list
            return []
        
        try:
            # Get open orders
            if symbol:
                orders = self.client.get_open_orders(symbol=symbol)
            else:
                orders = self.client.get_open_orders()
            
            logger.info(f"Retrieved {len(orders)} open orders")
            return orders
            
        except BinanceAPIException as e:
            logger.error(f"Error getting open orders from Binance: {e}")
            raise
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance from Binance.
        
        Returns:
            Dictionary mapping assets to their balances
        """
        # Check if we're in paper trading mode
        if self.trading_mode == 'paper':
            logger.info("Paper trading: Would get account balance")
            
            # Simulate account balance
            paper_balance = self.config.get('paper_trading', 'initial_balance', default=10000.0)
            return {
                'USDT': paper_balance,
                'BTC': 0.0,
                'ETH': 0.0
            }
        
        try:
            # Get account information
            account = self.client.get_account()
            
            # Extract balances
            balances = {}
            for asset in account['balances']:
                free = float(asset['free'])
                locked = float(asset['locked'])
                total = free + locked
                
                if total > 0:
                    balances[asset['asset']] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            logger.info(f"Retrieved account balance for {len(balances)} assets")
            return balances
            
        except BinanceAPIException as e:
            logger.error(f"Error getting account balance from Binance: {e}")
            raise
    
    def place_trailing_stop_order(self, symbol: str, side: str, quantity: float, 
                                 activation_price: float, callback_rate: float) -> Dict[str, Any]:
        """
        Place a trailing stop order on Binance.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            activation_price: Activation price for the trailing stop
            callback_rate: Callback rate in percentage
            
        Returns:
            Order information
        """
        # Check if we're in paper trading mode
        if self.trading_mode == 'paper':
            logger.info(f"Paper trading: Would place trailing stop {side} order for {quantity} {symbol}")
            
            # Simulate order response
            order_id = f"paper_trailing_{int(time.time() * 1000)}"
            return {
                'symbol': symbol,
                'orderId': order_id,
                'side': side,
                'type': 'TRAILING_STOP_MARKET',
                'quantity': quantity,
                'activationPrice': activation_price,
                'callbackRate': callback_rate,
                'status': 'NEW',
                'time': int(time.time() * 1000)
            }
        
        # Check with risk manager if this order is allowed
        if not self.risk_manager.check_order(symbol, side, quantity, activation_price):
            logger.warning(f"Order rejected by risk manager: {side} {quantity} {symbol} at {activation_price}")
            raise ValueError("Order rejected by risk manager")
        
        try:
            # Note: Trailing stop orders are only available on Binance Futures
            # For spot trading, we would need to implement this manually
            
            # Check if we're using futures
            if not self.config.get('binance', 'futures', default=False):
                logger.error("Trailing stop orders are only available on Binance Futures")
                raise NotImplementedError("Trailing stop orders are only available on Binance Futures")
            
            # Place the trailing stop order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='TRAILING_STOP_MARKET',
                quantity=quantity,
                activationPrice=activation_price,
                callbackRate=callback_rate
            )
            
            logger.info(f"Placed trailing stop {side} order for {quantity} {symbol}: {order['orderId']}")
            return order
            
        except BinanceAPIException as e:
            logger.error(f"Error placing trailing stop order on Binance: {e}")
            raise
