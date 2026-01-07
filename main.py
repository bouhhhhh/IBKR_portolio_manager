"""
Main entry point for IBKR Portfolio Manager.
Reads configuration from JSON file and executes portfolio rebalancing.
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Fix for Python 3.14+ event loop requirement
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from modules.connection import IBConnection
from modules.transactions import TransactionManager
from modules.portfolio_manager import PortfolioManager
from modules.display import PortfolioDisplay
from modules.charts import PortfolioCharts
from modules.historical_data import HistoricalDataManager
from modules.metrics import calculate_all_metrics
from modules.fees import display_fee_comparison, display_rebalance_fees


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


def display_balance(pm: PortfolioManager, display: PortfolioDisplay):
    """Display account balance and important financial information."""
    print("\n" + "=" * 80)
    print("ACCOUNT BALANCE & FINANCIAL SUMMARY")
    print("=" * 80)
    
    # Get account summary and key values
    summary = pm.get_account_summary()
    portfolio_value = pm.get_portfolio_value()
    cash_balance = pm.get_cash_balance()
    buying_power = pm.get_buying_power()
    
    # Extract important values
    equity = float(summary.get('EquityWithLoanValue', {}).get('value', 0)) if 'EquityWithLoanValue' in summary else portfolio_value
    gross_position_value = float(summary.get('GrossPositionValue', {}).get('value', 0)) if 'GrossPositionValue' in summary else 0
    
    # Calculate invested amount
    invested_amount = portfolio_value - cash_balance
    cash_percentage = (cash_balance / portfolio_value * 100) if portfolio_value > 0 else 0
    invested_percentage = (invested_amount / portfolio_value * 100) if portfolio_value > 0 else 0
    
    print("\nACCOUNT VALUE")
    print("-" * 80)
    print(f"Net Liquidation Value:    {display.format_currency(portfolio_value)}")
    print(f"Equity with Loan:         {display.format_currency(equity)}")
    print(f"Gross Position Value:     {display.format_currency(gross_position_value)}")
    
    print("\nCASH & INVESTMENTS")
    print("-" * 80)
    print(f"Total Cash:               {display.format_currency(cash_balance):<20} ({cash_percentage:>6.2f}%)")
    print(f"Invested Amount:          {display.format_currency(invested_amount):<20} ({invested_percentage:>6.2f}%)")
    
    print("\nBUYING POWER & MARGIN")
    print("-" * 80)
    print(f"Buying Power:             {display.format_currency(buying_power)}")
    
    # Additional margin info if available
    if 'InitMarginReq' in summary:
        init_margin = float(summary['InitMarginReq']['value'])
        print(f"Initial Margin Req:       {display.format_currency(init_margin)}")
    
    if 'MaintMarginReq' in summary:
        maint_margin = float(summary['MaintMarginReq']['value'])
        print(f"Maintenance Margin Req:   {display.format_currency(maint_margin)}")
    
    if 'AvailableFunds' in summary:
        avail_funds = float(summary['AvailableFunds']['value'])
        print(f"Available Funds:          {display.format_currency(avail_funds)}")
    
    if 'ExcessLiquidity' in summary:
        excess_liq = float(summary['ExcessLiquidity']['value'])
        print(f"Excess Liquidity:         {display.format_currency(excess_liq)}")
    
    # P&L Summary
    print("\nPROFIT & LOSS")
    print("-" * 80)
    
    if 'UnrealizedPnL' in summary:
        unrealized = float(summary['UnrealizedPnL']['value'])
        unrealized_str = display.format_currency(unrealized)
        if unrealized > 0:
            unrealized_str = f"\033[92m+{unrealized_str}\033[0m"  # Green
        elif unrealized < 0:
            unrealized_str = f"\033[91m{unrealized_str}\033[0m"  # Red
        print(f"Unrealized P&L:           {unrealized_str}")
    
    if 'RealizedPnL' in summary:
        realized = float(summary['RealizedPnL']['value'])
        realized_str = display.format_currency(realized)
        if realized > 0:
            realized_str = f"\033[92m+{realized_str}\033[0m"  # Green
        elif realized < 0:
            realized_str = f"\033[91m{realized_str}\033[0m"  # Red
        print(f"Realized P&L:             {realized_str}")
    
    if 'DailyPnL' in summary:
        daily = float(summary['DailyPnL']['value'])
        daily_str = display.format_currency(daily)
        if daily > 0:
            daily_str = f"\033[92m+{daily_str}\033[0m"  # Green
        elif daily < 0:
            daily_str = f"\033[91m{daily_str}\033[0m"  # Red
        print(f"Daily P&L:                {daily_str}")
    
    print("=" * 80)
    print()


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
        
        # Display fee analysis for these trades
        display_rebalance_fees(portfolio_value, filtered_trades)
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
    Execute rebalancing trades non-blocking.
    
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
    print(f"\nSubmitting {len(trades)} orders concurrently...")
    print("Orders will display status updates as they execute\n")
    
    submitted_trades = []
    
    # Submit all orders without waiting
    for i, trade_plan in enumerate(trades, 1):
        symbol = trade_plan['symbol']
        action = trade_plan['action']
        quantity = trade_plan['quantity']
        
        print(f"[{i}/{len(trades)}] Submitting {action} {quantity:.4f} shares of {symbol}...")
        
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
            submitted_trades.append((symbol, action, quantity, trade))
            
        except Exception as e:
            print(f"  ✗ Error submitting trade: {e}")
            continue
    
    print(f"\n✓ All {len(submitted_trades)} orders submitted")
    print("=" * 80)
    print("Monitoring order execution (press Enter to stop monitoring)...\n")
    
    # Wait for all trades to complete (non-blocking)
    pending = [t for _, _, _, t in submitted_trades if not t.isDone()]
    while pending:
        tm.ib.waitOnUpdate(timeout=0.5)
        pending = [t for _, _, _, t in submitted_trades if not t.isDone()]
    
    # Display final summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    
    for symbol, action, quantity, trade in submitted_trades:
        status = trade.orderStatus.status
        filled = trade.orderStatus.filled
        avg_price = trade.orderStatus.avgFillPrice or 0.0
        
        status_icon = "✓" if status in ["Filled", "Submitted", "PreSubmitted"] else "✗"
        print(f"{status_icon} {symbol:<6} {action:<4} {quantity:>10.4f} shares | "
              f"Status: {status:<12} | Filled: {filled:>10.4f} | Avg: ${avg_price:.2f}")
    
    print("=" * 80)
    if dry_run:
        print("DRY RUN COMPLETE - Orders processed in paper account")
    else:
        print("REBALANCING COMPLETE")
    print("=" * 80)


def display_returns(pm: PortfolioManager, display: PortfolioDisplay):
    """Display portfolio returns and yield."""
    print("\n" + "=" * 80)
    print("PORTFOLIO RETURNS & PERFORMANCE")
    print("=" * 80)
    
    # Get overall portfolio returns
    returns = pm.get_portfolio_returns()
    
    print("\nOVERALL PORTFOLIO")
    print("-" * 80)
    print(f"Cost Basis:        {display.format_currency(returns['cost_basis'])}")
    print(f"Current Value:     {display.format_currency(returns['current_value'])}")
    print(f"Unrealized P&L:    {display.format_currency(returns['unrealized_pnl'])}")
    print(f"Realized P&L:      {display.format_currency(returns['realized_pnl'])}")
    print(f"Total P&L:         {display.format_currency(returns['total_pnl'])}")
    
    return_str = f"{returns['return_percentage']:+.2f}%"
    if returns['return_percentage'] > 0:
        return_str = f"\033[92m{return_str}\033[0m"  # Green
    elif returns['return_percentage'] < 0:
        return_str = f"\033[91m{return_str}\033[0m"  # Red
    print(f"Total Return:      {return_str}")
    print("-" * 80)
    
    # Get position-level returns
    position_returns = pm.get_position_returns()
    
    if position_returns:
        print("\n" + "=" * 100)
        print("POSITION-LEVEL RETURNS")
        print("=" * 100)
        print(f"{'Symbol':<10} {'Quantity':<12} {'Cost Basis':<15} {'Market Value':<15} {'Unrealized P&L':<18} {'Return':<12}")
        print("-" * 100)
        
        for pos in position_returns:
            return_str = f"{pos['return_percentage']:+.2f}%"
            if pos['return_percentage'] > 0:
                pnl_prefix = "+"
            elif pos['return_percentage'] < 0:
                pnl_prefix = ""
            else:
                pnl_prefix = " "
            
            print(f"{pos['symbol']:<10} "
                  f"{pos['quantity']:<12.4f} "
                  f"{display.format_currency(pos['cost_basis']):<15} "
                  f"{display.format_currency(pos['market_value']):<15} "
                  f"{pnl_prefix}{display.format_currency(pos['unrealized_pnl']):<17} "
                  f"{return_str:<12}")
        
        print("=" * 100)
    
    print()


def display_advanced_metrics(
    hist: HistoricalDataManager,
    pm: PortfolioManager,
    display: PortfolioDisplay,
    benchmark_symbol: str = "SPY"
):
    """Display advanced portfolio metrics including VaR, Beta, Sortino, and Calmar ratios."""
    print("\n" + "=" * 80)
    print("ADVANCED PORTFOLIO METRICS")
    print("=" * 80)
    
    # Get portfolio positions to calculate returns
    positions = pm.get_portfolio_positions()
    
    if not positions:
        print("No positions found. Cannot calculate metrics.")
        return
    
    print(f"\nFetching historical data for portfolio analysis...")
    
    # Collect historical data for all positions
    portfolio_data = []
    weights = []
    total_value = sum(pos['marketValue'] for pos in positions)
    
    for pos in positions:
        symbol = pos['contract'].symbol
        weight = pos['marketValue'] / total_value if total_value > 0 else 0
        
        print(f"  Fetching {symbol} (weight: {weight:.1%})...", end=" ")
        try:
            hist_data = hist.get_position_history(symbol, pos['avgCost'], duration="1 Y")
            if 'error' not in hist_data and 'data' in hist_data:
                portfolio_data.append(hist_data['data'])
                weights.append(weight)
                print("✓")
            else:
                error_msg = hist_data.get('error', 'Unknown error')
                print(f"✗ {error_msg}")
        except Exception as e:
            print(f"✗ {e}")
            continue
    
    if not portfolio_data:
        print("\nError: Could not fetch historical data for any positions.")
        print("Make sure you are connected to IBKR and have market data subscriptions.")
        return
    
    print(f"\n✓ Successfully fetched data for {len(portfolio_data)} position(s)")
    
    # Calculate weighted portfolio returns
    # Align all dataframes by date
    import pandas as pd
    
    all_returns = []
    for i, data in enumerate(portfolio_data):
        # Calculate daily returns from close prices
        if 'close' in data.columns:
            daily_returns = data['close'].pct_change().dropna()
            weighted_returns = daily_returns * weights[i]
            all_returns.append(weighted_returns)
        else:
            print(f"Warning: No 'close' column in data at index {i}")
    
    if not all_returns:
        print("Error: Could not calculate portfolio returns.")
        return
    
    # Combine returns using pandas
    portfolio_returns = pd.concat(all_returns, axis=1).sum(axis=1)
    
    # Fetch benchmark data (SPY)
    print(f"Fetching benchmark data ({benchmark_symbol})...")
    try:
        benchmark_data = hist.get_position_history(benchmark_symbol, 0, duration="1 Y")
        if 'error' in benchmark_data or 'data' not in benchmark_data:
            print(f"Warning: Could not fetch {benchmark_symbol} data. Beta/Alpha/IR will not be available.")
            benchmark_returns = None
        else:
            # Calculate daily returns from close prices
            benchmark_df = benchmark_data['data']
            benchmark_returns = benchmark_df['close'].pct_change().dropna().values
            # Align lengths
            min_len = min(len(portfolio_returns), len(benchmark_returns))
            portfolio_returns_array = portfolio_returns.values[-min_len:]
            benchmark_returns = benchmark_returns[-min_len:]
    except Exception as e:
        print(f"Warning: Could not fetch benchmark data: {e}")
        benchmark_returns = None
        portfolio_returns_array = portfolio_returns.values
    
    # Get max drawdown from portfolio manager
    returns_data = pm.get_portfolio_returns()
    cost_basis = returns_data['cost_basis']
    current_value = returns_data['current_value']
    
    # Calculate max drawdown from cumulative returns
    cumulative_returns = (1 + portfolio_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdowns = (cumulative_returns - running_max) / running_max
    max_drawdown_pct = abs(drawdowns.min()) * 100
    
    # Calculate all metrics
    if benchmark_returns is not None:
        metrics = calculate_all_metrics(
            portfolio_returns=portfolio_returns_array,
            benchmark_returns=benchmark_returns,
            max_drawdown=max_drawdown_pct,
            risk_free_rate=0.04  # 4% risk-free rate
        )
    else:
        metrics = calculate_all_metrics(
            portfolio_returns=portfolio_returns_array,
            benchmark_returns=None,
            max_drawdown=max_drawdown_pct,
            risk_free_rate=0.04
        )
    
    # Display metrics
    print("\n" + "=" * 80)
    print("RISK METRICS")
    print("=" * 80)
    print(f"Value at Risk (95%):            {metrics['var_95']:.2f}%")
    print(f"Value at Risk (99%):            {metrics['var_99']:.2f}%")
    print(f"Conditional VaR (95%):          {metrics['cvar_95']:.2f}%")
    print(f"Max Drawdown:                   {max_drawdown_pct:.2f}%")
    
    print("\n" + "=" * 80)
    print("RISK-ADJUSTED RETURN METRICS")
    print("=" * 80)
    print(f"Sortino Ratio:                  {metrics['sortino_ratio']:.3f}")
    print(f"Calmar Ratio:                   {metrics['calmar_ratio']:.3f}")
    
    if 'beta' in metrics:
        print("\n" + "=" * 80)
        print(f"MARKET COMPARISON (vs {benchmark_symbol})")
        print("=" * 80)
        print(f"Beta:                           {metrics['beta']:.3f}")
        
        beta_interp = "Market-like"
        if metrics['beta'] > 1.2:
            beta_interp = "Higher volatility than market"
        elif metrics['beta'] < 0.8:
            beta_interp = "Lower volatility than market"
        print(f"  → {beta_interp}")
        
        print(f"Alpha (annualized):             {metrics['alpha']:.2f}%")
        alpha_interp = "Outperforming" if metrics['alpha'] > 0 else "Underperforming"
        print(f"  → {alpha_interp} risk-adjusted expectations")
        
        print(f"Information Ratio:              {metrics['information_ratio']:.3f}")
        ir_interp = "Excellent" if metrics['information_ratio'] > 1.0 else ("Good" if metrics['information_ratio'] > 0.5 else "Modest")
        print(f"  → {ir_interp} active management")
    
    # Add interpretations
    print("\n" + "=" * 80)
    print("INTERPRETATIONS")
    print("=" * 80)
    print(f"VaR(95%): 95% confidence that daily loss won't exceed {metrics['var_95']:.2f}%")
    print(f"CVaR(95%): Average loss in the worst 5% of cases is {metrics['cvar_95']:.2f}%")
    
    sortino_quality = "Excellent" if metrics['sortino_ratio'] > 2.0 else ("Good" if metrics['sortino_ratio'] > 1.0 else "Modest")
    print(f"Sortino: {sortino_quality} downside risk-adjusted returns")
    
    calmar_quality = "Strong" if metrics['calmar_ratio'] > 0.5 else ("Moderate" if metrics['calmar_ratio'] > 0.3 else "Weak")
    print(f"Calmar: {calmar_quality} return relative to max drawdown")
    
    print("=" * 80)
    print()


def show_help():
    """Display available commands."""
    print("\n" + "=" * 80)
    print("AVAILABLE COMMANDS")
    print("=" * 80)
    print("  portfolio / p     - Show current portfolio status")
    print("  balance / b       - Show account balance and financial summary")
    print("  returns / yield   - Show portfolio returns and performance")
    print("  metrics / m       - Show advanced metrics (VaR, Beta, Sortino, Calmar)")
    print("  fees              - Compare IBKR vs Wealthsimple fees")
    print("  history <SYMBOL>  - Show price history for a stock (e.g., 'history SPY')")
    print("  <SYMBOL>          - Quick access to stock history (e.g., 'SPY')")
    print("  chart allocation  - Display portfolio allocation pie chart")
    print("  chart returns     - Display position returns bar chart")
    print("  chart pnl         - Display P&L breakdown chart")
    print("  chart target      - Display current vs target allocation chart")
    print("  rebalance / r     - Calculate and execute rebalancing trades")
    print("  plan              - Show rebalancing plan without executing")
    print("  config            - Reload configuration file")
    print("  help / h          - Show this help message")
    print("  quit / q / exit   - Disconnect and exit")
    print("=" * 80)


def main(config_path: str = "config.json"):
    """
    Main execution function - runs as persistent server.
    
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
        hist = HistoricalDataManager(ib)
        
        print("\n" + "=" * 80)
        print("PORTFOLIO MANAGER SERVER - READY")
        print("=" * 80)
        print("Type 'help' for available commands or 'quit' to exit")
        
        # Command loop
        while True:
            try:
                command_raw = input("\n> ").strip()
                command = command_raw.lower()
                
                if not command:
                    continue
                
                # Handle quit commands
                if command in ['quit', 'q', 'exit']:
                    print("\nShutting down...")
                    break
                
                # Handle help command
                elif command in ['help', 'h']:
                    show_help()
                
                # Handle portfolio display
                elif command in ['portfolio', 'p']:
                    display_current_portfolio(pm, display)
                
                # Handle balance display
                elif command in ['balance', 'b']:
                    display_balance(pm, display)
                
                # Handle returns/yield display
                elif command in ['returns', 'yield', 'performance']:
                    display_returns(pm, display)
                
                # Handle advanced metrics display
                elif command in ['metrics', 'm', 'metric']:
                    display_advanced_metrics(hist, pm, display)
                
                # Handle fee comparison
                elif command == 'fees':
                    portfolio_value = pm.get_portfolio_value()
                    positions = pm.get_portfolio_positions()
                    display_fee_comparison(portfolio_value, positions)
                
                # Handle history commands
                elif command.startswith('history '):
                    symbol = command.split(' ', 1)[1].upper() if ' ' in command else ''
                    if symbol:
                        # Find position data if available
                        positions = pm.get_portfolio_positions()
                        avg_cost = None
                        for pos in positions:
                            if pos['contract'].symbol == symbol:
                                avg_cost = pos['avgCost']
                                break
                        
                        print(f"\nFetching historical data for {symbol}...")
                        history_data = hist.get_position_history(symbol, avg_cost or 0, duration="1 Y")
                        
                        if 'error' in history_data:
                            print(f"Error: {history_data['error']}")
                        else:
                            # Display metrics
                            print("\n" + "=" * 80)
                            print(f"{symbol} - HISTORICAL ANALYSIS (1 Year)")
                            print("=" * 80)
                            metrics = history_data['metrics']
                            print(f"Start Price:      ${metrics['start_price']:.2f}")
                            print(f"Current Price:    ${metrics['end_price']:.2f}")
                            print(f"Total Return:     {metrics['total_return']:+.2f}%")
                            if avg_cost:
                                print(f"Avg Cost:         ${avg_cost:.2f}")
                                print(f"Your Return:      {history_data['purchase_return']:+.2f}%")
                            print(f"Volatility:       {metrics['volatility']:.2f}%")
                            print(f"Max Drawdown:     {metrics['max_drawdown']:.2f}%")
                            print(f"Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
                            print("=" * 80)
                            
                            # Show charts
                            PortfolioCharts.plot_price_history(
                                history_data['data'], symbol, avg_cost
                            )
                            PortfolioCharts.plot_performance_metrics(
                                metrics, symbol
                            )
                    else:
                        print("Usage: history <SYMBOL>")
                
                # Handle chart commands
                elif command.startswith('chart '):
                    chart_type = command.split(' ', 1)[1] if ' ' in command else ''
                    
                    if chart_type == 'allocation':
                        positions = pm.get_portfolio_positions()
                        cash_balance = pm.get_cash_balance()
                        PortfolioCharts.plot_allocation_pie(positions, cash_balance)
                    
                    elif chart_type == 'returns':
                        position_returns = pm.get_position_returns()
                        PortfolioCharts.plot_returns_bar(position_returns)
                    
                    elif chart_type == 'pnl':
                        position_returns = pm.get_position_returns()
                        PortfolioCharts.plot_pnl_breakdown(position_returns)
                    
                    elif chart_type == 'target':
                        # Get current allocation percentages
                        positions = pm.get_portfolio_positions()
                        total_value = pm.get_portfolio_value()
                        cash = pm.get_cash_balance()
                        invested = total_value - cash
                        
                        current_alloc = {}
                        for pos in positions:
                            symbol = pos['contract'].symbol
                            current_alloc[symbol] = (pos['marketValue'] / invested * 100) if invested > 0 else 0
                        
                        PortfolioCharts.plot_allocation_vs_target(current_alloc, allocations)
                    
                    else:
                        print(f"Unknown chart type: '{chart_type}'")
                        print("Available: allocation, returns, pnl, target")
                
                # Handle rebalance plan (no execution)
                elif command == 'plan':
                    trades = calculate_and_display_rebalance_plan(
                        pm, display, allocations, min_trade_value
                    )
                    if trades:
                        print(f"\n{len(trades)} trades planned. Use 'rebalance' to execute.")
                
                # Handle rebalance with execution
                elif command in ['rebalance', 'r']:
                    # Calculate trades
                    trades = calculate_and_display_rebalance_plan(
                        pm, display, allocations, min_trade_value
                    )
                    
                    if trades:
                        # Confirm if not dry run
                        if not dry_run:
                            print("\n" + "!" * 80)
                            print("WARNING: You are about to execute REAL trades!")
                            print("!" * 80)
                            response = input("\nDo you want to proceed? (type 'YES' to confirm): ")
                            if response.strip() != 'YES':
                                print("Rebalancing cancelled.")
                                continue
                        
                        # Execute trades
                        execute_rebalance(tm, display, trades, dry_run)
                        print("\n✓ Rebalancing complete")
                    else:
                        print("\n✓ No trades needed - portfolio is balanced")
                
                # Handle config reload
                elif command == 'config':
                    print("Reloading configuration...")
                    config = load_config(config_path)
                    allocations = config['allocations']
                    settings = config.get('settings', {})
                    dry_run = settings.get('dry_run', True)
                    min_trade_value = settings.get('min_trade_value', 10.0)
                    print("✓ Configuration reloaded")
                
                # Handle stock symbol as shortcut for history
                elif command_raw.isupper() and len(command_raw) <= 5 and command_raw.isalpha():
                    # Treat as stock symbol shortcut
                    symbol = command_raw
                    positions = pm.get_portfolio_positions()
                    avg_cost = None
                    for pos in positions:
                        if pos['contract'].symbol == symbol:
                            avg_cost = pos['avgCost']
                            break
                    
                    print(f"\nFetching historical data for {symbol}...")
                    history_data = hist.get_position_history(symbol, avg_cost or 0, duration="1 Y")
                    
                    if 'error' in history_data:
                        print(f"Error: {history_data['error']}")
                    else:
                        # Display metrics
                        print("\n" + "=" * 80)
                        print(f"{symbol} - HISTORICAL ANALYSIS (1 Year)")
                        print("=" * 80)
                        metrics = history_data['metrics']
                        print(f"Start Price:      ${metrics['start_price']:.2f}")
                        print(f"Current Price:    ${metrics['end_price']:.2f}")
                        print(f"Total Return:     {metrics['total_return']:+.2f}%")
                        if avg_cost:
                            print(f"Avg Cost:         ${avg_cost:.2f}")
                            print(f"Your Return:      {history_data['purchase_return']:+.2f}%")
                        print(f"Volatility:       {metrics['volatility']:.2f}%")
                        print(f"Max Drawdown:     {metrics['max_drawdown']:.2f}%")
                        print(f"Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
                        print("=" * 80)
                        
                        # Show charts
                        PortfolioCharts.plot_price_history(
                            history_data['data'], symbol, avg_cost
                        )
                        PortfolioCharts.plot_performance_metrics(
                            metrics, symbol
                        )
                
                # Handle unknown command
                else:
                    print(f"Unknown command: '{command}'. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'quit' to exit.")
                continue
            except Exception as e:
                print(f"\n✗ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print("✓ Portfolio manager stopped")
        
    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
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
