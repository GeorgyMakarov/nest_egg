#!/usr/bin/python
# -*-coding:utf-8-*
# write_daily_prices_to_sql.py

import sys
from datetime import datetime
import yfinance as yf
import numpy as np
import pandas as pd

def get_yahoo_finance_data(ticker, start_date):
  """
  Downloads Yahoo Finance data from start_date to today.
  Adds price_date column and created_date = today. Assigns vendor 1.

  Param:
    ticker (string): ticker in capital letters
    start_date (string): format 'YYYY-MM-DD', example: '2019-01-01'
  Returns:
    data frame
  """
  # Use different conversions if start date contains hours and minutes:
  if len(start_date) > 10:
    start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    start_date = start_date.strftime("%Y-%m-%d")
  else:
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
  end_date   = pd.Timestamp.today().strftime('%Y-%m-%d')
  data = yf.download(ticker, start=start_date, end=end_date)
  data.columns = ['open_price', 'high_price', 'low_price', 
                  'close_price', 'adj_close_price', 'volume']
  data.reset_index(inplace=True)
  data.rename({'Date': 'price_date'}, axis=1, inplace=True)
  data['created_date'] = end_date
  data['data_vendor_id'] = 1 ## because Yahoo Finance is 1 and this is for YF only
  data['id'] = 0
  return data

def convert_yf_data(df, symbol_id):
  """
  Converts Yahoo data into the format appropriate for the master storage database.
  """
  df['symbol_id'] = symbol_id
  df = df[['id', 'data_vendor_id', 'symbol_id', 'price_date', 'created_date', 
           'open_price', 'high_price', 'low_price', 'close_price', 
           'adj_close_price', 'volume']]
  return df