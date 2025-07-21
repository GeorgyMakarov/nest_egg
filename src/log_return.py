import numpy as np
import polars as pl

def compute_log_returns(df: pl.DataFrame):
  """
  Computes log returns of an assets 'a' and a baseline 'b'
  """
  pa = df['price'].to_numpy()    ## asset of interest
  pb = df['baseline'].to_numpy() ## baseline
  ra = np.diff(np.log(pa + 1e-4))
  rb = np.diff(np.log(pb + 1e-4))
  return ra, rb