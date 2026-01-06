"""
Module for fetching and analyzing historical stock data.
"""
from ib_insync import IB, Stock, util
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd


class HistoricalDataManager:
    """Manages historical data retrieval and analysis."""
    
    def __init__(self, ib: IB):
        """
        Initialize historical data manager.
        
        Args:
            ib: Connected IB instance
        """
        self.ib = ib
    
    def get_historical_data(
        self,
        symbol: str,
        duration: str = "1 Y",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES",
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> pd.DataFrame:
        """
        Fetch historical data for a symbol.
        
        Args:
            symbol: Stock symbol
            duration: Duration string (e.g., "1 Y", "6 M", "1 M", "1 W")
            bar_size: Bar size (e.g., "1 day", "1 hour", "15 mins")
            what_to_show: Data type (TRADES, MIDPOINT, BID, ASK)
            exchange: Exchange to query
            currency: Currency
        
        Returns:
            DataFrame with historical data (date, open, high, low, close, volume)
        """
        try:
            # Create contract
            contract = Stock(symbol, exchange, currency)
            
            # Qualify the contract
            self.ib.qualifyContracts(contract)
            
            # Request historical data
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=True,  # Regular trading hours only
                formatDate=1
            )
            
            # Convert to DataFrame
            if bars:
                df = util.df(bars)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_returns(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate various return metrics from historical data.
        
        Args:
            df: DataFrame with historical price data
        
        Returns:
            Dictionary with return metrics
        """
        if df.empty or len(df) < 2:
            return {}
        
        first_price = df['close'].iloc[0]
        last_price = df['close'].iloc[-1]
        
        # Total return
        total_return = ((last_price - first_price) / first_price) * 100
        
        # Daily returns
        daily_returns = df['close'].pct_change().dropna()
        
        # Volatility (annualized standard deviation)
        volatility = daily_returns.std() * (252 ** 0.5) * 100  # Annualized
        
        # Max drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Sharpe ratio (assuming 0% risk-free rate for simplicity)
        avg_daily_return = daily_returns.mean()
        sharpe_ratio = (avg_daily_return / daily_returns.std()) * (252 ** 0.5) if daily_returns.std() > 0 else 0
        
        return {
            'total_return': total_return,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'start_price': first_price,
            'end_price': last_price,
            'days': len(df)
        }
    
    def get_position_history(
        self,
        symbol: str,
        avg_cost: float,
        duration: str = "1 Y"
    ) -> Dict:
        """
        Get historical data and calculate returns relative to purchase price.
        
        Args:
            symbol: Stock symbol
            avg_cost: Average cost basis
            duration: Duration to fetch
        
        Returns:
            Dictionary with historical data and metrics
        """
        df = self.get_historical_data(symbol, duration=duration)
        
        if df.empty:
            return {'symbol': symbol, 'error': 'No data available'}
        
        # Calculate metrics
        metrics = self.calculate_returns(df)
        
        # Calculate return from purchase price
        current_price = df['close'].iloc[-1]
        purchase_return = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
        
        return {
            'symbol': symbol,
            'data': df,
            'metrics': metrics,
            'avg_cost': avg_cost,
            'current_price': current_price,
            'purchase_return': purchase_return
        }
