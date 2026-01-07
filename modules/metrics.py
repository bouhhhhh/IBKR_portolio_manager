"""

Financial metrics included :
- Value at Risk (VaR)
- Beta
- Sortino Ratio
- Calmar Ratio
"""

import numpy as np
from typing import Union, Optional



# percentage value are displayed as positive numbers (e.g., 0.05 means 5% loss)   

"""
Calculate Value at Risk (VaR) - the maximum expected loss over a time period
at a given confidence level.

Args:
    returns: Series or array of returns (e.g., daily returns)
    confidence_level: Confidence level (default 0.95 for 95% VaR)
    method: Method to use ('historical', 'parametric')
    
Returns:
    VaR as a positive float (e.g., 0.05 means 5% potential loss)
"""
def calculate_var(
    returns: np.ndarray,
    confidence_level: float = 0.95,
    method: str = "historical"
) -> float:

    if len(returns) == 0:
        return 0.0
    
    returns_array = np.array(returns)
    
    if method == "historical":
        # Historical VaR: the (1-confidence_level) percentile of returns
        var = np.percentile(returns_array, (1 - confidence_level) * 100)
        return abs(var) * 100  # Return as positive percentage
    
    elif method == "parametric":
        # Parametric VaR: assumes normal distribution
        mean = float(np.mean(returns_array))
        std = float(np.std(returns_array))
        # Z-score for confidence level (e.g., 1.645 for 95%)
        from scipy import stats
        z_score = float(stats.norm.ppf(1 - confidence_level))
        var = mean + z_score * std
        return abs(var) * 100  # Return as positive percentage
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'historical' or 'parametric'")

"""
Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
This is the expected loss given that the loss exceeds VaR.

Args:
    returns: Series or array of returns
    confidence_level: Confidence level (default 0.95)
    
Returns:
    CVaR as a positive percentage 
"""
def calculate_cvar(
    returns: np.ndarray,
    confidence_level: float = 0.95
) -> float:

    if len(returns) == 0:
        return 0.0
    
    returns_array = np.array(returns)
    var_threshold = np.percentile(returns_array, (1 - confidence_level) * 100)
    
    # CVaR is the mean of all returns below the VaR threshold
    tail_losses = returns_array[returns_array <= var_threshold]
    
    if len(tail_losses) == 0:
        return 0.0
    
    cvar = float(np.mean(tail_losses))
    return abs(cvar) * 100  # Return as positive percentage

"""
Calculate Beta - measure of systematic risk relative to a benchmark.

Beta = Covariance(Portfolio, Benchmark) / Variance(Benchmark)

Args:
    portfolio_returns: Portfolio returns
    benchmark_returns: Benchmark returns (e.g., SPY)
    
Returns:
    Beta coefficient
    
Interpretation:
    Beta = 1.0: Moves with the market
    Beta > 1.0: More volatile than the market
    Beta < 1.0: Less volatile than the market
    Beta < 0.0: Moves opposite to the market
"""
def calculate_beta(
    portfolio_returns: np.ndarray,
    benchmark_returns: np.ndarray
) -> float:

    if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
        return 0.0
    
    # Ensure same length
    min_len = min(len(portfolio_returns), len(benchmark_returns))
    portfolio_returns = np.array(portfolio_returns)[-min_len:]
    benchmark_returns = np.array(benchmark_returns)[-min_len:]
    
    # Calculate covariance and variance
    covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
    benchmark_variance = np.var(benchmark_returns)
    
    if benchmark_variance == 0:
        return 0.0
    
    beta = covariance / benchmark_variance
    return float(beta)

