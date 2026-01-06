"""
Module for generating portfolio visualization charts.
"""
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
