"""
Example usage of the refactored IBKR portfolio manager modules.
This file demonstrates how to use the connection, transactions, 
portfolio_manager, and display modules together.
"""
from connection import IBConnection
from transactions import TransactionManager
from portfolio_manager import PortfolioManager
from display import PortfolioDisplay


def example_simple_buy():
    """Example: Connect and place a simple buy order."""
    # 1. Establish connection
    conn = IBConnection(host='127.0.0.1', port=4002, client_id=1)
    ib = conn.connect()
    
    try:
        # 2. Create transaction manager
        tm = TransactionManager(ib)
        
        # 3. Place a buy order
        trade = tm.place_buy_async(symbol="QQQ", qty=10, dry_run=False)
        
        # 4. Wait for completion
        tm.wait_for_trade_completion(trade)
        
        print("Trade completed successfully!")
        
    finally:
        # Always disconnect when done
        conn.disconnect()


def example_view_portfolio():
    """Example: Connect and view current portfolio."""
    # 1. Establish connection
    conn = IBConnection(host='127.0.0.1', port=4002, client_id=1)
    ib = conn.connect()
    
    try:
        # 2. Create portfolio manager and display
        pm = PortfolioManager(ib)
        display = PortfolioDisplay()
        
        # 3. Get and display positions
        print(display.generate_report_header())
        
        positions = pm.get_portfolio_positions()
        display.print_positions(positions)
        
        # 4. Get and display account summary
        summary = pm.get_account_summary()
        display.print_account_summary(summary)
        
        # 5. Show additional info
        print(f"Total Portfolio Value: {display.format_currency(pm.get_portfolio_value())}")
        print(f"Cash Balance: {display.format_currency(pm.get_cash_balance())}")
        print(f"Buying Power: {display.format_currency(pm.get_buying_power())}")
        
    finally:
        conn.disconnect()


def example_rebalance_portfolio():
    """Example: Calculate and display rebalancing plan."""
    # 1. Establish connection
    conn = IBConnection(host='127.0.0.1', port=4002, client_id=1)
    ib = conn.connect()
    
    try:
        # 2. Create managers
        pm = PortfolioManager(ib)
        tm = TransactionManager(ib)
        display = PortfolioDisplay()
        
        # 3. Define target allocations (must sum to 100%)
        target_allocations = {
            'SPY': 40.0,   # 40% in SPY
            'QQQ': 30.0,   # 30% in QQQ
            'IWM': 20.0,   # 20% in IWM
            'TLT': 10.0    # 10% in TLT
        }
        
        # 4. Calculate target dollar amounts
        portfolio_value = pm.get_portfolio_value()
        target_amounts = pm.calculate_target_allocations(target_allocations, portfolio_value)
        
        # 5. Calculate rebalancing trades
        trades = pm.calculate_rebalance_trades(target_amounts)
        
        # 6. Display the plan
        print(display.generate_report_header())
        print(f"Portfolio Value: {display.format_currency(portfolio_value)}\n")
        display.print_rebalance_plan(trades)
        
        # 7. Execute trades (optional - uncomment to actually trade)
        # execute_rebalance = input("Execute these trades? (yes/no): ")
        # if execute_rebalance.lower() == 'yes':
        #     for trade_plan in trades:
        #         if trade_plan['action'] == 'BUY':
        #             trade = tm.place_buy_async(
        #                 symbol=trade_plan['symbol'],
        #                 qty=trade_plan['quantity']
        #             )
        #         else:
        #             trade = tm.place_sell_async(
        #                 symbol=trade_plan['symbol'],
        #                 qty=trade_plan['quantity']
        #             )
        #         tm.wait_for_trade_completion(trade)
        #     print("\nRebalancing complete!")
        
    finally:
        conn.disconnect()


def example_multiple_trades():
    """Example: Place multiple trades in sequence."""
    conn = IBConnection(host='127.0.0.1', port=4002, client_id=1)
    ib = conn.connect()
    
    try:
        tm = TransactionManager(ib)
        
        # Define trades to execute
        trades_to_place = [
            {'symbol': 'SPY', 'qty': 5, 'action': 'BUY'},
            {'symbol': 'QQQ', 'qty': 3, 'action': 'BUY'},
            {'symbol': 'IWM', 'qty': 2, 'action': 'BUY'},
        ]
        
        # Execute each trade
        for trade_info in trades_to_place:
            print(f"\nExecuting: {trade_info['action']} {trade_info['qty']} of {trade_info['symbol']}")
            
            if trade_info['action'] == 'BUY':
                trade = tm.place_buy_async(
                    symbol=trade_info['symbol'],
                    qty=trade_info['qty']
                )
            else:
                trade = tm.place_sell_async(
                    symbol=trade_info['symbol'],
                    qty=trade_info['qty']
                )
            
            # Wait for this trade to complete before moving to next
            tm.wait_for_trade_completion(trade)
        
        print("\nAll trades completed!")
        
    finally:
        conn.disconnect()


if __name__ == "__main__":
    # Uncomment the example you want to run:
    
    # Example 1: Simple buy order (original test2.py functionality)
    example_simple_buy()
    
    # Example 2: View portfolio
    # example_view_portfolio()
    
    # Example 3: Calculate rebalancing plan
    # example_rebalance_portfolio()
    
    # Example 4: Multiple sequential trades
    # example_multiple_trades()