"""
Calculate Jensen's Alpha - excess return over expected return based on CAPM.

Alpha = Portfolio_Return - (Risk_Free_Rate + Beta * (Benchmark_Return - Risk_Free_Rate))

Args:
    portfolio_returns: Portfolio returns
    benchmark_returns: Benchmark returns
    risk_free_rate: Risk-free rate (annualized, e.g., 0.04 for 4%)
    
Returns:
    Alpha as annualized percentage
    
Interpretation:
    Alpha > 0: Outperforming risk-adjusted expectations
    Alpha < 0: Underperforming risk-adjusted expectations
"""
def calculate_alpha(
    portfolio_returns: np.ndarray,
    benchmark_returns: np.ndarray,
    risk_free_rate: float = 0.0
) -> float:

    if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
        return 0.0
    
    portfolio_returns = np.array(portfolio_returns)
    benchmark_returns = np.array(benchmark_returns)
    
    # Calculate average returns (annualized)
    avg_portfolio_return = float(np.mean(portfolio_returns) * 252)  # Assuming daily returns
    avg_benchmark_return = float(np.mean(benchmark_returns) * 252)
    
    # Calculate beta
    beta = calculate_beta(portfolio_returns, benchmark_returns)
    
    # Calculate alpha
    expected_return = risk_free_rate + beta * (avg_benchmark_return - risk_free_rate)
    alpha = avg_portfolio_return - expected_return
    
    return float(alpha)


def calculate_sortino_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0,
    target_return: float = 0.0
) -> float:
    """
    Calculate Sortino Ratio - risk-adjusted return using downside deviation.
    Similar to Sharpe Ratio but only penalizes downside volatility.
    
    Sortino = (Return - Target) / Downside_Deviation
    
    Args:
        returns: Series or array of returns
        risk_free_rate: Risk-free rate (annualized)
        target_return: Target return (default 0.0)
        
    Returns:
        Sortino Ratio
        
    Interpretation:
        Higher is better. Sortino > 2.0 is considered good.
        Sortino > Sharpe indicates asymmetric return distribution with positive skew.
    """
    if len(returns) == 0:
        return 0.0
    
    returns_array = np.array(returns)
    
    # Calculate average return (annualized)
    avg_return = float(np.mean(returns_array) * 252)  # Assuming daily returns
    
    # Calculate downside deviation (only negative returns)
    downside_returns = returns_array[returns_array < target_return]
    
    if len(downside_returns) == 0:
        return float('inf') if avg_return > risk_free_rate else 0.0
    
    downside_std = float(np.std(downside_returns) * np.sqrt(252))  # Annualized
    
    if downside_std == 0:
        return 0.0
    
    sortino = (avg_return - risk_free_rate) / downside_std
    return float(sortino)

"""
Calculate Calmar Ratio - annualized return divided by maximum drawdown.
Measures return per unit of drawdown risk.

Calmar = Annualized_Return / |Max_Drawdown|

Args:
    returns: Series or array of returns
    max_drawdown: Pre-calculated max drawdown (if None, will calculate)
    
Returns:
    Calmar Ratio
    
Interpretation:
    Higher is better. Calmar > 0.5 is considered good.
    Shows return efficiency relative to worst historical loss.
"""
def calculate_calmar_ratio(
    returns: np.ndarray,
    max_drawdown: Optional[float] = None
) -> float:

    if len(returns) == 0:
        return 0.0
    
    returns_array = np.array(returns)
    
    # Calculate annualized return
    avg_return = float(np.mean(returns_array) * 252 * 100)  # As percentage
    
    # Calculate max drawdown if not provided
    if max_drawdown is None:
        cumulative_returns = np.cumprod(1 + returns_array)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = float(abs(np.min(drawdowns)) * 100)  # As positive percentage
    else:
        max_drawdown = abs(max_drawdown)  # Ensure positive
    
    if max_drawdown == 0:
        return float('inf') if avg_return > 0 else 0.0
    
    calmar = avg_return / max_drawdown
    return float(calmar)

