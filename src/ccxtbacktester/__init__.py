import tqdm
import numpy as np

class historicExchange:
    
    run = 1
    finished = False
    
    orders = []
    trades = []
    specs = None
    plot_trades = []
    plot_orders = []
    total_trades = 0

    
    def __init__(self, ohlcv: list, base: str="MKR", quote: str="USDT", start_amount: int=1000, log=print, *args, **kwargs) -> None:
        '''
        To Backtest simply set this class as your exchange and pass it a ohlcv list from ccxt.exchange.ohlcv
        Call the `next` function on the exchange to progress for one candle/period/...
        Once all ohlcv items are given back the finished Param is set to  True and the Exchange will print(in future maybe also plot) the benchmark.
        Be careful! At the moment the Exchange does not feature numerous elements of a normal Exchange. ( if you're Missing a function, just at it yourself, the class's structure is quite simple. I'd appreciate it if you'd commit your changes so other can also use it)
        Shorting isn't supported.

        Parameters
        ----------
        ohlcv : list
            the data to perform the backtest on
        '''
        self.ohlcv = ohlcv
        self.rounds = len(ohlcv)
        self.base = base
        self.quote = quote
        self.log = log
        self.start_amount = start_amount
        self.reset()
    
    def fetch_ohlcv(self, *args, **kwargs):
        return self.ohlcv[:self.run]
    
    def next(self):
        add_order = False
        self.run += 1

        
        if len(self.trades) > self.total_trades:
            self.total_trades = len(self.trades)
            self.plot_trades.append(self.ohlcv[self.run-2][4])
        else:
            self.plot_trades.append(0)
        
        self.plot_balance.append(self.balance["free"][self.base])
        self.plot_money.append(self.balance["free"][self.quote])
        
        for index, x in enumerate(self.orders):
            if x["side"] == "sell" and x["stop"] >= self.ohlcv[self.run - 1][4]:
                if not add_order:
                    add_order = True
                    self.plot_orders.append(self.ohlcv[self.run - 1][4])
                counter = 1
                self.balance["free"][self.quote] += x["amount"] * self.ohlcv[self.run-1][4]
                self.balance["free"][self.base] -= x["amount"]
                while x["amount"] > 0.00001:
                    try:
                        if self.trades[-counter]["filled"]: continue
                        self.trades[-counter]["closed_at"] = self.ohlcv[self.run-1][4]
                        x["amount"] -= self.trades[-counter]["amount"]
                        self.trades[-counter]["filled"] = True
                        counter += 1
                    except IndexError:
                        raise SyntaxError("Tried to close nonexistent position")
                self.orders.pop(index)
            else:
                pass
        
        if not add_order:
            self.plot_orders.append(0)
        
        success = []
        tot_profit = []
        tot_loss = []
        
        if self.run == self.rounds:
            self.finished = True
            for index, x in enumerate(self.trades):
                self.trades[index]["profit"] = (x["closed_at"] - x["price"]) if x["side"] == "buy" else (x["price"] - x["closed_at"])
                success.append(1 if self.trades[index]["profit"] > 0 else 0)
                if self.trades[index]["profit"] > 0:
                    tot_profit.append(self.trades[index]["profit"])
                else:
                    tot_loss.append(self.trades[index]["profit"])
            self.specs = {
                "success" : 0 if len(success) == 0 else sum(success)/len(success),
                "tries" : len(self.trades),
                "profit" : self.balance['free'][self.quote] - self.start_amount,
                "length" : self.rounds,
                "loss_per_trader" : 0 if len(tot_loss) == 0 else sum(tot_loss)/len(tot_loss),
                "profit_per_trade" : 0 if len(tot_profit) == 0 else sum(tot_profit)/len(tot_profit),
                }
            self.log(f"Success rate: {0 if len(success) == 0 else sum(success)/len(success)} with {len(self.trades)} tries")
            self.log(f"Total profit over {self.rounds} periods: {self.balance['free'][self.quote] - self.start_amount}")
            self.log(f'Win and loss per trade (mean): {self.specs["profit_per_trade"]} : {self.specs["loss_per_trade"]}')
            
            import matplotlib.pyplot as plt
            close = [x[4] for x in self.ohlcv]
            x_axis = np.array(list(range(self.rounds)))
            
            buy = np.array(self.plot_trades)
            buy[buy == 0] = np.nan
            
            sell = np.array(self.plot_orders)
            sell[sell == 0] = np.nan
            
            plt.subplot(2, 2, 1)
            plt.title("Trades")
            plt.plot(close)
            plt.ylabel('Close Values')
            plt.scatter(x=x_axis, y=buy, marker="^", c="green")
            plt.scatter(x=x_axis, y=sell, c="red")
            
            plt.subplot(2, 2, 3)
            plt.title("Money")
            plt.plot(self.plot_money)
            
            plt.subplot(2, 2, 4)
            plt.title("Assets")
            plt.plot(self.plot_balance)
            
            plt.show()
        else: pass
        
        # Set Progress Bar
        next(self.progress)
    
    def fetch_balance(self, *args, **kwargs):
        '''
        Returns Balance

        Returns
        -------
        dict
            {"free":{...}}
        '''
        return self.balance
    
    def create_order(self, symbol: str, type: any, side: any, amount: any, price: any=None, params: any={}):
        '''
        Same Params as ccxt
        '''
        stop_loss = None
        in_base = amount * self.ohlcv[self.run-1][4]
        for x in params:
            if "stop" in x or "limit" in x or "trigger" in x or "price" in x:
                stop_loss = params[x]
        if type == "market":
            if in_base > self.balance["free"][self.quote]:
                raise SyntaxError("Not enough base currency")
            else:
                self.balance["free"][self.quote] += in_base if side == "sell" else in_base * -1
                self.balance["free"][self.base] += amount if side == "buy" else amount * -1 # TODO Add Positions
                self.trades.append({
                    "side" : side,
                    "price" : self.ohlcv[self.run-1][4],
                    "amount" : amount,
                    "filled" : False,
                    "profit" : 0,
                    "closed_at" : None,
                })
        else:
            if bool(price and price in self.ohlcv[self.run-1]) or amount > self.balance["free"][self.base]:
                raise SyntaxError(f"Tried to open Stop_limit at current price or tried to close non existent (too small) position")
            else:
                self.orders.append({
                    "side" : side,
                    "amount" : amount,
                    "stop" : stop_loss if stop_loss else price}
                )
    
    def cancel_all_orders(self, *args, **kwargs):
        self.orders = []
    
    def reset(self):
        '''
        Resets internall counters and `finished` var for new Benchmark
        '''
        self.run = 1
        self.finished = 0
        self.specs = None
        self.balance = {
            "free" : {
                self.quote : self.start_amount,
                self.base : 0,
            }
        }
        self.progress = iter(tqdm.tqdm(range(self.rounds-2), miniters=1))
        self.plot_money = [self.start_amount]
        self.plot_balance = [0]