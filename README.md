# Cryptocurrency Trading Bot

A Python-based cryptocurrency trading bot that can monitor the top 10 cryptocurrencies by market cap, analyze market trends using multiple technical indicators, and execute trades on Binance with both paper trading and live trading capabilities.

## Features

- **Data Collection**: Fetches top 10 cryptocurrencies by market cap and retrieves historical and real-time price data from Binance
- **Technical Analysis**: Implements multiple technical indicators (RSI, MACD, Bollinger Bands, Stochastic, ATR, etc.)
- **Custom Strategy**: Combines indicators to generate trading signals with configurable parameters
- **Risk Management**: Implements trailing stop loss and position sizing based on risk parameters
- **Execution**: Supports both paper trading (simulation) and live trading with real funds
- **Performance Tracking**: Tracks and analyzes trading performance with metrics

## Installation

### Prerequisites

- Python 3.8 or higher
- Binance account (for live trading)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-trading-bot.git
cd crypto-trading-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
   - Edit `config/config.yaml` with your settings
   - For live trading, add your Binance API keys

## Configuration

The bot is configured using the `config/config.yaml` file. Here are the main configuration sections:

### Binance Configuration

```yaml
binance:
  api_key: ""  # Your Binance API key
  api_secret: ""  # Your Binance API secret
  testnet: true  # Use testnet for testing
```

### Execution Configuration

```yaml
execution:
  mode: "paper"  # "paper" or "live"
```

### Paper Trading Configuration

```yaml
paper_trading:
  initial_balance: 10000.0  # Initial balance for paper trading
```

### Strategy Configuration

```yaml
strategy:
  # RSI parameters
  rsi_period: 14
  rsi_overbought: 70
  rsi_oversold: 30
  
  # MACD parameters
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  
  # Bollinger Bands parameters
  bb_period: 20
  bb_std_dev: 2.0
  
  # Stochastic parameters
  stoch_k_period: 14
  stoch_d_period: 3
  stoch_smooth_k: 3
  
  # ATR parameters
  atr_period: 14
  atr_multiplier: 2.0
  
  # Trailing stop parameters
  trailing_stop_pct: 2.0
  
  # Signal threshold
  signal_threshold: 3
```

### Risk Management Configuration

```yaml
risk:
  max_position_size: 0.05  # 5% of account
  max_open_positions: 5
  max_daily_loss: 0.03  # 3% of account
  trailing_stop_pct: 0.02  # 2%
```

## Usage

### Running the Bot

To start the bot, run:

```bash
python src/main.py
```

### Testing Individual Modules

To test individual modules:

```bash
# Test data collection
python tests/test_data_collection.py

# Test strategy
python tests/test_strategy.py

# Test execution
python tests/test_execution.py

# Run integration test
python tests/test_integration.py
```

## Project Structure

```
crypto_trading_bot/
├── config/
│   └── config.yaml
├── data/
│   └── historical/
├── logs/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── data_collection/
│   │   ├── __init__.py
│   │   ├── market_data_provider.py
│   │   ├── binance_data_provider.py
│   │   └── data_preprocessor.py
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── strategy.py
│   │   ├── indicator_calculator.py
│   │   ├── custom_strategy.py
│   │   └── signal_generator.py
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── order_executor.py
│   │   ├── binance_executor.py
│   │   ├── paper_trading_executor.py
│   │   └── position_manager.py
│   ├── risk_management/
│   │   ├── __init__.py
│   │   └── risk_manager.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── config_manager.py
│   └── logging/
│       ├── __init__.py
│       └── logger.py
├── tests/
│   ├── test_data_collection.py
│   ├── test_strategy.py
│   ├── test_execution.py
│   └── test_integration.py
└── requirements.txt
```

## Module Descriptions

### Data Collection Module

The data collection module is responsible for fetching market data from Binance. It includes:

- **BinanceDataProvider**: Fetches data from Binance API
- **DataPreprocessor**: Cleans and prepares data for analysis

### Strategy Module

The strategy module analyzes market data and generates trading signals. It includes:

- **IndicatorCalculator**: Calculates technical indicators
- **CustomStrategy**: Implements the trading strategy
- **SignalGenerator**: Generates and filters trading signals

### Execution Module

The execution module executes trades based on signals. It includes:

- **OrderExecutor**: Interface for order execution
- **BinanceExecutor**: Executes orders on Binance
- **PaperTradingExecutor**: Simulates order execution
- **PositionManager**: Manages trading positions

### Risk Management Module

The risk management module handles risk management. It includes:

- **RiskManager**: Implements risk management strategies

## Custom Strategy

The bot uses a custom strategy that combines multiple technical indicators:

1. **RSI (Relative Strength Index)**: Identifies overbought and oversold conditions
2. **MACD (Moving Average Convergence Divergence)**: Identifies trend changes
3. **Bollinger Bands**: Identifies volatility and potential price targets
4. **Stochastic Oscillator**: Identifies momentum and potential reversals
5. **ATR (Average True Range)**: Measures volatility for stop loss placement

The strategy generates buy signals when multiple indicators align in a bullish direction and sell signals when they align in a bearish direction.

## Trailing Stop Loss

The bot implements a trailing stop loss mechanism that automatically adjusts the stop loss price as the price moves in favor of the trade. This helps lock in profits while allowing the trade to continue if the price keeps moving favorably.

## Paper Trading vs. Live Trading

The bot supports two trading modes:

- **Paper Trading**: Simulates trading without using real funds. This is useful for testing strategies.
- **Live Trading**: Executes real trades on Binance using your API keys.

To switch between modes, change the `execution.mode` setting in the configuration file.

## Performance Metrics

The bot tracks various performance metrics:

- Win rate
- Profit factor
- Average profit/loss
- Maximum drawdown
- Total return

These metrics can be accessed through the `get_performance_metrics()` method of the position manager.

## Warning

Trading cryptocurrencies involves significant risk and can result in the loss of your invested capital. Always start with paper trading and small amounts when transitioning to live trading.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
