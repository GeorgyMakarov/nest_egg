from datetime import datetime
import yfinance as yf
import numpy as np

start_date = datetime(2002, 1, 1)
end_date   = datetime(2023, 7, 27)
sp500 = yf.download('^GSPC', start=start_date, end=end_date)
sp500.to_csv('sp500_daily_history_2002_2023.csv')

# Ishares SP500 InformationTechnology Sector
# IUIT.L
start_date = datetime(2017, 1, 1) ## started in 2016-06, but use 2017-1-1 here
end_date   = datetime(2023, 7, 27) ## always one day before current
iuit = yf.download('IUIT.L', start=start_date, end=end_date)
iuit.to_csv('ishares_sp500_it_etf_history_2017_2023.csv')
