import numpy as np
import polars as pl

import time
from src.argparser import ArgParser
from src.data_loader import DataLoader
from src.acf_tester import AutoCorrelationTester
from src.setup_logger import setup_log
from src.get_year_ago import get_year_ago

CON  = r"C:\sqlite\\trading.db"


def main():
  args = ArgParser(['cat', 'test'], setup_log('ArgParser')).parse()
  loader = DataLoader(CON, setup_log('DataLoader'))
  tickers = loader.get_tickers(args)
  test_res = []

  for idx, row in tickers.iter_rows():
    year_ago = get_year_ago()
    prices = loader.get_ttm(idx, year_ago)['price'].to_numpy()
    series = np.diff(np.log(prices + 1e-4))
    tester = AutoCorrelationTester(series, setup_log(f"AcfTester-{row}"))
    test_res.append(tester.summary(nlags = 20, ticker = row))
  
  today = time.localtime()
  today = time.strftime("%Y-%m-%d", today)
  dt = pl.DataFrame(test_res)
  dt = dt.with_columns(pl.lit(today).alias('test_date'))
  tester.write_table(dt, args, CON)

if __name__ == '__main__':
  start_time = time.time()
  main()
  end_time = time.time()
  print(f"This program took {end_time - start_time} seconds to run.")