# main.py - runs the main program
# paper.py loads the paper version
from TradingBot import TradingBot
import time

if __name__ == '__main__':
    # Run the trading bot
    while True:
        try:
            trading_bot = TradingBot(paper=True)
            trading_bot.run()
        except Exception as error:
            trading_bot.write_to_log(error)
            time.sleep(60)
