"""
Module for handling trading transactions and order execution.
"""
from ib_insync import IB, Stock, MarketOrder, Trade, Fill
from typing import Optional


class TransactionManager:
    """Handles trading operations and order execution."""
    
    def __init__(self, ib: IB):
        """
        Initialize transaction manager.
        
        Args:
            ib: Connected IB instance
        """
        self.ib = ib
    
    def place_buy_async(
        self,
        symbol: str,
        qty: float = 1.0,
        currency: str = "USD",
        exchange: str = "SMART",
        dry_run: bool = False
    ) -> Trade:
        """
        Place a market BUY order with async event handlers.
        
        Args:
            symbol: Stock symbol to buy
            qty: Quantity to buy (supports fractional shares)
            currency: Currency for the trade
            exchange: Exchange to route the order
            dry_run: If True, simulate the order first
        
        Returns:
            Trade: Trade object with attached event handlers
        """
        contract = Stock(symbol, exchange, currency)
        order = MarketOrder("BUY", qty)
        order.tif = "GTC"  # Good-Til-Cancelled to allow orders outside market hours
        order.outsideRth = True  # Allow orders outside regular trading hours
        
        # Optional: preview order first
        if dry_run:
            try:
                whatif = self.ib.whatIfOrder(contract, order)
                if whatif:
                    print(f"[WHAT-IF] {symbol} - Status: {whatif.initMarginChange} init margin, {whatif.commission} commission")
            except Exception as e:
                print(f"[WHAT-IF] Could not simulate order: {e}")
        
        trade = self.ib.placeOrder(contract, order)
        
        # Attach event handlers
        def on_status(tr: Trade):
            print(f"[STATUS] {symbol} {tr.orderStatus.status}  filled={tr.orderStatus.filled}  remaining={tr.orderStatus.remaining}")
            if tr.isDone():
                print(f"[DONE]   {symbol} {tr.orderStatus.status}  "
                      f"filled={tr.orderStatus.filled}  avgPx={tr.orderStatus.avgFillPrice or 0.0}")
                # Detach handlers when done
                tr.statusEvent -= on_status
                tr.fillEvent -= on_fill
                tr.filledEvent -= on_filled
        
        def on_fill(tr: Trade, fill: Fill):
            ex = fill.execution
            print(f"[FILL]   {symbol} {ex.shares} @ {ex.price} on {ex.exchange}  time={ex.time}")
        
        def on_filled(tr: Trade):
            # Fires once when fully filled
            print(f"[FILLED] {symbol} totalFilled={tr.orderStatus.filled} avgPx={tr.orderStatus.avgFillPrice or 0.0}")
        
        trade.statusEvent += on_status
        trade.fillEvent += on_fill
        trade.filledEvent += on_filled
        
        print(f"Submitted BUY: {qty} x {symbol}")
        return trade
    
    def place_sell_async(
        self,
        symbol: str,
        qty: float = 1.0,
        currency: str = "USD",
        exchange: str = "SMART",
        dry_run: bool = False
    ) -> Trade:
        """
        Place a market SELL order with async event handlers.
        
        Args:
            symbol: Stock symbol to sell
            qty: Quantity to sell (supports fractional shares)
            currency: Currency for the trade
            exchange: Exchange to route the order
            dry_run: If True, simulate the order first
        
        Returns:
            Trade: Trade object with attached event handlers
        """
        contract = Stock(symbol, exchange, currency)
        order = MarketOrder("SELL", qty)
        order.tif = "GTC"  # Good-Til-Cancelled to allow orders outside market hours
        order.outsideRth = True  # Allow orders outside regular trading hours
        
        if dry_run:
            try:
                whatif = self.ib.whatIfOrder(contract, order)
                if whatif:
                    print(f"[WHAT-IF] {symbol} - Status: {whatif.initMarginChange} init margin, {whatif.commission} commission")
            except Exception as e:
                print(f"[WHAT-IF] Could not simulate order: {e}")
        
        trade = self.ib.placeOrder(contract, order)
        
        # Attach event handlers
        def on_status(tr: Trade):
            print(f"[STATUS] {symbol} {tr.orderStatus.status}  filled={tr.orderStatus.filled}  remaining={tr.orderStatus.remaining}")
            if tr.isDone():
                print(f"[DONE]   {symbol} {tr.orderStatus.status}  "
                      f"filled={tr.orderStatus.filled}  avgPx={tr.orderStatus.avgFillPrice or 0.0}")
                tr.statusEvent -= on_status
                tr.fillEvent -= on_fill
                tr.filledEvent -= on_filled
        
        def on_fill(tr: Trade, fill: Fill):
            ex = fill.execution
            print(f"[FILL]   {symbol} {ex.shares} @ {ex.price} on {ex.exchange}  time={ex.time}")
        
        def on_filled(tr: Trade):
            print(f"[FILLED] {symbol} totalFilled={tr.orderStatus.filled} avgPx={tr.orderStatus.avgFillPrice or 0.0}")
        
        trade.statusEvent += on_status
        trade.fillEvent += on_fill
        trade.filledEvent += on_filled
        
        print(f"Submitted SELL: {qty} x {symbol}")
        return trade
    
    def wait_for_trade_completion(self, trade: Trade, timeout: float = 1.0) -> Trade:
        """
        Wait for a trade to complete.
        
        Args:
            trade: Trade object to monitor
            timeout: Timeout in seconds for each update check
        
        Returns:
            Trade: Completed trade object
        """
        while not trade.isDone():
            self.ib.waitOnUpdate(timeout=timeout)
        return trade
    
    def get_open_orders(self) -> list:
        """
        Get all open orders.
        
        Returns:
            list: List of open trades
        """
        return self.ib.openTrades()
    
    def cancel_order(self, trade: Trade) -> None:
        """
        Cancel an open order.
        
        Args:
            trade: Trade object to cancel
        """
        self.ib.cancelOrder(trade.order)
        print(f"Cancelled order for {trade.contract.symbol}")
