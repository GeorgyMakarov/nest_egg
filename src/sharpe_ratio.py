import numpy as np

def sharpe_ratio(ra: np.array, rb: np.array, n:int) -> float:
  """
  Computes annualized Sharpe ratio using arrays of returns of assets 'a' and 'b'
  $R_a$ and $R_b$ and trading frequency $n$.
  """
  if np.array_equal(ra, rb):
    res = np.array([0.0])
  else:
    res = np.sqrt(n) * np.mean(ra - rb) / np.std(ra - rb) 
  return res