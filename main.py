# main.py - runs the main program
# paper.py loads the paper version
from TradingBot import TradingBot

if __name__ == '__main__':
    trading_bot = TradingBot(paper=True)
    trading_bot.run()
