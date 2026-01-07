# IBKR vs Wealthsimple Fee Comparison

Comprehensive cost analysis comparing Interactive Brokers' per-trade commission structure against Wealthsimple's annual management fee model.

---

## Overview

This module helps you determine which broker is more cost-effective based on your trading frequency and portfolio size.

### Fee Structures

#### Interactive Brokers (IBKR)
**Tiered Commission Structure (CAD per share):**
- ≤ 300,000 shares: $0.008 per share
- 300,001 - 3,000,000: $0.005 per share
- 3,000,001 - 20,000,000: $0.004 per share
- > 20,000,000: $0.003 per share

**Per-Order Constraints:**
- Minimum: $1.00 CAD
- Maximum: 0.5% of trade value

**Additional Fees:** Exchange fees, clearing fees, and regulatory fees may apply (typically minimal for Canadian stocks).

#### Wealthsimple Portfolio Management
**Annual Management Fee:** 0.5% of portfolio value, charged regardless of trading activity.

---

## Key Insights

### When IBKR is More Cost-Effective

✅ **Infrequent Rebalancing** - Quarterly or less frequent portfolio adjustments  
✅ **Long-Term Holdings** - Buy-and-hold strategy with minimal turnover  
✅ **Larger Trades** - Higher share counts reduce the impact of $1 minimum  
✅ **Active DIY Management** - You control when and how often to trade  


### When Wealthsimple May Be Better

❌ **Many Small Trades** - Frequent micro-adjustments hitting the $1 minimum  
❌ **Small Portfolios** - Below ~$50,000 where 0.5% is minimal  

---

## Real-World Examples

### Example 1: Conservative Rebalancer
**Portfolio:** $1,000,000 CAD  
**Strategy:** Quarterly rebalancing (4 times per year)  
**Typical Rebalancing:** 3-5 trades per session

**Annual Costs:**
- **Wealthsimple:** $5,000.00 (0.5% × $1M)
- **IBKR:** $12-20 (4 sessions × $3-5 per session)
- **Savings with IBKR:** $4,980-4,988 per year

**Breakeven Point:** You could rebalance **1,666 times per year** (5+ times per day) before IBKR becomes more expensive than Wealthsimple.

### Example 2: Active Rebalancer
**Portfolio:** $500,000 CAD  
**Strategy:** Monthly rebalancing (12 times per year)  
**Typical Rebalancing:** 4-6 trades per session

**Annual Costs:**
- **Wealthsimple:** $2,500.00
- **IBKR:** $48-72 (12 sessions × $4-6)
- **Savings with IBKR:** $2,428-2,452 per year

**Breakeven Point:** ~520 rebalances per year (1.4 per day) before IBKR costs more.

### Example 3: Very Active Trader
**Portfolio:** $200,000 CAD  
**Strategy:** Weekly rebalancing (52 times per year)  
**Typical Rebalancing:** 5 small trades per session

**Annual Costs:**
- **Wealthsimple:** $1,000.00
- **IBKR:** $260 (52 sessions × $5)
- **Savings with IBKR:** $740 per year

## Using the Fee Calculator

### Command: `fees`

Displays a comprehensive fee comparison based on your actual portfolio value and positions.

```bash
> fees

IBKR vs WEALTHSIMPLE FEE COMPARISON
================================================================================
Portfolio Value: $1,077,254.16 CAD
Wealthsimple Annual Fee (0.5%): $5,386.27 CAD

BREAKEVEN ANALYSIS BY TRADE SIZE
================================================================================

Small trades (10 shares @ $176.13)
--------------------------------------------------------------------------------
  Trade Value:              $1,761.29
  IBKR Fee per Trade:       $1.00
  Max Annual Trades:        5386
  Max Monthly Trades:       448.9
  Max Weekly Trades:        103.6

Medium trades (50 shares @ $176.13)
--------------------------------------------------------------------------------
  Trade Value:              $8,806.45
  IBKR Fee per Trade:       $4.00
  Max Annual Trades:        1346
  Max Monthly Trades:       112.2
  Max Weekly Trades:        25.9

Large trades (100 shares @ $176.13)
--------------------------------------------------------------------------------
  Trade Value:              $17,612.90
  IBKR Fee per Trade:       $8.00
  Max Annual Trades:        673
  Max Monthly Trades:       56.1
  Max Weekly Trades:        13.0
```

### Rebalancing Fee Analysis

When you run `plan` or `rebalance`, the system automatically calculates exact IBKR fees for your specific trades:

```bash
> plan

REBALANCING PLAN
================================================================================
Symbol     Action   Quantity     Difference
SPY        SELL     18           -$12,287.66
IWM        BUY      5            +$1,152.74
TLT        BUY      9            +$749.56

REBALANCING FEE ANALYSIS
================================================================================
Portfolio Value: $1,077,254.16 CAD
Number of Trades: 3

TRADE-BY-TRADE FEE BREAKDOWN
--------------------------------------------------------------------------------
Symbol     Action Shares     Price        Trade Value     IBKR Fee
SPY        SELL   18         $690.33      $12,425.94      $1.00
IWM        BUY    5          $252.71      $1,263.55       $1.00
TLT        BUY    9          $87.26       $785.34         $1.00
--------------------------------------------------------------------------------
TOTAL IBKR FEES:                                          $3.00

COMPARISON TO WEALTHSIMPLE
================================================================================
Wealthsimple Annual Fee (0.5%):        $5,386.27
Wealthsimple Quarterly Equivalent:     $1,346.57
IBKR Fees for This Rebalance:          $3.00

✓ SAVINGS with IBKR (vs quarterly):    $1343.57
✓ Projected Annual Savings (4x/year):  $5374.27

  → You can rebalance 1795.4 times per year
    and still pay LESS than Wealthsimple
================================================================================
```

