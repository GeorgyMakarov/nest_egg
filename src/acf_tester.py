import numpy as np
from statsmodels.stats.stattools  import durbin_watson
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools    import acf
from src.batch_df_to_sql import batch_df_to_sql


class AutoCorrelationTester:
  def __init__(self, series: np.ndarray, logger):
    self.logger = logger
    if not isinstance(series, np.ndarray):
      self.logger.error("Input must be a NumPy array.")
      raise TypeError("Input must be a NumPy array.")
    if series.ndim != 1:
      self.logger.error("Input must be a 1D NumPy array.")
      raise ValueError("Input must be a 1D NumPy array.")    
    self.series = series
    
  def compute_acf(self, nlags: int = 20) -> np.ndarray:
    """Compute autocorrelation coefficients up to nlags."""
    acor = acf(self.series, nlags=nlags, fft=True)
    threshold = 1.96 / np.sqrt(len(self.series))
    first_four = np.abs(acor[1:5]) ## except 0 because it is always 1.0
    others = np.abs(acor[5:])
    if any(first_four > threshold):
      lag_value = max(np.where(first_four > threshold)[0]).item()
    elif any(others > threshold):
      # Here the algorithm is similar to decision when you look at an ACF plot
      # with your eyes trying to note significant spikes, but 1 out of 20 lags
      # is allowed to be above a threshold by chance.
      spikes = np.where(others > threshold)[0]
      if len(spikes) == 1:
        lag_value = 0
      else:
        lag_value = max(spikes).item()
    else:
      lag_value = 0
    return lag_value
    
  def durbin_watson_test(self) -> float:
    """Compute the Durbin-Watson statistic (≈ 2 means no autocorrelation)."""
    return durbin_watson(self.series)
    
  def ljung_box_test(self, lags: int = 20) -> dict:
    """
    Perform the Ljung-Box test.
    Returns a dictionary with p-values for each lag.
    """
    lb_test = acorr_ljungbox(self.series, lags=[lags], return_df=True)
    return lb_test.to_dict("list")
    
  def summary(self, nlags: int = 20, ticker: str = None):
    """Prints a summary of autocorrelation tests."""
    ac_res = self.compute_acf()
    db_res = self.durbin_watson_test()
    lj_box = self.ljung_box_test()
    ljp = lj_box['lb_pvalue'][0]
    self.logger.info(
      f"Tic. {ticker}: DB = {db_res:.2f}, ACF = {ac_res}, LB p-val = {ljp:.2f}"
    )
    res = {'ticker': ticker, 'acf': ac_res, 'darb_wat': db_res, 
           'l_box': lj_box['lb_stat'][0], 'lb_pval': lj_box['lb_pvalue'][0]}
    return res
  
  def write_table(self, dt, args, con_str):
    """Writes table to SQL."""
    if args.test == 'y':
      self.logger.warning("Test mode, terminating without writing to SQL...")
    else:
      self.logger.info("Writing test results to SQL...")
      batch_df_to_sql(con_str, 'acf_test', dt, 1000, self.logger)
