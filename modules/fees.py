"""
Module for comparing IBKR vs Wealthsimple fee structures.
"""
from typing import Dict, Tuple


class FeeComparator:
    """Compare IBKR trading fees with Wealthsimple management fees."""
    
    # IBKR Tiered fee structure (CAD per share)
    IBKR_TIERS = [
        (300_000, 0.008),           # ≤ 300,000 shares
        (3_000_000, 0.005),         # 300,001 - 3,000,000
        (20_000_000, 0.004),        # 3,000,001 - 20,000,000
        (float('inf'), 0.003)       # > 20,000,000
    ]
    
    IBKR_MIN_PER_ORDER = 1.00      # CAD
    IBKR_MAX_PER_ORDER_PCT = 0.005  # 0.5% of trade value
    
    WEALTHSIMPLE_ANNUAL_FEE = 0.005  # 0.5% annual management fee
    
    def __init__(self, portfolio_value: float):
        """
        Initialize fee comparator.
        
        Args:
            portfolio_value: Current portfolio value in CAD
        """
        self.portfolio_value = portfolio_value
    
    def calculate_wealthsimple_annual_fee(self) -> float:
        """
        Calculate Wealthsimple's annual management fee.
        
        Returns:
            Annual fee in CAD
        """
        return self.portfolio_value * self.WEALTHSIMPLE_ANNUAL_FEE
    
    def calculate_ibkr_trade_fee(
        self, 
        shares: int, 
        share_price: float
    ) -> float:
        """
        Calculate IBKR fee for a single trade.
        
        Args:
            shares: Number of shares traded
            share_price: Price per share in CAD
        
        Returns:
            Fee in CAD
        """
        trade_value = shares * share_price
        
        # Calculate base fee using tiered structure
        remaining_shares = shares
        total_fee = 0.0
        cumulative_shares = 0
        
        for tier_limit, rate in self.IBKR_TIERS:
            if remaining_shares <= 0:
                break
            
            # How many shares fall into this tier?
            tier_shares = min(
                remaining_shares, 
                tier_limit - cumulative_shares
            )
            
            total_fee += tier_shares * rate
            remaining_shares -= tier_shares
            cumulative_shares += tier_shares
        
        # Apply minimum and maximum per order
        fee = max(total_fee, self.IBKR_MIN_PER_ORDER)
        fee = min(fee, trade_value * self.IBKR_MAX_PER_ORDER_PCT)
        
        return fee
    
    def estimate_average_trade_fee(
        self,
        avg_shares_per_trade: int = 100,
        avg_share_price: float = 100.0
    ) -> float:
        """
        Estimate average fee per trade.
        
        Args:
            avg_shares_per_trade: Average number of shares per trade
            avg_share_price: Average price per share in CAD
        
        Returns:
            Average fee per trade in CAD
        """
        return self.calculate_ibkr_trade_fee(avg_shares_per_trade, avg_share_price)
    
    def calculate_breakeven_trades(
        self,
        avg_shares_per_trade: int = 100,
        avg_share_price: float = 100.0
    ) -> Dict[str, float]:
        """
        Calculate how many trades can be done to break even with Wealthsimple.
        
        Args:
            avg_shares_per_trade: Average number of shares per trade
            avg_share_price: Average price per share in CAD
        
        Returns:
            Dictionary with breakeven analysis
        """
        ws_annual_fee = self.calculate_wealthsimple_annual_fee()
        avg_trade_fee = self.estimate_average_trade_fee(
            avg_shares_per_trade, 
            avg_share_price
        )
        
        # Calculate maximum trades per year to break even
        max_annual_trades = ws_annual_fee / avg_trade_fee if avg_trade_fee > 0 else float('inf')
        
        # Monthly and weekly breakdowns
        max_monthly_trades = max_annual_trades / 12
        max_weekly_trades = max_annual_trades / 52
        
        return {
            'portfolio_value': self.portfolio_value,
            'wealthsimple_annual_fee': ws_annual_fee,
            'ibkr_avg_trade_fee': avg_trade_fee,
            'max_annual_trades': max_annual_trades,
            'max_monthly_trades': max_monthly_trades,
            'max_weekly_trades': max_weekly_trades,
            'avg_shares_per_trade': avg_shares_per_trade,
            'avg_share_price': avg_share_price,
            'trade_value': avg_shares_per_trade * avg_share_price
        }
    
    def compare_scenarios(self, positions: list) -> Dict:
        """
        Compare fees across different trading scenarios based on actual positions.
        
        Args:
            positions: List of position dictionaries with marketPrice
        
        Returns:
            Dictionary with multiple scenario analyses
        """
        ws_annual_fee = self.calculate_wealthsimple_annual_fee()
        
        # Calculate average share price from positions
        if positions:
            avg_price = sum(pos['marketPrice'] for pos in positions) / len(positions)
        else:
            avg_price = 100.0
        
        scenarios = {}
        
        # Scenario 1: Small trades (fractional position rebalancing)
        small_shares = 10
        scenarios['small_trades'] = {
            'description': f'Small trades ({small_shares} shares @ ${avg_price:.2f})',
            **self.calculate_breakeven_trades(small_shares, avg_price)
        }
        
        # Scenario 2: Medium trades (typical rebalancing)
        medium_shares = 50
        scenarios['medium_trades'] = {
            'description': f'Medium trades ({medium_shares} shares @ ${avg_price:.2f})',
            **self.calculate_breakeven_trades(medium_shares, avg_price)
        }
        
        # Scenario 3: Large trades (full position adjustments)
        large_shares = 100
        scenarios['large_trades'] = {
            'description': f'Large trades ({large_shares} shares @ ${avg_price:.2f})',
            **self.calculate_breakeven_trades(large_shares, avg_price)
        }
        
        # Scenario 4: Minimum fee trades (hit the $1 minimum)
        min_fee_shares = 5
        scenarios['minimum_fee'] = {
            'description': f'Minimum fee trades ({min_fee_shares} shares @ ${avg_price:.2f})',
            **self.calculate_breakeven_trades(min_fee_shares, avg_price)
        }
        
        return {
            'portfolio_value': self.portfolio_value,
            'wealthsimple_annual_fee': ws_annual_fee,
            'scenarios': scenarios
        }
    
    def calculate_rebalance_fees(self, trades: list) -> Dict:
        """
        Calculate total IBKR fees for a specific rebalancing plan.
        
        Args:
            trades: List of trade dictionaries with 'symbol', 'quantity', 'price', 'action'
        
        Returns:
            Dictionary with fee breakdown and comparison
        """
        total_ibkr_fees = 0.0
        trade_details = []
        
        for trade in trades:
            shares = abs(int(trade['quantity']))  # Use absolute value, cast to int
            price = trade.get('price', 0.0)  # Changed from 'current_price' to 'price'
            
            if shares > 0 and price > 0:
                fee = self.calculate_ibkr_trade_fee(shares, price)
                total_ibkr_fees += fee
                
                trade_details.append({
                    'symbol': trade['symbol'],
                    'action': trade['action'],
                    'shares': shares,
                    'price': price,
                    'trade_value': shares * price,
                    'fee': fee
                })
        
        # Calculate what Wealthsimple would charge (proportional to rebalancing frequency)
        # Assume quarterly rebalancing = 4 times per year
        ws_quarterly_cost = self.calculate_wealthsimple_annual_fee() / 4
        
        return {
            'trade_details': trade_details,
            'total_ibkr_fees': total_ibkr_fees,
            'num_trades': len(trade_details),
            'wealthsimple_quarterly_fee': ws_quarterly_cost,
            'wealthsimple_annual_fee': self.calculate_wealthsimple_annual_fee(),
            'savings_this_rebalance': ws_quarterly_cost - total_ibkr_fees,
            'portfolio_value': self.portfolio_value
        }


