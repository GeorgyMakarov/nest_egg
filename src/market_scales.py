import polars as pl
import numpy as np
from datetime import datetime
from src.batch_df_to_sql import batch_df_to_sql

class MarketScales:
  def __init__(self, meat, args, benchmarks, logger):
    self.data = meat
    self.ma   = args.ma
    self.cat  = args.cat 
    self.bm   = benchmarks
    self.test = args.test
    self.logger = logger

  def run(self, con_str):
    df = pl.DataFrame(self.data)
    df = df.filter(pl.col('sharpe') > 0)
    df = df.with_columns(pl.lit(self.bm['total_ret_pct']).alias('benchmark_pct'))
    df = df.filter((pl.col('total_ret_pct') > pl.col('benchmark_pct')) | (pl.col('sharpe') >= 1))
    df = df.sort('sharpe', descending=True)
    df = df.with_columns([
      pl.lit(self.cat).alias('category'),
      pl.lit(datetime.now()).alias('run_id')
    ])
    df = df.with_columns(pl.col("run_id").dt.truncate("1s").alias("run_id"))
    df = df.with_columns(pl.lit(self.ma).alias('ma'))
    if self.test == 'n':
      batch_df_to_sql(con_str, 'buy_hold', df, 1000, self.logger)
    

    