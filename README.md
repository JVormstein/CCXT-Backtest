# ccxt-backtest
 Fake Exchange based BAcktesting libary for ccxt in Python
 *At the Moment the library only supports only a few main functions and does not allow shorting.*

## Installation
Just download the repository and run `pip install .` in the directory with `pyproject.toml` file.

## Usage
The Usage is quite simple: Just import the library, set your exchange to `historicExchange` and give it a ohlcv list of another exchange.
Everytime you want to move forward in time just call the `next` function. When there's no more ohlcv data the exchange will calculate some simply metrics and print them.
You can change some optional Parameters when loading the library (like logger, Quote and Base Currency as well your starting Money).
The actual Code structure of the library is quite simple, so you're invited to add you're own functionalities and commit them to the repository.



    import ccxt_backtester as cb
    import ccxt

    # Get OHLCV Data
    data_exchange = ccxt.gate()
    ohlcv = data_exchange.fetch_ohlcv(symbol="BTC/USDT") # You should at least fetch a thousand candles or more

    # Set Backtesting Exchange
    exchange = cb.historicExchange(ohlcv=ohlcv) # See docstring for additional optional Parameters

    # Get old_OHLCV
    old_ohlcv = exchange.fetch_ohlcv(symbol="BTC/USDT")
    exchange.create_order(symbol="BTC/USD", type="market", side="buy", amount=0.0001) # At the Moment the create_order function doesn't give anything back
    exchange.create_order(symbol="BTC/USD", type="stop_limit", sell="sell", amount=0.0001, price=99999, params={"trigger_price" : 99999})

    # Move on to the next candle
    exchange.next()