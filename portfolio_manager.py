"""
Module for portfolio management including rebalancing operations.
"""
from ib_insync import IB
from typing import Dict, List, Optional
from decimal import Decimal


class PortfolioManager:
    """Manages portfolio operations including rebalancing."""
    
    def __init__(self, ib: IB):
        """
        Initialize portfolio manager.
        
        Args:
            ib: Connected IB instance
        """
        self.ib = ib
    
    def get_portfolio_positions(self) -> List[Dict]:
        """
        Get current portfolio positions.
        
        Returns:
            List of position dictionaries with contract and position details
        """
        positions = []
        # Use portfolio() instead of positions() to get full position details
        for item in self.ib.portfolio():
            positions.append({
                'contract': item.contract,
                'position': item.position,
                'avgCost': item.averageCost,
                'marketValue': item.marketValue,
                'marketPrice': item.marketPrice,
                'realizedPNL': item.realizedPNL,
                'unrealizedPNL': item.unrealizedPNL
            })
        return positions
    
    def get_account_summary(self) -> Dict:
        """
        Get account summary information.
        
        Returns:
            Dictionary with account values
        """
        account_values = {}
        for item in self.ib.accountSummary():
            account_values[item.tag] = {
                'value': item.value,
                'currency': item.currency,
                'account': item.account
            }
        return account_values
    
    def get_portfolio_value(self) -> float:
        """
        Get total portfolio value.
        
        Returns:
            Total portfolio value as float
        """
        summary = self.get_account_summary()
        if 'NetLiquidation' in summary:
            return float(summary['NetLiquidation']['value'])
        return 0.0
    
    def calculate_target_allocations(
        self,
        allocations: Dict[str, float],
        total_value: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate target dollar amounts for each allocation.
        
        Args:
            allocations: Dictionary mapping symbols to target percentages (0-100)
            total_value: Total portfolio value (if None, fetches current value)
        
        Returns:
            Dictionary mapping symbols to target dollar amounts
        """
        if total_value is None:
            total_value = self.get_portfolio_value()
        
        # Validate allocations sum to 100%
        total_allocation = sum(allocations.values())
        if abs(total_allocation - 100.0) > 0.01:
            raise ValueError(f"Allocations must sum to 100%, got {total_allocation}%")
        
        target_amounts = {}
        for symbol, percentage in allocations.items():
            target_amounts[symbol] = (percentage / 100.0) * total_value
        
        return target_amounts
    
    def get_market_price(self, symbol: str, exchange: str = 'SMART', currency: str = 'USD') -> float:
        """
        Get current market price for a symbol using delayed data.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange to query
            currency: Currency
        
        Returns:
            Current market price
        """
        from ib_insync import Stock
        
        try:
            contract = Stock(symbol, exchange, currency)
            self.ib.qualifyContracts(contract)
            
            # Request delayed market data (type 3 = delayed, no subscription needed)
            self.ib.reqMarketDataType(3)
            
            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Wait for data to arrive
            
            # Try different price fields in order of preference
            price = ticker.marketPrice()
            if price != price or price <= 0:  # Check for NaN or invalid
                price = ticker.last
            if price != price or price <= 0:
                price = ticker.close
            if price != price or price <= 0:
                # Use mid-point of bid/ask if available
                if ticker.bid > 0 and ticker.ask > 0:
                    price = (ticker.bid + ticker.ask) / 2
            
            # Cancel market data subscription
            self.ib.cancelMktData(contract)
            
            return float(price) if price == price else 0.0
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return 0.0
    
    def calculate_rebalance_trades(
        self,
        target_allocations: Dict[str, float],
        current_positions: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Calculate trades needed to rebalance portfolio.
        
        Args:
            target_allocations: Target dollar amounts per symbol
            current_positions: Current positions (if None, fetches current)
        
        Returns:
            List of trade instructions with symbol, action, and quantity
        """
        if current_positions is None:
            current_positions = self.get_portfolio_positions()
        
        # Build current position map
        current_map = {}
        for pos in current_positions:
            symbol = pos['contract'].symbol
            current_map[symbol] = {
                'quantity': pos['position'],
                'marketValue': pos['marketValue'],
                'marketPrice': pos['marketPrice']
            }
        
        trades = []
        
        # Calculate trades for each target allocation
        for symbol, target_value in target_allocations.items():
            current_value = current_map.get(symbol, {}).get('marketValue', 0.0)
            current_price = current_map.get(symbol, {}).get('marketPrice', 0.0)
            
            # If we don't have current price (not in portfolio), fetch it
            if current_price <= 0:
                current_price = self.get_market_price(symbol)
                if current_price <= 0:
                    print(f"Warning: Could not get price for {symbol}, skipping")
                    continue
            
            difference = target_value - current_value
            
            if abs(difference) < 0.01:  # Skip negligible differences
                continue
            
            quantity_change = difference / current_price
            # Round to whole shares - IB API doesn't support fractional shares
            quantity_change = round(quantity_change)
            
            if quantity_change == 0:  # Skip if rounds to zero
                continue
            
            trades.append({
                'symbol': symbol,
                'action': 'BUY' if difference > 0 else 'SELL',
                'quantity': abs(quantity_change),
                'price': current_price,
                'target_value': target_value,
                'current_value': current_value,
                'difference': difference
            })
        
        return trades
    
    def get_buying_power(self) -> float:
        """
        Get available buying power.
        
        Returns:
            Available buying power as float
        """
        summary = self.get_account_summary()
        if 'BuyingPower' in summary:
            return float(summary['BuyingPower']['value'])
        return 0.0
    
    def get_cash_balance(self) -> float:
        """
        Get cash balance.
        
        Returns:
            Cash balance as float
        """
        summary = self.get_account_summary()
        if 'TotalCashValue' in summary:
            return float(summary['TotalCashValue']['value'])
        return 0.0
