# Main entry point for the cryptocurrency trading bot.

import os
import sys
from pathlib import Path

# Add the project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import logging
import time
import argparse
import signal
import pandas as pd

from src.config.config_manager import ConfigManager
from src.logging.logger import setup_logger
from src.data_collection import DataCollectionModule
from src.strategy import StrategyModule
from src.risk_management.risk_manager import RiskManager
from src.execution import ExecutionModule

class TradingBot:
    """
    Main trading bot class that orchestrates all components.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the trading bot.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        # Setup logging
        self.logger = setup_logger(log_level=logging.INFO)
        self.logger.info("Initializing trading bot...")
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        self.config = ConfigManager(config_path)
        self.logger.info(f"Configuration loaded from {config_path}")
        
        # Initialize components
        self.risk_manager = RiskManager(self.config)
        self.data_collection = DataCollectionModule(self.config)
        self.strategy = StrategyModule(self.config)
        self.execution = ExecutionModule(self.config, self.risk_manager)
        
        # Trading parameters
        self.trading_interval = self.config.get('bot', 'trading_interval', default=3600)  # Default: 1 hour
        self.top_n_cryptos = self.config.get('bot', 'top_n_cryptos', default=10)
        self.running = False
        
        self.logger.info("Trading bot initialized")
    
    def start(self):
        """
        Start the trading bot.
        """
        self.logger.info("Starting trading bot...")
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Main trading loop
            while self.running:
                self.logger.info("Starting trading cycle...")
                
                try:
                    # Step 1: Get top trading pairs
                    # trading_pairs = self.data_collection.get_top_trading_pairs(limit=self.top_n_cryptos)
                    trading_pairs = self.config.get('bot', 'trading_pairs', default=['BTCUSDT'])
                    self.logger.info(f"Top {len(trading_pairs)} trading pairs: {trading_pairs}")
                    
                    candle_interval = self.config.get('bot', 'candle_interval', default='1h')
                    self.logger.info(f"Candle interval: {candle_interval}")
                    
                    # Step 2: Get historical data for pairs
                    historical_data = self.data_collection.get_historical_data_for_pairs(
                        trading_pairs=trading_pairs,
                        interval=candle_interval,
                        days=7
                    )
                    self.logger.info(f"Retrieved historical data for {len(historical_data)} pairs")
                    
                    # Step 3: Analyze data and generate signals
                    analyzed_data = self.strategy.analyze_data(historical_data)
                    self.logger.info(f"Analyzed data for {len(analyzed_data)} pairs")
                    
                    # Step 4: Get trading opportunities
                    opportunities = self.strategy.get_trading_opportunities(analyzed_data)
                    self.logger.info(f"Found {len(opportunities)} trading opportunities")
                    
                    # Step 5: Execute signals
                    if opportunities:
                        executed_positions = self.execution.execute_signals(opportunities)
                        self.logger.info(f"Executed {len(executed_positions)} positions")
                    
                    # Step 6: Update positions with current prices
                    current_prices = {}
                    for pair in trading_pairs:
                        if pair in historical_data:
                            current_prices[pair] = historical_data[pair].iloc[-1]['Close']
                    
                    self.execution.update_positions(current_prices)
                    self.logger.info("Updated positions with current prices")
                    
                    # Step 7: Get exit signals
                    open_positions = self.execution.get_open_positions()
                    exit_signals = self.strategy.get_exit_signals(analyzed_data, open_positions)
                    self.logger.info(f"Found {len(exit_signals)} exit signals")
                    
                    # Step 8: Execute exit signals
                    if exit_signals:
                        closed_positions = self.execution.execute_exit_signals(exit_signals)
                        self.logger.info(f"Closed {len(closed_positions)} positions")
                    
                    # Step 9: Get performance metrics
                    metrics = self.execution.get_performance_metrics()
                    self.logger.info(f"Performance metrics: {metrics}")
                    
                except Exception as e:
                    self.logger.error(f"Error in trading cycle: {e}")
                
                # Wait for next cycle
                self.logger.info(f"Trading cycle completed. Waiting {self.trading_interval} seconds for next cycle...")
                # time.sleep(self.trading_interval)
                for _ in range(self.trading_interval):
                    if not self.running:
                        break
                    time.sleep(1)
        
        except Exception as e:
            self.logger.error(f"Critical error in trading bot: {e}")
        
        finally:
            self.logger.info("Trading bot stopped")
    
    def stop(self):
        """
        Stop the trading bot.
        """
        self.logger.info("Stopping trading bot...")
        self.running = False
    
    def _signal_handler(self, sig, frame):
        """
        Handle signals for graceful shutdown.
        """
        self.logger.info(f"Received signal {sig}. Shutting down...")
        self.stop()

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Cryptocurrency Trading Bot')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--mode', type=str, choices=['paper', 'live'], help='Trading mode')
    parser.add_argument('--interval', type=int, help='Trading interval in seconds')
    parser.add_argument('--top', type=int, help='Number of top cryptocurrencies to trade')
    
    return parser.parse_args()

def main():
    """
    Main entry point.
    """
    # Parse arguments
    args = parse_arguments()
    
    # Create trading bot
    bot = TradingBot(config_path=args.config)
    
    # Override configuration with command line arguments
    if args.mode:
        bot.config.set('execution', 'mode', args.mode)
    
    if args.interval:
        bot.trading_interval = args.interval
    
    if args.top:
        bot.top_n_cryptos = args.top
    
    # Start trading bot
    bot.start()

if __name__ == "__main__":
    main()
