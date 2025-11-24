# IBKR Portfolio Manager - Modular Structure

This project has been refactored into separate modules for better organization and maintainability.

## Module Overview

### 1. `connection.py` - Connection Management
Handles establishing and managing connections to Interactive Brokers.

**Key Classes:**
- `IBConnection`: Manages IB TWS/Gateway connections

**Usage:**
```python
from connection import IBConnection

conn = IBConnection(host='127.0.0.1', port=4002, client_id=1)
ib = conn.connect()
# ... do work ...
conn.disconnect()
```

### 2. `transactions.py` - Trade Execution
Handles all trading operations including buying, selling, and order management.

**Key Classes:**
- `TransactionManager`: Executes trades and monitors order status

**Usage:**
```python
from transactions import TransactionManager

tm = TransactionManager(ib)
trade = tm.place_buy_async(symbol="QQQ", qty=10)
tm.wait_for_trade_completion(trade)
```

### 3. `portfolio_manager.py` - Portfolio Management
Manages portfolio operations including rebalancing calculations and position tracking.

**Key Classes:**
- `PortfolioManager`: Handles portfolio analysis and rebalancing logic

**Usage:**
```python
from portfolio_manager import PortfolioManager

pm = PortfolioManager(ib)
positions = pm.get_portfolio_positions()
portfolio_value = pm.get_portfolio_value()

# Calculate rebalancing
target_allocations = {'SPY': 60.0, 'TLT': 40.0}
target_amounts = pm.calculate_target_allocations(target_allocations)
trades = pm.calculate_rebalance_trades(target_amounts)
```

### 4. `display.py` - Data Display
Provides formatting and display utilities for portfolio data and reports.

**Key Classes:**
- `PortfolioDisplay`: Static methods for formatting and displaying data

**Usage:**
```python
from display import PortfolioDisplay

display = PortfolioDisplay()
display.print_positions(positions)
display.print_account_summary(summary)
display.print_rebalance_plan(trades)
```

## Main Entry Point

### `main.py` - Complete Portfolio Manager
Main script that orchestrates the entire workflow:
1. Loads configuration from JSON file
2. Connects to Interactive Brokers
3. Displays current portfolio status
4. Calculates rebalancing trades based on target allocations
5. Executes trades (with confirmation for live trading)

**Features:**
- JSON-based configuration
- Dry run mode for safe testing
- Minimum trade value threshold
- Automatic allocation validation
- Detailed progress reporting

## Example Usage

See `example_usage.py` for additional working examples including:
- Simple buy orders
- Viewing portfolio positions
- Calculating rebalancing plans
- Executing multiple trades

## Legacy Files

- `test2.py` - Original monolithic implementation (can be removed)
- `api.py` - REST API implementation (different approach)
- `portfolio_rebalancer.py` - Previous rebalancing logic (different approach)

## Quick Start

### Using Main Script with JSON Configuration

1. Edit `config.json` to set your target allocations:
```json
{
  "connection": {
    "host": "127.0.0.1",
    "port": 4002,
    "client_id": 1
  },
  "allocations": {
    "SPY": 40.0,
    "QQQ": 30.0,
    "IWM": 20.0,
    "TLT": 10.0
  },
  "settings": {
    "dry_run": true,
    "min_trade_value": 10.0
  }
}
```

2. Run the main script:
```bash
python main.py
```

Or with a custom config file:
```bash
python main.py my_config.json
```

The script will:
- Connect to IB
- Display your current portfolio
- Calculate rebalancing trades
- Execute trades (with confirmation if not in dry_run mode)

### Programmatic Usage

```python
from connection import IBConnection
from transactions import TransactionManager
from portfolio_manager import PortfolioManager
from display import PortfolioDisplay

# Connect
conn = IBConnection(host='127.0.0.1', port=4002, client_id=1)
ib = conn.connect()

try:
    # View portfolio
    pm = PortfolioManager(ib)
    display = PortfolioDisplay()
    
    positions = pm.get_portfolio_positions()
    display.print_positions(positions)
    
    # Execute trades
    tm = TransactionManager(ib)
    trade = tm.place_buy_async("SPY", qty=5)
    tm.wait_for_trade_completion(trade)
    
finally:
    conn.disconnect()
```

## Port Configuration

- `4002` - Paper trading
- `4001` - Live trading

## Requirements

- `ib_insync` library
- Interactive Brokers TWS or IB Gateway running
- Active IB account (paper or live)