"""
Calculate Information Ratio - measures portfolio returns above benchmark
per unit of tracking error (active risk).

IR = (Portfolio_Return - Benchmark_Return) / Tracking_Error

Args:
    portfolio_returns: Portfolio returns
    benchmark_returns: Benchmark returns
    
Returns:
    Information Ratio
    
Interpretation:
    IR > 0.5: Good active management
    IR > 1.0: Excellent active management
    Measures consistency of outperformance
"""
def calculate_information_ratio(
    portfolio_returns: np.ndarray,
    benchmark_returns: np.ndarray
) -> float:

    if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
        return 0.0
    
    # Ensure same length
    min_len = min(len(portfolio_returns), len(benchmark_returns))
    portfolio_returns = np.array(portfolio_returns)[-min_len:]
    benchmark_returns = np.array(benchmark_returns)[-min_len:]
    
    # Calculate excess returns
    excess_returns = portfolio_returns - benchmark_returns
    
    # Annualized excess return
    avg_excess_return = float(np.mean(excess_returns) * 252)
    
    # Tracking error (annualized standard deviation of excess returns)
    tracking_error = float(np.std(excess_returns) * np.sqrt(252))
    
    if tracking_error == 0:
        return 0.0
    
    information_ratio = avg_excess_return / tracking_error
    return float(information_ratio)

"""
****Calculate all available metrics for a portfolio.****

Args:
    portfolio_returns: Portfolio returns
    benchmark_returns: Benchmark returns (optional, for Beta/Alpha/IR)
    max_drawdown: Pre-calculated max drawdown (optional)
    risk_free_rate: Risk-free rate (default 4%)
    
Returns:
    Dictionary with all calculated metrics
"""
def calculate_all_metrics(
    portfolio_returns: np.ndarray,
    benchmark_returns: Optional[np.ndarray] = None,
    max_drawdown: Optional[float] = None,
    risk_free_rate: float = 0.04
) -> dict:

    metrics = {
        'var_95': calculate_var(portfolio_returns, confidence_level=0.95),
        'var_99': calculate_var(portfolio_returns, confidence_level=0.99),
        'cvar_95': calculate_cvar(portfolio_returns, confidence_level=0.95),
        'sortino_ratio': calculate_sortino_ratio(portfolio_returns, risk_free_rate),
        'calmar_ratio': calculate_calmar_ratio(portfolio_returns, max_drawdown)
    }
    
    if benchmark_returns is not None:
        metrics['beta'] = calculate_beta(portfolio_returns, benchmark_returns)
        metrics['alpha'] = calculate_alpha(portfolio_returns, benchmark_returns, risk_free_rate)
        metrics['information_ratio'] = calculate_information_ratio(portfolio_returns, benchmark_returns)
    
    return metrics


if __name__ == "__main__":
    # Example usage and testing
    print("Portfolio Metrics Module - Example Usage\n")
    
    # Generate sample data
    np.random.seed(42)
    portfolio_returns = np.random.normal(0.0005, 0.01, 252)  # Daily returns for 1 year
    benchmark_returns = np.random.normal(0.0004, 0.008, 252)
    
    print("Sample Portfolio Metrics:")
    print("-" * 50)
    
    var_95 = calculate_var(portfolio_returns, 0.95)
    print(f"Value at Risk (95%):          {var_95:.2f}%")
    
    cvar_95 = calculate_cvar(portfolio_returns, 0.95)
    print(f"Conditional VaR (95%):        {cvar_95:.2f}%")
    
    beta = calculate_beta(portfolio_returns, benchmark_returns)
    print(f"Beta:                         {beta:.3f}")
    
    alpha = calculate_alpha(portfolio_returns, benchmark_returns)
    print(f"Alpha (annualized):           {alpha:.2f}%")
    
    sortino = calculate_sortino_ratio(portfolio_returns)
    print(f"Sortino Ratio:                {sortino:.3f}")
    
    calmar = calculate_calmar_ratio(portfolio_returns)
    print(f"Calmar Ratio:                 {calmar:.3f}")
    
    ir = calculate_information_ratio(portfolio_returns, benchmark_returns)
    print(f"Information Ratio:            {ir:.3f}")
    
    print("\n" + "-" * 50)
    print("\nAll metrics calculated successfully!")
