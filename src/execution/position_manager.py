"""
Position manager for tracking and managing trading positions.
"""

import logging
import time
from typing import Dict, List, Any, Optional
import pandas as pd

from src.execution.order_executor import OrderExecutor
from src.risk_management.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class PositionManager:
    """
    Manages trading positions and their lifecycle.
    """
    
    def __init__(self, config, executor: OrderExecutor, risk_manager: RiskManager):
        """
        Initialize the position manager.
        
        Args:
            config: Configuration manager instance
            executor: Order executor instance
            risk_manager: Risk manager instance
        """
        self.config = config
        self.executor = executor
        self.risk_manager = risk_manager
        
        # Position tracking
        self.positions = []
        self.position_history = []
        
        logger.info("Position manager initialized")
    
    def open_position(self, symbol: str, side: str, quantity: float, 
                     price: Optional[float] = None, stop_loss: Optional[float] = None,
                     take_profit: Optional[float] = None) -> Dict[str, Any]:
        """
        Open a new trading position.
        
        Args:
            symbol: Trading pair symbol
            side: Position side ('LONG' or 'SHORT')
            quantity: Position size
            price: Entry price (optional, uses market price if not provided)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            
        Returns:
            Position information
        """
        # Convert position side to order side
        order_side = 'BUY' if side == 'LONG' else 'SELL'
        
        # Check with risk manager
        position_size = self.risk_manager.calculate_position_size(symbol, side, price)
        if quantity > position_size:
            logger.warning(f"Position size {quantity} exceeds risk limit {position_size}")
            quantity = position_size
        
        # Place the order
        order = self.executor.place_order(
            symbol=symbol,
            side=order_side,
            order_type='MARKET',
            quantity=quantity,
            price=price
        )
        
        # Create position object
        position = {
            'id': f"pos_{int(time.time() * 1000)}",
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'entry_price': price or float(order.get('price', 0)),
            'entry_time': int(time.time() * 1000),
            'entry_order_id': order.get('orderId'),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'status': 'OPEN',
            'pnl': 0.0,
            'pnl_percent': 0.0
        }
        
        # Place stop loss order if provided
        if stop_loss:
            sl_side = 'SELL' if side == 'LONG' else 'BUY'
            try:
                sl_order = self.executor.place_order(
                    symbol=symbol,
                    side=sl_side,
                    order_type='STOP_LOSS',
                    quantity=quantity,
                    stop_price=stop_loss
                )
                position['stop_loss_order_id'] = sl_order.get('orderId')
            except Exception as e:
                logger.error(f"Error placing stop loss order: {e}")
        
        # Place take profit order if provided
        if take_profit:
            tp_side = 'SELL' if side == 'LONG' else 'BUY'
            try:
                tp_order = self.executor.place_order(
                    symbol=symbol,
                    side=tp_side,
                    order_type='TAKE_PROFIT',
                    quantity=quantity,
                    stop_price=take_profit
                )
                position['take_profit_order_id'] = tp_order.get('orderId')
            except Exception as e:
                logger.error(f"Error placing take profit order: {e}")
        
        # Add to positions
        self.positions.append(position)
        
        logger.info(f"Opened {side} position for {quantity} {symbol} at {position['entry_price']}")
        return position
    
    def close_position(self, position_id: str, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Close an existing trading position.
        
        Args:
            position_id: Position ID
            price: Exit price (optional, uses market price if not provided)
            
        Returns:
            Position information
        """
        # Find the position
        position = None
        position_index = -1
        
        for i, pos in enumerate(self.positions):
            if pos['id'] == position_id:
                position = pos
                position_index = i
                break
        
        if not position:
            logger.warning(f"Position {position_id} not found")
            raise ValueError(f"Position {position_id} not found")
        
        # Convert position side to order side (opposite for closing)
        order_side = 'SELL' if position['side'] == 'LONG' else 'BUY'
        
        # Place the order
        order = self.executor.place_order(
            symbol=position['symbol'],
            side=order_side,
            order_type='MARKET',
            quantity=position['quantity'],
            price=price
        )
        
        # Cancel any existing stop loss or take profit orders
        if 'stop_loss_order_id' in position:
            try:
                self.executor.cancel_order(position['symbol'], position['stop_loss_order_id'])
            except Exception as e:
                logger.error(f"Error cancelling stop loss order: {e}")
        
        if 'take_profit_order_id' in position:
            try:
                self.executor.cancel_order(position['symbol'], position['take_profit_order_id'])
            except Exception as e:
                logger.error(f"Error cancelling take profit order: {e}")
        
        # Update position
        exit_price = price or float(order.get('price', 0))
        position['exit_price'] = exit_price
        position['exit_time'] = int(time.time() * 1000)
        position['exit_order_id'] = order.get('orderId')
        position['status'] = 'CLOSED'
        
        # Calculate profit/loss
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        if position['side'] == 'LONG':
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity
        
        position['pnl'] = pnl
        position['pnl_percent'] = (pnl / (entry_price * quantity)) * 100
        
        # Move to position history
        self.position_history.append(position)
        self.positions.pop(position_index)
        
        logger.info(f"Closed {position['side']} position for {quantity} {position['symbol']} " +
                   f"at {exit_price} with PnL: {pnl:.2f} ({position['pnl_percent']:.2f}%)")
        return position
    
    def update_position(self, position_id: str, current_price: float) -> Dict[str, Any]:
        """
        Update a position with current price information.
        
        Args:
            position_id: Position ID
            current_price: Current price
            
        Returns:
            Updated position information
        """
        # Find the position
        position = None
        
        for pos in self.positions:
            if pos['id'] == position_id:
                position = pos
                break
        
        if not position:
            logger.warning(f"Position {position_id} not found")
            raise ValueError(f"Position {position_id} not found")
        
        # Update current price
        position['current_price'] = current_price
        
        # Calculate unrealized profit/loss
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        if position['side'] == 'LONG':
            pnl = (current_price - entry_price) * quantity
        else:
            pnl = (entry_price - current_price) * quantity
        
        position['unrealized_pnl'] = pnl
        position['unrealized_pnl_percent'] = (pnl / (entry_price * quantity)) * 100
        
        logger.debug(f"Updated {position['side']} position for {quantity} {position['symbol']} " +
                    f"at {current_price} with unrealized PnL: {pnl:.2f} ({position['unrealized_pnl_percent']:.2f}%)")
        return position
    
    def update_trailing_stop(self, position_id: str, current_price: float) -> Dict[str, Any]:
        """
        Update trailing stop for a position.
        
        Args:
            position_id: Position ID
            current_price: Current price
            
        Returns:
            Updated position information
        """
        # Find the position
        position = None
        
        for pos in self.positions:
            if pos['id'] == position_id:
                position = pos
                break
        
        if not position:
            logger.warning(f"Position {position_id} not found")
            raise ValueError(f"Position {position_id} not found")
        
        # Check if trailing stop is enabled
        if not position.get('trailing_stop_enabled', False):
            logger.debug(f"Trailing stop not enabled for position {position_id}")
            return position
        
        # Get trailing stop parameters
        activation_price = position.get('trailing_stop_activation_price')
        callback_rate = position.get('trailing_stop_callback_rate', 1.0)  # Default 1%
        
        # Check if trailing stop is activated
        if position['side'] == 'LONG':
            # For long positions, trailing stop activates when price rises above activation price
            if current_price > activation_price:
                # Calculate new stop loss price
                new_stop_loss = current_price * (1 - callback_rate / 100)
                
                # Update stop loss if it's higher than the current one
                if not position.get('stop_loss') or new_stop_loss > position['stop_loss']:
                    position['stop_loss'] = new_stop_loss
                    
                    # Update stop loss order if it exists
                    if 'stop_loss_order_id' in position:
                        try:
                            # Cancel existing order
                            self.executor.cancel_order(position['symbol'], position['stop_loss_order_id'])
                            
                            # Place new order
                            sl_order = self.executor.place_order(
                                symbol=position['symbol'],
                                side='SELL',
                                order_type='STOP_LOSS',
                                quantity=position['quantity'],
                                stop_price=new_stop_loss
                            )
                            position['stop_loss_order_id'] = sl_order.get('orderId')
                            
                            logger.info(f"Updated trailing stop for {position['symbol']} to {new_stop_loss}")
                        except Exception as e:
                            logger.error(f"Error updating trailing stop: {e}")
        else:
            # For short positions, trailing stop activates when price falls below activation price
            if current_price < activation_price:
                # Calculate new stop loss price
                new_stop_loss = current_price * (1 + callback_rate / 100)
                
                # Update stop loss if it's lower than the current one
                if not position.get('stop_loss') or new_stop_loss < position['stop_loss']:
                    position['stop_loss'] = new_stop_loss
                    
                    # Update stop loss order if it exists
                    if 'stop_loss_order_id' in position:
                        try:
                            # Cancel existing order
                            self.executor.cancel_order(position['symbol'], position['stop_loss_order_id'])
                            
                            # Place new order
                            sl_order = self.executor.place_order(
                                symbol=position['symbol'],
                                side='BUY',
                                order_type='STOP_LOSS',
                                quantity=position['quantity'],
                                stop_price=new_stop_loss
                            )
                            position['stop_loss_order_id'] = sl_order.get('orderId')
                            
                            logger.info(f"Updated trailing stop for {position['symbol']} to {new_stop_loss}")
                        except Exception as e:
                            logger.error(f"Error updating trailing stop: {e}")
        
        return position
    
    def enable_trailing_stop(self, position_id: str, activation_price: float, 
                            callback_rate: float = 1.0) -> Dict[str, Any]:
        """
        Enable trailing stop for a position.
        
        Args:
            position_id: Position ID
            activation_price: Price at which trailing stop activates
            callback_rate: Callback rate in percentage
            
        Returns:
            Updated position information
        """
        # Find the position
        position = None
        
        for pos in self.positions:
            if pos['id'] == position_id:
                position = pos
                break
        
        if not position:
            logger.warning(f"Position {position_id} not found")
            raise ValueError(f"Position {position_id} not found")
        
        # Enable trailing stop
        position['trailing_stop_enabled'] = True
        position['trailing_stop_activation_price'] = activation_price
        position['trailing_stop_callback_rate'] = callback_rate
        
        logger.info(f"Enabled trailing stop for {position['symbol']} with activation price {activation_price} " +
                   f"and callback rate {callback_rate}%")
        return position
    
    def get_position(self, position_id: str) -> Dict[str, Any]:
        """
        Get information about a position.
        
        Args:
            position_id: Position ID
            
        Returns:
            Position information
        """
        # Find the position
        for pos in self.positions:
            if pos['id'] == position_id:
                return pos
        
        # Check position history
        for pos in self.position_history:
            if pos['id'] == position_id:
                return pos
        
        logger.warning(f"Position {position_id} not found")
        raise ValueError(f"Position {position_id} not found")
    
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Args:
            symbol: Trading pair symbol (optional)
            
        Returns:
            List of open positions
        """
        if symbol:
            open_positions = [pos for pos in self.positions if pos['symbol'] == symbol]
        else:
            open_positions = self.positions.copy()
        
        logger.info(f"Retrieved {len(open_positions)} open positions")
        return open_positions
    
    def get_position_history(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get position history.
        
        Args:
            symbol: Trading pair symbol (optional)
            
        Returns:
            List of closed positions
        """
        if symbol:
            history = [pos for pos in self.position_history if pos['symbol'] == symbol]
        else:
            history = self.position_history.copy()
        
        logger.info(f"Retrieved {len(history)} closed positions")
        return history
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate performance metrics for all closed positions.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.position_history:
            logger.info("No closed positions to calculate performance metrics")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'average_pnl': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0
            }
        
        # Calculate metrics
        total_trades = len(self.position_history)
        winning_trades = sum(1 for pos in self.position_history if pos['pnl'] > 0)
        losing_trades = sum(1 for pos in self.position_history if pos['pnl'] < 0)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        total_pnl = sum(pos['pnl'] for pos in self.position_history)
        average_pnl = total_pnl / total_trades if total_trades > 0 else 0.0
        
        winning_pnls = [pos['pnl'] for pos in self.position_history if pos['pnl'] > 0]
        losing_pnls = [pos['pnl'] for pos in self.position_history if pos['pnl'] < 0]
        
        average_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0.0
        average_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0.0
        
        gross_profit = sum(winning_pnls)
        gross_loss = abs(sum(losing_pnls))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate maximum drawdown
        equity_curve = []
        current_equity = 0
        
        for pos in sorted(self.position_history, key=lambda x: x['exit_time']):
            current_equity += pos['pnl']
            equity_curve.append(current_equity)
        
        if not equity_curve:
            max_drawdown = 0.0
        else:
            max_equity = 0
            max_drawdown = 0
            
            for equity in equity_curve:
                max_equity = max(max_equity, equity)
                drawdown = max_equity - equity
                max_drawdown = max(max_drawdown, drawdown)
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'average_pnl': average_pnl,
            'average_win': average_win,
            'average_loss': average_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown
        }
        
        logger.info(f"Calculated performance metrics: {metrics}")
        return metrics
