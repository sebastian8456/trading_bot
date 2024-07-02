# Holds the new trading client class
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import os
import time
import math
import pandas_ta as ta
import yfinance as yf
import datetime as dt

class TradingBot:
    """automatic trading bot"""
    symbols = {"BTC/USD": "Bitcoin", 
               "ETH/USD": "Ethereum",
               "LINK/USD": "Link",
               "USDT/USD": "Tether",
               "USDC/USD": "U.S. Dollar Coin",
               "AVAX/USD": "Avalanche"
               }
    symbol_minimum = {"BTC/USD": .01,
                      "ETH/USD": .01,
                      "LINK/USD": 0.1, 
                      "USDT/USD": 1, 
                      "USDC/USD": 1, 
                      "AVAX/USD": 0.1}
    
    def __init__(self, paper=True):
        """constructor:
            paper(bool) set to true by default
            for live trading, set paper to False"""
        # load environment variables
        load_dotenv('.env')

        # set default variables
        self.ticker = None
        if paper:
            self.is_paper = True
        else:
            self.is_paper = False
        self.get_secrets()
        self.trading = True
        self.set_trading_client()

    def run(self):
        '''Runs the trading bot to trade cryptocurrency automatically'''
        counter = 0
        trades = 0
        # Trading algorithm based on MACD and RSI strategies
        while self.trading:
            date = dt.datetime.now()
            s_time = date.strftime("%H.%M")
            
            # Trade at stock market opening
            if 8.3 <= float(s_time) <= 9.2:
                pass
            else:
                time.sleep(1800) # sleep for 30 minutes
                continue

            self.trade() # Initiate trades

            counter += 1
            time.sleep(3600) # Wait an hour
            # Stop the bot after a year if no stocks have been bought
            if counter >= 365 and trades == 0:
                break

    def trade(self):
        """Buys or Sells stock based on RSI and MACD indicators"""
        for symbol in self.symbols:
                time.time()
                self.get_account_info()
                time.time()
                self.set_ticker(symbol)
                try:
                    price = self.ticker.history(period="1d").iloc[-1]['Close'] # Get the price
                except:
                    self.write_to_log(error=f"{self.symbols[symbol]} ({symbol}) is an invalid stock.")
                    continue
                status = self.analyze_market()
                try:
                    # Buy the stock
                    if status == "BUY":
                        cash = float(self.acct_info.cash)
                        qty = math.floor(((cash/2)/(price*1.03))*100)/100
                        if qty < self.symbol_minimum[symbol]:
                            continue
                        self.order_stock(symbol, quantity=qty, side=OrderSide.BUY)
                    # Sell the stock
                    elif status == "SELL":
                        pos = self.get_position(symbol)
                        if pos == None:
                            continue
                        qty = math.floor(float(pos.qty_available)*100)/100
                        self.order_stock(symbol, quantity=qty, side=OrderSide.SELL)
                    else:
                        continue
                    time.sleep(5) # wait 5 seconds
                except Exception as Error:
                    self.write_to_log(Error, info=f"Failed to {status} {symbol}.")
                    self.trading = False

    def get_secrets(self):
        """Gets the API and secret keys"""
        if self.is_paper is True:
            self.key = os.getenv('alpaca_paper_key')
            self.secret = os.getenv('alpaca_paper_secret')
        elif self.is_paper is False:
            self.key = os.getenv('alpaca_live_key')
            self.secret = os.getenv('alpaca_live_secret')

    def set_trading_client(self):
        '''initializes the Alpaca trading client'''
        if self.is_paper:
            # If paper is set to true
            self.trading_client = TradingClient(
                    api_key=self.key, 
                    secret_key=self.secret,
                    paper=True
                    )
        else:
            # If paper is set to false
            self.trading_client = TradingClient(
                    paper=False,
                    oauth_token=os.getenv("access_token")
                    )
        
    def get_account_info(self):
        """Gets the user's trading account info"""
        self.acct_info = self.trading_client.get_account()
        # validate account
        if self.acct_info.account_blocked == True:
            error = Exception("Trading account is blocked.")
            self.write_to_log(error=error)
            raise error
    
    def get_position(self, symbol):
        """Gets the user's position on the given stock"""
        symbol = symbol.replace("/", "")
        try:
            pos = self.trading_client.get_open_position(symbol)
        except:
            return None
        return pos
    
    def set_ticker(self, symbol=None):
        """Sets the stock ticker"""
        if "/" in symbol:
            symbol = symbol.replace("/", "-")
        self.ticker = yf.Ticker(symbol)

    def get_RSI(self):
        """Gets the relative strength index"""
        hist = self.ticker.history(period="max")
        hist.dropna(inplace=True)
        # Calculate the RSI
        RSI = ta.rsi(hist['Close'], length=14).iloc[-1]

        return RSI # A number 1-100
    
    def get_MACD_status(self):
        """Gets the BUY or SELL status from the moving average convergence divergence"""
        short_period = 12
        long_period = 26
        signal_period = 9
        hist = self.ticker.history("max")
        hist.dropna(inplace=True)
        
        # Short and long period MACD exponential moving averages(EMA)
        MACD_short_EMA = hist['Close'].ewm(span=short_period).mean()
        MACD_long_EMA = hist['Close'].ewm(span=long_period).mean()

        MACD_line = MACD_short_EMA - MACD_long_EMA

        # EMA of the MACD line (Signal line)
        MACD_signal_line = MACD_line.ewm(span=signal_period).mean()
        # Get the most recent MACD values
        try:
            # MACD crossing above the signal line indicates BUY
            if MACD_line.iloc[-1] > MACD_signal_line.iloc[-1]:
                return "BUY"
            # MACD crossing below the signal line indicates SELL
            if MACD_line.iloc[-1] < MACD_signal_line.iloc[-1]:
                return "SELL"
        except IndexError as Error:
            self.write_to_log(error=Error)
            raise Exception(f"Stock {self.ticker.ticker} has no data.")

    def analyze_market(self):
        """Checks whether to BUY or SELL
            Returns one of "BUY", "SELL", or "HOLD" """
        result = "HOLD"
        RSI = self.get_RSI()
        MACD_status = self.get_MACD_status()

        # RSI less than 30 indicates oversold - BUY
        if RSI < 35 and MACD_status == "BUY":
            result = "BUY"
        # RSI greater than 70 indicates overbought - SELL
        elif RSI > 65 and MACD_status == "SELL":
            result = "SELL"
        return result
    
    def order_stock(self, symbol, quantity=.01, side="BUY"):
        """Executes the trade
            Parameters: 
                quantity - quantity of bitcoin to buy/sell
                side - OrderSide.BUY or OrderSide.SELL; set to BUY by default
            Returns the market order
        """
        # set order side
        if side == "BUY":
            side = OrderSide.BUY
        elif side == "SELL":
            side=OrderSide.SELL

        # initialize market order data
        market_order_data = MarketOrderRequest(
                        symbol=symbol,
                        qty=quantity,
                        side=side,
                        time_in_force=TimeInForce.GTC
                        )
        # Place the order
        try:
            market_order = self.trading_client.submit_order(
                        order_data = market_order_data 
                    )
            if side == OrderSide.BUY:
                info = f"Bought {quantity} {self.symbols[symbol]}."
            elif side == OrderSide.SELL:
                info = f"Sold {quantity} {self.symbols[symbol]}."
            self.write_to_log(info=info)
            print(info)
        except Exception as Error:
            self.write_to_log(error=Error)
            raise Exception(f"MarketOrderFailure: Check log for details")
        
        return market_order
    
    def write_to_log(self, error=None, info=None):
        """Logs errors and info into file"""
        time = dt.datetime.now()
        time = time.strftime("(%d/%m/%y %H:%M:%S)")
        if error is not None:
            with open("log.txt", 'a') as log:
                log.write(time + " ERROR: " + str(error) + "\n")
        if info is not None:
            with open("log.txt", 'a') as log:
                log.write(time + " INFO: " + info + "\n")