---

## Fee Calculation Details

### IBKR Fee Calculation Logic

For each trade, the system:

1. **Calculates base fee** using tiered rates:
   - Multiply number of shares by applicable tier rate
   - Accumulate fees across multiple tiers if necessary

2. **Applies minimum constraint:**
   - If calculated fee < $1.00, use $1.00

3. **Applies maximum constraint:**
   - If calculated fee > 0.5% of trade value, cap at 0.5%

**Examples:**

| Shares | Price | Trade Value | Base Fee | Applied Fee | Reason |
|--------|-------|-------------|----------|-------------|--------|
| 5 | $100 | $500 | $0.04 | $1.00 | Minimum applies |
| 50 | $100 | $5,000 | $0.40 | $1.00 | Minimum applies |
| 150 | $100 | $15,000 | $1.20 | $1.20 | Within constraints |
| 1,000 | $100 | $100,000 | $8.00 | $8.00 | Within constraints |
| 10,000 | $50 | $500,000 | $80.00 | $80.00 | Within constraints |
| 1,000 | $1,000 | $1,000,000 | $8.00 | $8.00 | Below 0.5% max |

### Wealthsimple Fee Calculation

Simple annual calculation:
```
Annual Fee = Portfolio Value × 0.005 (0.5%)
Quarterly Equivalent = Annual Fee ÷ 4
```

The quarterly equivalent is used for comparison since most investors rebalance quarterly.

---

## Recommendations

### For Most Investors (IBKR Recommended)

If you're rebalancing **quarterly or less frequently**, IBKR will save you thousands annually:

| Portfolio Size | Wealthsimple Annual Fee | IBKR Annual Cost (4x/year) | Annual Savings |
|----------------|-------------------------|----------------------------|----------------|
| $100,000 | $500 | $12-20 | ~$480 |
| $250,000 | $1,250 | $12-20 | ~$1,230 |
| $500,000 | $2,500 | $12-20 | ~$2,480 |
| $1,000,000 | $5,000 | $12-20 | ~$4,980 |
| $2,000,000 | $10,000 | $12-20 | ~$9,980 |

### When to Consider Wealthsimple

- **Very small portfolios** (< $20,000) where 0.5% is negligible
- **Daily trading activity** with dozens of small trades
- **No time for DIY management** and value the hands-off approach
- **Tax-loss harvesting** with very frequent adjustments

---

## Technical Implementation

### Module: `fees.py`

**Key Functions:**

```python
from fees import FeeComparator, display_fee_comparison, display_rebalance_fees

# Initialize comparator
comparator = FeeComparator(portfolio_value=1_000_000)

# Calculate single trade fee
fee = comparator.calculate_ibkr_trade_fee(shares=50, share_price=100.0)
# Returns: $1.00 (minimum applies)

# Calculate breakeven analysis
analysis = comparator.calculate_breakeven_trades(
    avg_shares_per_trade=100, 
    avg_share_price=100.0
)
# Returns: max_annual_trades, max_monthly_trades, max_weekly_trades

# Calculate fees for specific rebalancing plan
fee_breakdown = comparator.calculate_rebalance_fees(trades=[
    {'symbol': 'SPY', 'action': 'BUY', 'quantity': 10, 'price': 690.0},
    {'symbol': 'QQQ', 'action': 'SELL', 'quantity': 5, 'price': 617.0}
])
```

### Integration with Portfolio Manager

The fee calculator automatically integrates with:
- `plan` command: Shows fees before executing
- `rebalance` command: Displays fees as part of execution summary
- `fees` command: Standalone fee comparison analysis

---

## Assumptions & Limitations

### Assumptions
- Quarterly rebalancing (4 times per year) for baseline comparisons
- No exchange fees, clearing fees, or regulatory fees included in IBKR calculations
- Wealthsimple fee is exactly 0.5% with no hidden costs
- All prices in CAD

### Limitations
- Does not account for IBKR monthly minimum fees (waived for accounts > $100k)
- Does not consider Wealthsimple's additional services (tax-loss harvesting, etc.)
- Exchange/clearing/regulatory fees may add ~$0.01-0.10 per trade on IBKR
- Currency conversion fees not included (only applies to non-CAD stocks)

### Real-World Adjustments
In practice, add ~5-10% to IBKR fees for miscellaneous exchange/regulatory fees. Even with this adjustment, IBKR remains dramatically cheaper for typical rebalancing patterns.

---

## Conclusion

**For portfolios > $50,000 with quarterly or less frequent rebalancing, IBKR saves thousands annually.**

The `fees` command provides real-time, portfolio-specific analysis to help you make informed decisions about broker selection based on your actual trading patterns and portfolio size.

Use `fees` before major portfolio decisions to understand your true cost structure.
