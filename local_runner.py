# Branch: local_runner
# Use for live trading

import datetime
from handlers  import csv_handler
from portfolio import portfolio
from execution import daily_handler
from mac       import mac
from live_trd  import live_trd
from loader    import get_yf_tickers

TICKERS  = ['KMB']

# This is the path to the folder where you store your updated CSV files.
FOLDER   = './trading_data/'

# Here the start date must be fixed on the day of investment. Do not move it as
# moving will distort the quantity due to accumulated equity difference.
START    = datetime.datetime(2024, 1, 2, 0, 0)
INIT_CAP = 10000

# This load date can be pretty close to the day of investment until very long
# moving average is used to produce the signal.
START_LOAD = '2022-01-01'

get_yf_tickers(TICKERS, FOLDER, START_LOAD, gog=False)
print()

if __name__ == '__main__':
  live_trd = live_trd(TICKERS, FOLDER, START, INIT_CAP, csv_handler, daily_handler, portfolio, mac)
  live_trd.run_simulation()