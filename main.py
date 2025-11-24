"""
Main entry point for IBKR Portfolio Manager.
Reads configuration from JSON file and executes portfolio rebalancing.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

from connection import IBConnection
from transactions import TransactionManager
from portfolio_manager import PortfolioManager
from display import PortfolioDisplay


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Dictionary containing configuration
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate required sections
        if 'connection' not in config:
            raise ValueError("Configuration must contain 'connection' section")
        if 'allocations' not in config:
            raise ValueError("Configuration must contain 'allocations' section")
        
        # Validate allocations sum to 100%
        total = sum(config['allocations'].values())
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Allocations must sum to 100%, got {total}%")
        
        return config
    
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def display_current_portfolio(pm: PortfolioManager, display: PortfolioDisplay):
    """Display current portfolio status."""
    print(display.generate_report_header())
    print("CURRENT PORTFOLIO STATUS")
    print("=" * 80)
    
    # Get and display positions
    positions = pm.get_portfolio_positions()
    if positions:
        display.print_positions(positions)
    else:
        print("No current positions.\n")
    
    # Get and display account summary
    summary = pm.get_account_summary()
    display.print_account_summary(summary)
    
    # Display key metrics
    portfolio_value = pm.get_portfolio_value()
    cash_balance = pm.get_cash_balance()
    buying_power = pm.get_buying_power()
    
    print("\nKEY METRICS")
    print("-" * 60)
    print(f"Portfolio Value:  {display.format_currency(portfolio_value)}")
    print(f"Cash Balance:     {display.format_currency(cash_balance)}")
    print(f"Buying Power:     {display.format_currency(buying_power)}")
    print("-" * 60)


def calculate_and_display_rebalance_plan(
    pm: PortfolioManager,
    display: PortfolioDisplay,
    target_allocations: Dict[str, float],
    min_trade_value: float = 10.0
) -> list:
    """
    Calculate and display rebalancing plan.
    
    Args:
        pm: Portfolio manager instance
        display: Display instance
        target_allocations: Target allocation percentages
        min_trade_value: Minimum trade value threshold
    
    Returns:
        List of trades to execute
    """
    print("\n" + "=" * 80)
    print("TARGET ALLOCATIONS")
    print("=" * 80)
    
    portfolio_value = pm.get_portfolio_value()
    
    for symbol, percentage in target_allocations.items():
        target_value = (percentage / 100.0) * portfolio_value
        print(f"{symbol:<10} {display.format_percentage(percentage):<10} "
              f"→ {display.format_currency(target_value)}")
    print()
    
    # Calculate target amounts and trades
    target_amounts = pm.calculate_target_allocations(target_allocations)
    trades = pm.calculate_rebalance_trades(target_amounts)
    
    # Filter out trades below minimum value
    filtered_trades = [
        t for t in trades 
        if abs(t['difference']) >= min_trade_value
    ]
    
    if filtered_trades:
        display.print_rebalance_plan(filtered_trades)
        
        # Calculate total trade value
        total_buy = sum(t['difference'] for t in filtered_trades if t['action'] == 'BUY')
        total_sell = sum(abs(t['difference']) for t in filtered_trades if t['action'] == 'SELL')
        
        print(f"Total Buy Amount:  {display.format_currency(total_buy)}")
        print(f"Total Sell Amount: {display.format_currency(total_sell)}")
        print(f"Number of Trades:  {len(filtered_trades)}")
    else:
        print("✓ Portfolio is already balanced within threshold.")
        print(f"  (No trades exceed ${min_trade_value:.2f} minimum)")
    
    return filtered_trades


def execute_rebalance(
    tm: TransactionManager,
    display: PortfolioDisplay,
    trades: list,
    dry_run: bool = True
):
    """
    Execute rebalancing trades.
    
    Args:
        tm: Transaction manager instance
        display: Display instance
        trades: List of trades to execute
        dry_run: If True, simulate orders without executing
    """
    if not trades:
        return
    
    print("\n" + "=" * 80)
    if dry_run:
        print("DRY RUN MODE - Orders will include what-if analysis")
        print("Note: Orders ARE executed (in paper trading account)")
    else:
        print("EXECUTING TRADES")
    print("=" * 80)
    
    for i, trade_plan in enumerate(trades, 1):
        symbol = trade_plan['symbol']
        action = trade_plan['action']
        quantity = trade_plan['quantity']
        
        print(f"\n[{i}/{len(trades)}] {action} {quantity:.4f} shares of {symbol}")
        
        try:
            if action == 'BUY':
                trade = tm.place_buy_async(
                    symbol=symbol,
                    qty=quantity,
                    dry_run=dry_run
                )
            else:  # SELL
                trade = tm.place_sell_async(
                    symbol=symbol,
                    qty=quantity,
                    dry_run=dry_run
                )
            
            # Wait for completion
            tm.wait_for_trade_completion(trade)
            
            # Display trade info
            trade_info = {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'status': trade.orderStatus.status,
                'filled': trade.orderStatus.filled,
                'avgFillPrice': trade.orderStatus.avgFillPrice or 0.0
            }
            display.print_trade_status(trade_info)
            
        except Exception as e:
            print(f"  ✗ Error executing trade: {e}")
            continue
    
    print("\n" + "=" * 80)
    if dry_run:
        print("DRY RUN COMPLETE - Trades executed in paper account")
    else:
        print("REBALANCING COMPLETE - Trades executed")
    print("=" * 80)


def main(config_path: str = "config.json"):
    """
    Main execution function.
    
    Args:
        config_path: Path to configuration JSON file
    """
    # Load configuration
    print("Loading configuration from", config_path)
    config = load_config(config_path)
    
    # Extract settings
    conn_config = config['connection']
    allocations = config['allocations']
    settings = config.get('settings', {})
    dry_run = settings.get('dry_run', True)
    min_trade_value = settings.get('min_trade_value', 10.0)
    
    # Display configuration
    print("\nConfiguration loaded successfully:")
    print(f"  Host: {conn_config['host']}")
    print(f"  Port: {conn_config['port']} ({'Paper Trading' if conn_config['port'] == 4002 else 'Live Trading'})")
    print(f"  Dry Run: {dry_run}")
    print(f"  Min Trade Value: ${min_trade_value:.2f}")
    print(f"  Target Allocations: {len(allocations)} positions")
    
    # Establish connection
    print("\nConnecting to Interactive Brokers...")
    conn = IBConnection(
        host=conn_config['host'],
        port=conn_config['port'],
        client_id=conn_config['client_id']
    )
    
    try:
        ib = conn.connect()
        
        # Initialize managers
        pm = PortfolioManager(ib)
        tm = TransactionManager(ib)
        display = PortfolioDisplay()
        
        # Step 1: Display current portfolio
        display_current_portfolio(pm, display)
        
        # Step 2: Calculate and display rebalance plan
        trades = calculate_and_display_rebalance_plan(
            pm, display, allocations, min_trade_value
        )
        
        # Step 3: Execute rebalancing (with confirmation if not dry run)
        if trades:
            if not dry_run:
                print("\n" + "!" * 80)
                print("WARNING: You are about to execute REAL trades!")
                print("!" * 80)
                response = input("\nDo you want to proceed? (type 'YES' to confirm): ")
                if response.strip() != 'YES':
                    print("Rebalancing cancelled by user.")
                    return
            
            execute_rebalance(tm, display, trades, dry_run)
        
        print("\n✓ Portfolio manager completed successfully")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Always disconnect
        conn.disconnect()


if __name__ == "__main__":
    # Check for custom config file argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    main(config_file)
