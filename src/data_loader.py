import polars as pl
from src.batch_query_to_df import batch_query_to_df
from src.setup_logger import setup_log

class DataLoader:
  def __init__(self, db, logger):
    self.db    = db
    self.log   = logger
    self.count = 50
    self.bs = 1000
    self.f_log = setup_log("batch_query_to_df()")

  def get_tickers(self, args_vals):
    if hasattr(args_vals, 'test'):
      self.count = 3 if args_vals.test == 'y' else self.count
      self.bs = 100 if args_vals.test == 'y' else self.bs      
      self.log.info(f"Running in test mode, loading {self.count} tickers...")
      self.log.info(f"Defaulting to batch size: {self.bs}")
    if hasattr(args_vals, 'cat'):
      self.cat = args_vals.cat
      self.log.info(f"Collecting tickers for '{self.cat}' category...")
      if self.count == 3:
        query = f"SELECT id, ticker FROM symbol WHERE sector = '{self.cat.lower()}' GROUP BY id, ticker LIMIT {self.count};"
      else:
        query = f"SELECT id, ticker FROM symbol WHERE sector = '{self.cat.lower()}' GROUP BY id, ticker;"
      sch_over = {'id': pl.Int64, 'ticker': pl.Utf8}
      tickers = batch_query_to_df(self.db, query, sch_over, self.bs, self.f_log)
      return tickers
  
  def get_history(self, id):
    query = f"SELECT price_date AS [date], close_price AS price FROM daily_price WHERE symbol_id = {id} GROUP BY price_date ORDER BY price_date;"
    sch_over = {'date': pl.Utf8, 'price': pl.Float64}
    history = batch_query_to_df(self.db, query, sch_over, self.bs, self.f_log)
    return history
  
  def get_ttm(self, id, after):
    """
    Get history for 12 trailing months.
    """
    query = f"SELECT price_date AS [date], close_price AS price FROM daily_price WHERE symbol_id = {id} AND price_date >= '{after}' GROUP BY price_date ORDER BY price_date;"
    sch_over = {'date': pl.Utf8, 'price': pl.Float64}
    dt = batch_query_to_df(self.db, query, sch_over, 1000, self.f_log)
    return dt