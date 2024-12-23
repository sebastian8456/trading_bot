# main.py - runs the main program
from TradingBot import TradingBot

if __name__ == '__main__':
    # Run the trading bot
    try:
        trading_bot = TradingBot(paper=False)
        trading_bot.write_to_log(info='running...')
        # trading_bot.trade()
        trading_bot.run()
    except Exception as error:
        trading_bot.write_to_log(error)
