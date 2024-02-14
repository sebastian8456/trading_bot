# main.py - runs the main program
from TradingBot import TradingBot

if __name__ == '__main__':
    # Run the trading bot
    try:
        trading_bot = TradingBot(paper=True)
        trading_bot.write_to_log(info='running...')
        trading_bot.trade()
    except Exception as error:
        trading_bot.write_to_log(error)
