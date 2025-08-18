import polars as pl
from src.batch_query_to_df import batch_query_to_df
from src.setup_logger import setup_log
from datetime import datetime
from datetime import timedelta

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
  
  def get_arma_tickers(self, args):
    """
    Gets the list of tickers that have ARMA-GARCH models for the chosen sector.
    """
    cat = args.cat
    query = f"SELECT ticker, date_effect, file_name, p_used, q_used FROM (SELECT ticker, date_effect, p_used, q_used, file_name, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date_effect DESC) AS rn FROM arma_models WHERE sector = '{cat}') WHERE rn = 1;"
    sch_over = {'ticker': pl.Utf8, 'date_effect': pl.Utf8, 'file_name': pl.Utf8}
    dt = batch_query_to_df(self.db, query, sch_over, 100, self.f_log)
    return dt
  
  def get_arma_test_data(self, id, ticker, dt):
    """
    Get maximum period that needs to be loaded to be able to run the model.
    The data should start on the date preceding the effective date of the model,
    because the model's train + test set ended just the day prior to the effect
    date, but we also need to account for log returns computation. So the first 
    prediction of the model must be the effect date.
    """
    de_i = dt.clone().filter(pl.col('ticker') == ticker)['date_effect'].to_numpy().item()
    de_date = datetime.strptime(de_i, "%Y-%m-%d").date()
    lookup_date = de_date - timedelta(days=3) ## use 3 to account for Sat-Sun
    lookup_date = lookup_date.strftime("%Y-%m-%d")
    query = f"SELECT price_date AS [date], close_price AS price FROM daily_price WHERE symbol_id = {id} AND price_date >= '{lookup_date}' GROUP BY price_date ORDER BY price_date;"
    sch_over = {'date': pl.Utf8, 'price': pl.Float64}
    res = batch_query_to_df(self.db, query, sch_over, 1000, self.f_log)
    self.f_log.info(res)
    return res