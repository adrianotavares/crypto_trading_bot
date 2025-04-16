"""
Binance implementation of the market data provider.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import requests

from src.data_collection.market_data_provider import MarketDataProvider
from src.data_collection.data_preprocessor import DataPreprocessor

logger = logging.getLogger(__name__)

class BinanceDataProvider(MarketDataProvider):
    """
    Implementation of MarketDataProvider for Binance exchange.
    """
    
    def __init__(self, config):
        """
        Initialize the Binance data provider.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.api_key = config.get('binance', 'api_key', default='')
        self.api_secret = config.get('binance', 'api_secret', default='')
        self.testnet = config.get('binance', 'testnet', default=False)
        
        # Initialize Binance client
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        
        # Initialize data preprocessor
        self.preprocessor = DataPreprocessor()
        
        logger.info("Binance data provider initialized")
    
    def get_top_cryptocurrencies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top cryptocurrencies by market cap from CoinMarketCap API.
        
        Args:
            limit: Number of cryptocurrencies to return
            
        Returns:
            List of dictionaries containing cryptocurrency information
        """
        try:
            # First, try to get data from Binance
            exchange_info = self.client.get_exchange_info()
            tickers = self.client.get_ticker()
            
            # Filter for USDT pairs and sort by volume
            usdt_tickers = [t for t in tickers if t['symbol'].endswith('USDT')]
            sorted_tickers = sorted(usdt_tickers, key=lambda x: float(x['quoteVolume']), reverse=True)
            
            # Get the top N by volume
            top_tickers = sorted_tickers[:limit]
            
            # Format the result
            result = []
            for ticker in top_tickers:
                symbol = ticker['symbol']
                base_asset = symbol[:-4]  # Remove 'USDT'
                result.append({
                    'symbol': symbol,
                    'baseAsset': base_asset,
                    'quoteAsset': 'USDT',
                    'price': float(ticker['lastPrice']),
                    'volume': float(ticker['quoteVolume']),
                    'change24h': float(ticker['priceChangePercent'])
                })
            
            logger.info(f"Retrieved top {limit} cryptocurrencies from Binance")
            return result
            
        except BinanceAPIException as e:
            logger.error(f"Error getting top cryptocurrencies from Binance: {e}")
            raise
    
    def get_historical_data(self, symbol: str, interval: str, 
                           start_time: Optional[str] = None, 
                           end_time: Optional[str] = None,
                           limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get historical OHLCV data for a specific cryptocurrency.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1h', '1d')
            start_time: Start time in ISO format
            end_time: End time in ISO format
            limit: Maximum number of candles to return
            
        Returns:
            DataFrame with historical data
        """
        try:
            # Convert ISO format to milliseconds timestamp if provided
            start_ms = None
            end_ms = None
            
            if start_time:
                start_ms = int(pd.Timestamp(start_time).timestamp() * 1000)
            if end_time:
                end_ms = int(pd.Timestamp(end_time).timestamp() * 1000)
            
            # Get klines from Binance
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_ms,
                end_str=end_ms,
                limit=limit
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Preprocess the data
            df = self.preprocessor.preprocess_ohlcv(df)
            
            logger.info(f"Retrieved historical data for {symbol} at {interval} interval")
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Error getting historical data from Binance: {e}")
            raise
    
    def get_ticker_data(self, symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get current ticker data for specified symbols.
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dictionary mapping symbols to their ticker data
        """
        try:
            if symbols:
                # Get ticker data for specific symbols
                tickers = {}
                for symbol in symbols:
                    ticker = self.client.get_ticker(symbol=symbol)
                    tickers[symbol] = ticker
            else:
                # Get all ticker data
                all_tickers = self.client.get_ticker()
                tickers = {t['symbol']: t for t in all_tickers}
            
            logger.info(f"Retrieved ticker data for {len(tickers)} symbols")
            return tickers
            
        except BinanceAPIException as e:
            logger.error(f"Error getting ticker data from Binance: {e}")
            raise
    
    def setup_websocket(self, symbols: List[str], interval: str, callback) -> Any:
        """
        Set up a websocket connection for real-time data.
        
        Args:
            symbols: List of trading pair symbols
            interval: Time interval for kline data
            callback: Callback function to handle incoming data
            
        Returns:
            Websocket connection object
        """
        try:
            from binance.websockets import BinanceSocketManager
            
            # Initialize socket manager
            bm = BinanceSocketManager(self.client)
            
            # Start kline socket for each symbol
            conn_keys = []
            for symbol in symbols:
                conn_key = bm.start_kline_socket(
                    symbol=symbol,
                    interval=interval,
                    callback=callback
                )
                conn_keys.append(conn_key)
            
            # Start the socket manager
            bm.start()
            
            logger.info(f"Started websocket for {len(symbols)} symbols with {interval} interval")
            return bm
            
        except Exception as e:
            logger.error(f"Error setting up websocket: {e}")
            raise
