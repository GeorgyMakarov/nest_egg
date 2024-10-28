#!/usr/bin/python
# -*-coding:utf-8-*
# write_daily_prices_to_sql.py

import sys
import sqlite3
import time
import argparse
import numpy as np
import pandas as pd
from sql_query_helper import sql_query
from sql_query_helper import write_table_to_sql
from sql_query_helper import read_sql_to_pd
from yfinance_helper import get_yahoo_finance_data
from yfinance_helper import convert_yf_data

ROOT = 'C:/Users/makar/OneDrive/Documents/project_george/'
CSV_PATH = 'csv_data/ticker_param.xlsx'
DB_PATH  = 'dbms/master_storage/master_storage.db'
F_NM = "write_daily_prices_to_sql(): "

# Helper functions
def get_latest_dates(tickers, db_path):
  """
  """
  ticker_sql = "('" + "', '".join(tickers) + "')"
  query = "SELECT B.ticker as ticker, MAX(A.price_date) as max_date FROM "\
          "daily_price A LEFT JOIN symbol B ON A.symbol_id = B.id WHERE "\
          "B.ticker IN " + ticker_sql + " GROUP BY B.ticker;"
  res = read_sql_to_pd(db_path, query)
  return res

# Provide an argument --sector="<your-sector-name>" to
# update one sector at a time to avoid too many calls to API
# and prevent blocking. Example: --sector="consumer defensive"
# Use Finance Yahoo sector names.

if __name__ == '__main__':
  print(f"{F_NM}Collecting arguments ...")
  parser = argparse.ArgumentParser()
  parser.add_argument("--sector")
  args = parser.parse_args()
  config = vars(args)
  if config['sector'] is None:
    print(f"{F_NM}Error: provide sector!")
    print(f"{F_NM}Execution terminated!")
    sys.exit(1)
  # Check if tickers belonging to the sector exist in symbol table
  ins = config['sector'].lower()
  q = "select id, ticker from symbol where lower(sector) = '" + ins +\
      "' group by id, ticker;"
  ticker_df = read_sql_to_pd(ROOT+DB_PATH, q)
  tickers = ticker_df['ticker'].tolist()
  len_t = len(tickers)
  
  if len_t == 0:
    print(f"{F_NM}Error: no tickers for {ins} in the data base!")
    print(f"{F_NM}Execution terminated!")
    sys.exit(1)
  
  # For every ticker check the latest date that exists in the database and
  # load the data starting from that date and until today. Run all of them
  # in one call to reduce I/O traffic.
  latest_dates = get_latest_dates(tickers, ROOT+DB_PATH)
  
  # If some tickers are missing from the data frame, use default
  # starting date as a start date for the load
  miss_tickers = [x for x in tickers if x not in latest_dates['ticker'].values]
  missing_df = pd.DataFrame({'ticker': miss_tickers, 'max_date': '2019-01-01'})
  latest_dates = pd.concat([latest_dates, missing_df], ignore_index=True)
  
  # Select max id present in the daily table allowing to continue
  # numeration of rows (primary key)
  q = "select max(id) from daily_price;"
  max_idx = sql_query(ROOT+DB_PATH, q)[0][0]

  new_data = {}
  for i, t in enumerate(tickers):
    print(f"{F_NM}Adding {t}: {i+1} out of {len_t} tickers ...")
    yf_data = get_yahoo_finance_data(
      t, 
      latest_dates.query(f"ticker == '{t}'")['max_date'].values[0])
    time.sleep(5)
    print(f"{F_NM}Converting {yf_data.shape[0]} rows for {t} ... ")
    if yf_data.shape[0] > 0:
      yf_data = convert_yf_data(
        yf_data, ticker_df.query(f"ticker == '{t}'")['id'].values[0])
      new_data[t] = yf_data      
  # Concatenate to one frame and assign new id
  if len(new_data) > 0:
    new_data = pd.concat(new_data.values(), ignore_index=True)
    new_data['id'] = range(max_idx+1, max_idx+1+len(new_data))
    write_table_to_sql(ROOT+DB_PATH, new_data, 'daily_price')





  