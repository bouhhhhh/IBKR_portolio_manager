"""
Module for displaying portfolio data and generating reports.
"""
from typing import List, Dict
from datetime import datetime


class PortfolioDisplay:
    """Handles display and formatting of portfolio data."""
    
    @staticmethod
    def format_currency(value: float, currency: str = "USD") -> str:
        """
        Format a value as currency.
        
        Args:
            value: Numeric value to format
            currency: Currency symbol
        
        Returns:
            Formatted currency string
        """
        symbol = "$" if currency == "USD" else currency
        return f"{symbol}{value:,.2f}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """
        Format a value as percentage.
        
        Args:
            value: Numeric value to format (0-100)
        
        Returns:
            Formatted percentage string
        """
        return f"{value:.2f}%"
    
    @staticmethod
    def print_positions(positions: List[Dict]) -> None:
        """
        Print current portfolio positions in a formatted table.
        
        Args:
            positions: List of position dictionaries
        """
        if not positions:
            print("No positions found.")
            return
        
        print("\n" + "="*100)
        print("CURRENT PORTFOLIO POSITIONS")
        print("="*100)
        print(f"{'Symbol':<10} {'Quantity':<12} {'Avg Cost':<12} {'Market Price':<12} {'Market Value':<15} {'Unrealized P/L':<15}")
        print("-"*100)
        
        total_value = 0.0
        total_pnl = 0.0
        
        for pos in positions:
            symbol = pos['contract'].symbol
            quantity = pos['position']
            avg_cost = pos['avgCost']
            market_price = pos['marketPrice']
            market_value = pos['marketValue']
            unrealized_pnl = pos['unrealizedPNL']
            
            total_value += market_value
            total_pnl += unrealized_pnl
            
            pnl_str = PortfolioDisplay.format_currency(unrealized_pnl)
            if unrealized_pnl > 0:
                pnl_str = f"+{pnl_str}"
            
            print(f"{symbol:<10} {quantity:<12.4f} {PortfolioDisplay.format_currency(avg_cost):<12} "
                  f"{PortfolioDisplay.format_currency(market_price):<12} "
                  f"{PortfolioDisplay.format_currency(market_value):<15} {pnl_str:<15}")
        
        print("-"*100)
        print(f"{'TOTAL':<10} {'':<12} {'':<12} {'':<12} "
              f"{PortfolioDisplay.format_currency(total_value):<15} "
              f"{PortfolioDisplay.format_currency(total_pnl):<15}")
        print("="*100 + "\n")
    
    @staticmethod
    def print_account_summary(summary: Dict) -> None:
        """
        Print account summary information.
        
        Args:
            summary: Account summary dictionary
        """
        print("\n" + "="*60)
        print("ACCOUNT SUMMARY")
        print("="*60)
        
        important_keys = [
            'NetLiquidation',
            'TotalCashValue',
            'BuyingPower',
            'GrossPositionValue',
            'UnrealizedPnL',
            'RealizedPnL'
        ]
        
        for key in important_keys:
            if key in summary:
                item = summary[key]
                print(f"{key:<30} {PortfolioDisplay.format_currency(float(item['value']), item['currency'])}")
        
        print("="*60 + "\n")
    
    @staticmethod
    def print_rebalance_plan(trades: List[Dict]) -> None:
        """
        Print rebalancing trade plan.
        
        Args:
            trades: List of trade dictionaries
        """
        if not trades:
            print("No rebalancing trades needed.")
            return
        
        print("\n" + "="*130)
        print("REBALANCING PLAN")
        print("="*130)
        print(f"{'Symbol':<10} {'Action':<8} {'Quantity':<12} {'Price':<12} {'Current Value':<15} {'Target Value':<15} {'Difference':<15}")
        print("-"*130)
        
        for trade in trades:
            symbol = trade['symbol']
            action = trade['action']
            quantity = trade['quantity']
            price = trade.get('price', 0.0)
            current_value = trade['current_value']
            target_value = trade['target_value']
            difference = trade['difference']
            
            diff_str = PortfolioDisplay.format_currency(abs(difference))
            if difference > 0:
                diff_str = f"+{diff_str}"
            else:
                diff_str = f"-{diff_str}"
            
            print(f"{symbol:<10} {action:<8} {quantity:<12.0f} "
                  f"{PortfolioDisplay.format_currency(price):<12} "
                  f"{PortfolioDisplay.format_currency(current_value):<15} "
                  f"{PortfolioDisplay.format_currency(target_value):<15} "
                  f"{diff_str:<15}")
        
        print("="*130 + "\n")
    
    @staticmethod
    def print_trade_status(trade_info: Dict) -> None:
        """
        Print status of a trade.
        
        Args:
            trade_info: Trade information dictionary
        """
        print(f"\nTrade Status for {trade_info.get('symbol', 'Unknown')}:")
        print(f"  Action: {trade_info.get('action', 'N/A')}")
        print(f"  Quantity: {trade_info.get('quantity', 0):.4f}")
        print(f"  Status: {trade_info.get('status', 'Unknown')}")
        if 'filled' in trade_info:
            print(f"  Filled: {trade_info['filled']:.4f}")
        if 'avgFillPrice' in trade_info:
            print(f"  Avg Fill Price: {PortfolioDisplay.format_currency(trade_info['avgFillPrice'])}")
        print()
    
    @staticmethod
    def generate_report_header() -> str:
        """
        Generate a report header with timestamp.
        
        Returns:
            Formatted header string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""
{'='*80}
PORTFOLIO REPORT
Generated: {timestamp}
{'='*80}
"""
        return header
