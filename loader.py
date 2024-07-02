import re
from datetime import datetime
import yfinance as yf
import numpy as np
# from google.colab import files


def get_yf_tickers(tickers, folder, start, end=None, gog=True):
  """
  Collects and saves to csv daily trading data from Yahoo Finance.

  Params:
    tickers (list): The list of tickers to load.
    folder (string): The path to where to save the loaded data.
    start (string): The start date for data load, format YYYY-MM-DD.
    end (string): The end date for data load, format YYYY-MM-DD.
    gog (binary): If true use google download to download file, else use csv.
  """
  res = {}
  start_date = datetime.strptime(start, '%Y-%m-%d')

  if end is None:
    end = datetime.now()
  else:
    end = datetime.strptime(end, '%Y-%m-%d')
    
  for t in tickers:
    ticker = yf.download(t, start=start, end=end)
    ticker.columns = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
    res[t] = ticker
  
  for t in res:
    data = res[t]
    data.index.name = None
    file_name = re.sub('\.', '_', t.upper()) + '.csv'
    data.to_csv(folder + file_name)
    if gog == True:
      files.download(file_name)