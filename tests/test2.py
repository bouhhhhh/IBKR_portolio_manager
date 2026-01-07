from ib_insync import *
import datetime

# Parameters
HOST = '127.0.0.1'
PORT = 4002       # 4002 = paper trading, 4001 = live
CLIENT_ID = 1

ib = IB()
ib.connect(HOST, PORT, clientId=CLIENT_ID)

from ib_insync import Stock, MarketOrder

def place_buy_async(ib: IB, symbol: str, qty: float = 1.0,
                    currency: str = "USD", exchange: str = "SMART",
                    dry_run: bool = False) -> Trade:
    """
    Place a market BUY order (supports fractional qty) and attach async hooks.
    Keep ib.waitOnUpdate() running in your main loop so events flow.
    Set dry_run=True to simulate (what-if) and print any warnings before sending.
    """
    contract = Stock(symbol, exchange, currency)
    order = MarketOrder("BUY", qty)

    # Optional: simulate first to catch fractional rejections in advance
    if dry_run:
        whatif = ib.whatIfOrder(contract, order)
        if whatif and (whatif.warnings or whatif.status):
            print("[WHAT-IF]", whatif.status, whatif.warnings)
        # Continue to place the real order after preview. Comment next line if you want preview-only.

    trade = ib.placeOrder(contract, order)

    def on_status(tr: Trade):
        print(f"[STATUS] {symbol} {tr.orderStatus.status}  filled={tr.filled}  remaining={tr.remaining}")
        if tr.isDone():
            print(f"[DONE]   {symbol} {tr.orderStatus.status}  "
                  f"filled={tr.filled}  avgPx={tr.orderStatus.avgFillPrice or 0.0}")
            # detach
            tr.statusEvent -= on_status
            tr.fillEvent   -= on_fill
            tr.filledEvent -= on_filled

    def on_fill(tr: Trade, fill: Fill):
        ex = fill.execution
        print(f"[FILL]   {symbol} {ex.shares} @ {ex.price} on {ex.exchange}  time={ex.time}")

    def on_filled(tr: Trade):
        # fires once when fully filled
        print(f"[FILLED] {symbol} totalFilled={tr.filled} avgPx={tr.orderStatus.avgFillPrice or 0.0}")

    trade.statusEvent += on_status
    trade.fillEvent   += on_fill
    trade.filledEvent += on_filled

    print(f"Submitted BUY: {qty} x {symbol}")
    return trade

trade = place_buy_async(ib, "QQQ", 10)   # fractional quantity

# Event loop: DO NOT use time.sleep() here
while not trade.isDone():
    ib.waitOnUpdate(timeout=1.0)