def display_fee_comparison(portfolio_value: float, positions: list = None):
    """
    Display comprehensive fee comparison.
    
    Args:
        portfolio_value: Current portfolio value in CAD
        positions: List of current positions
    """
    comparator = FeeComparator(portfolio_value)
    
    print("\n" + "=" * 80)
    print("IBKR vs WEALTHSIMPLE FEE COMPARISON")
    print("=" * 80)
    
    print(f"\nPortfolio Value: ${portfolio_value:,.2f} CAD")
    
    ws_fee = comparator.calculate_wealthsimple_annual_fee()
    print(f"Wealthsimple Annual Fee (0.5%): ${ws_fee:,.2f} CAD")
    
    if positions:
        print("\n" + "=" * 80)
        print("BREAKEVEN ANALYSIS BY TRADE SIZE")
        print("=" * 80)
        
        comparison = comparator.compare_scenarios(positions)
        
        for scenario_name, scenario_data in comparison['scenarios'].items():
            print(f"\n{scenario_data['description']}")
            print("-" * 80)
            print(f"  Trade Value:              ${scenario_data['trade_value']:,.2f}")
            print(f"  IBKR Fee per Trade:       ${scenario_data['ibkr_avg_trade_fee']:.2f}")
            print(f"  Max Annual Trades:        {scenario_data['max_annual_trades']:.0f}")
            print(f"  Max Monthly Trades:       {scenario_data['max_monthly_trades']:.1f}")
            print(f"  Max Weekly Trades:        {scenario_data['max_weekly_trades']:.1f}")
    
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print("You can execute the number of trades shown above per year and still")
    print("pay LESS in fees than Wealthsimple's 0.5% annual management fee.")
    print("\nIBKR is advantageous if you:")
    print("  • Rebalance quarterly or less frequently")
    print("  • Make larger trades (reducing impact of $1 minimum)")
    print("  • Hold positions long-term with minimal trading")
    print("=" * 80)
    print()


