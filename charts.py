"""
Module for generating portfolio visualization charts.
"""
import warnings
import os

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Suppress macOS-specific matplotlib backend warnings
os.environ['MPLBACKEND'] = 'TkAgg'  # Use TkAgg backend to avoid macOS issues

import matplotlib
matplotlib.use('TkAgg', force=True)

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Dict
import numpy as np


class PortfolioCharts:
    """Generates charts for portfolio visualization."""
    
    @staticmethod
    def plot_allocation_pie(positions: List[Dict], title: str = "Portfolio Allocation"):
        """
        Create a pie chart showing portfolio allocation by position.
        
        Args:
            positions: List of position dictionaries with marketValue
            title: Chart title
        """
        if not positions:
            print("No positions to display.")
            return
        
        # Extract symbols and values
        symbols = [pos['contract'].symbol for pos in positions]
        values = [pos['marketValue'] for pos in positions]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create pie chart with percentages
        colors = plt.cm.Set3(np.linspace(0, 1, len(symbols)))
        wedges, texts, autotexts = ax.pie(
            values,
            labels=symbols,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 10}
        )
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Add legend with values
        legend_labels = [f"{symbol}: ${value:,.2f}" for symbol, value in zip(symbols, values)]
        ax.legend(legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_returns_bar(position_returns: List[Dict], title: str = "Position Returns"):
        """
        Create a bar chart showing returns for each position.
        
        Args:
            position_returns: List of position return dictionaries
            title: Chart title
        """
        if not position_returns:
            print("No position returns to display.")
            return
        
        # Extract data
        symbols = [pos['symbol'] for pos in position_returns]
        returns = [pos['return_percentage'] for pos in position_returns]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Color bars based on positive/negative
        colors = ['green' if r > 0 else 'red' if r < 0 else 'gray' for r in returns]
        
        # Create bar chart
        bars = ax.bar(symbols, returns, color=colors, alpha=0.7, edgecolor='black')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'{height:+.2f}%',
                ha='center',
                va='bottom' if height > 0 else 'top',
                fontsize=9,
                fontweight='bold'
            )
        
        # Formatting
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_xlabel('Symbol', fontsize=12, fontweight='bold')
        ax.set_ylabel('Return (%)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        # Add legend
        green_patch = mpatches.Patch(color='green', alpha=0.7, label='Positive Return')
        red_patch = mpatches.Patch(color='red', alpha=0.7, label='Negative Return')
        ax.legend(handles=[green_patch, red_patch], loc='upper right')
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_pnl_breakdown(position_returns: List[Dict], title: str = "P&L Breakdown by Position"):
        """
        Create a horizontal bar chart showing P&L for each position.
        
        Args:
            position_returns: List of position return dictionaries
            title: Chart title
        """
        if not position_returns:
            print("No position P&L to display.")
            return
        
        # Extract data
        symbols = [pos['symbol'] for pos in position_returns]
        pnl_values = [pos['unrealized_pnl'] for pos in position_returns]
        
        # Sort by P&L
        sorted_data = sorted(zip(symbols, pnl_values), key=lambda x: x[1], reverse=True)
        symbols_sorted, pnl_sorted = zip(*sorted_data)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, max(6, len(symbols) * 0.5)))
        
        # Color bars based on positive/negative
        colors = ['green' if p > 0 else 'red' if p < 0 else 'gray' for p in pnl_sorted]
        
        # Create horizontal bar chart
        bars = ax.barh(symbols_sorted, pnl_sorted, color=colors, alpha=0.7, edgecolor='black')
        
        # Add value labels on bars
        for bar, value in zip(bars, pnl_sorted):
            width = bar.get_width()
            ax.text(
                width,
                bar.get_y() + bar.get_height()/2.,
                f' ${value:,.2f}',
                ha='left' if width > 0 else 'right',
                va='center',
                fontsize=9,
                fontweight='bold'
            )
        
        # Formatting
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_xlabel('Unrealized P&L ($)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Symbol', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3)
        
        # Add total P&L to title
        total_pnl = sum(pnl_sorted)
        ax.text(
            0.98, 0.02,
            f'Total P&L: ${total_pnl:,.2f}',
            transform=ax.transAxes,
            ha='right',
            va='bottom',
            fontsize=11,
            fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_allocation_vs_target(
        current_allocations: Dict[str, float],
        target_allocations: Dict[str, float],
        title: str = "Current vs Target Allocation"
    ):
        """
        Create a grouped bar chart comparing current vs target allocation.
        
        Args:
            current_allocations: Dictionary of symbol -> current percentage
            target_allocations: Dictionary of symbol -> target percentage
            title: Chart title
        """
        # Get all symbols
        all_symbols = sorted(set(list(current_allocations.keys()) + list(target_allocations.keys())))
        
        if not all_symbols:
            print("No allocation data to display.")
            return
        
        # Prepare data
        current_values = [current_allocations.get(s, 0) for s in all_symbols]
        target_values = [target_allocations.get(s, 0) for s in all_symbols]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Set up bar positions
        x = np.arange(len(all_symbols))
        width = 0.35
        
        # Create grouped bars
        bars1 = ax.bar(x - width/2, current_values, width, label='Current', color='steelblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, target_values, width, label='Target', color='orange', alpha=0.8)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(
                        bar.get_x() + bar.get_width()/2.,
                        height,
                        f'{height:.1f}%',
                        ha='center',
                        va='bottom',
                        fontsize=8
                    )
        
        # Formatting
        ax.set_xlabel('Symbol', fontsize=12, fontweight='bold')
        ax.set_ylabel('Allocation (%)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(all_symbols)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_price_history(
        df,
        symbol: str,
        avg_cost: float = None,
        title: str = None
    ):
        """
        Plot historical price chart with optional purchase price line.
        
        Args:
            df: DataFrame with historical data (must have 'close' column and datetime index)
            symbol: Stock symbol
            avg_cost: Average cost basis to display as horizontal line
            title: Custom title (default uses symbol)
        """
        if df is None or df.empty:
            print(f"No historical data available for {symbol}")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot price
        ax1.plot(df.index, df['close'], linewidth=2, color='steelblue', label='Close Price')
        
        # Add purchase price line if provided
        if avg_cost is not None and avg_cost > 0:
            ax1.axhline(y=avg_cost, color='red', linestyle='--', linewidth=2, 
                       label=f'Avg Cost: ${avg_cost:.2f}', alpha=0.7)
            
            # Shade profit/loss regions
            current_price = df['close'].iloc[-1]
            if current_price > avg_cost:
                ax1.fill_between(df.index, avg_cost, df['close'], 
                               where=(df['close'] >= avg_cost), 
                               alpha=0.2, color='green', label='Profit Region')
            else:
                ax1.fill_between(df.index, avg_cost, df['close'],
                               where=(df['close'] <= avg_cost),
                               alpha=0.2, color='red', label='Loss Region')
        
        # Formatting price chart
        ax1.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
        ax1.set_title(title or f'{symbol} Price History', fontsize=14, fontweight='bold', pad=20)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Add price annotations
        first_price = df['close'].iloc[0]
        last_price = df['close'].iloc[-1]
        price_change = ((last_price - first_price) / first_price) * 100
        
        color = 'green' if price_change > 0 else 'red'
        ax1.text(0.02, 0.98, f'Start: ${first_price:.2f}', transform=ax1.transAxes,
                va='top', fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        ax1.text(0.02, 0.91, f'Current: ${last_price:.2f}\n({price_change:+.2f}%)', 
                transform=ax1.transAxes, va='top', fontsize=10, color=color,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Plot volume
        colors = ['green' if df['close'].iloc[i] >= df['open'].iloc[i] else 'red' 
                 for i in range(len(df))]
        ax2.bar(df.index, df['volume'], color=colors, alpha=0.5, width=1)
        ax2.set_ylabel('Volume', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Format x-axis
        fig.autofmt_xdate()
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_performance_metrics(
        metrics: dict,
        symbol: str
    ):
        """
        Display performance metrics as a bar chart.
        
        Args:
            metrics: Dictionary with performance metrics
            symbol: Stock symbol
        """
        if not metrics or 'total_return' not in metrics:
            print(f"No metrics available for {symbol}")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepare data (exclude non-percentage values)
        metric_names = ['Total Return', 'Volatility', 'Max Drawdown']
        metric_values = [
            metrics['total_return'],
            metrics['volatility'],
            metrics['max_drawdown']
        ]
        colors = ['green' if v > 0 else 'red' for v in metric_values]
        
        # Create bars
        bars = ax.bar(metric_names, metric_values, color=colors, alpha=0.7, edgecolor='black')
        
        # Add value labels
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:+.2f}%',
                   ha='center', va='bottom' if height > 0 else 'top',
                   fontsize=11, fontweight='bold')
        
        # Add Sharpe ratio as text annotation
        sharpe = metrics.get('sharpe_ratio', 0)
        sharpe_color = 'green' if sharpe > 1 else 'orange' if sharpe > 0 else 'red'
        ax.text(0.98, 0.98, f'Sharpe Ratio: {sharpe:.2f}',
               transform=ax.transAxes, ha='right', va='top',
               fontsize=12, fontweight='bold', color=sharpe_color,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Formatting
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{symbol} Performance Metrics ({metrics.get("days", 0)} days)',
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.show()