def display_rebalance_fees(portfolio_value: float, trades: list):
    """
    Display IBKR fees for specific rebalancing trades with comparison to Wealthsimple.
    
    Args:
        portfolio_value: Current portfolio value in CAD
        trades: List of trade dictionaries from rebalancing plan
    """
    if not trades:
        return
    
    comparator = FeeComparator(portfolio_value)
    fee_analysis = comparator.calculate_rebalance_fees(trades)
    
    print("\n" + "=" * 80)
    print("REBALANCING FEE ANALYSIS")
    print("=" * 80)
    
    print(f"\nPortfolio Value: ${portfolio_value:,.2f} CAD")
    print(f"Number of Trades: {fee_analysis['num_trades']}")
    
    print("\n" + "-" * 80)
    print("TRADE-BY-TRADE FEE BREAKDOWN")
    print("-" * 80)
    print(f"{'Symbol':<10} {'Action':<6} {'Shares':<10} {'Price':<12} {'Trade Value':<15} {'IBKR Fee':<12}")
    print("-" * 80)
    
    for detail in fee_analysis['trade_details']:
        print(f"{detail['symbol']:<10} "
              f"{detail['action']:<6} "
              f"{detail['shares']:<10} "
              f"${detail['price']:<11.2f} "
              f"${detail['trade_value']:<14,.2f} "
              f"${detail['fee']:<11.2f}")
    
    print("-" * 80)
    print(f"{'TOTAL IBKR FEES:':<54} ${fee_analysis['total_ibkr_fees']:.2f}")
    
    print("\n" + "=" * 80)
    print("COMPARISON TO WEALTHSIMPLE")
    print("=" * 80)
    
    ws_annual = fee_analysis['wealthsimple_annual_fee']
    ws_quarterly = fee_analysis['wealthsimple_quarterly_fee']
    
    print(f"Wealthsimple Annual Fee (0.5%):        ${ws_annual:,.2f}")
    print(f"Wealthsimple Quarterly Equivalent:     ${ws_quarterly:,.2f}")
    print(f"IBKR Fees for This Rebalance:          ${fee_analysis['total_ibkr_fees']:.2f}")
    
    savings = fee_analysis['savings_this_rebalance']
    print()
    if savings > 0:
        print(f"✓ SAVINGS with IBKR (vs quarterly):    ${savings:.2f}")
        annual_savings = savings * 4
        print(f"✓ Projected Annual Savings (4x/year):  ${annual_savings:.2f}")
        
        # Calculate how many rebalances per year before breaking even
        if fee_analysis['total_ibkr_fees'] > 0:
            breakeven_rebalances = ws_annual / fee_analysis['total_ibkr_fees']
            print(f"\n  → You can rebalance {breakeven_rebalances:.1f} times per year")
            print(f"    and still pay LESS than Wealthsimple")
    else:
        loss = abs(savings)
        print(f"✗ IBKR costs ${loss:.2f} MORE for this rebalance")
        print(f"  (But still ${ws_annual - fee_analysis['total_ibkr_fees']:.2f} cheaper annually)")
    
    print("=" * 80)
    print()
