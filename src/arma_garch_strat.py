import numpy as np
import polars as pl
from datetime import date
from datetime import timedelta
from statsmodels.tsa.arima.model import ARIMA
from arch import arch_model
from statsmodels.stats.diagnostic import acorr_ljungbox
import pickle
import re
import os


class ArmaGarchStrategy:
  def __init__(self, budget, increment, commission, logger):
    self.budget = budget
    self.increment = increment
    self.commission = commission
    self.logger = logger
    self.model_folder = './arma_garch_models/'
    self.effective_date = None

  def _check_edate(self, dt:pl.DataFrame, ha: pl.DataFrame, ticker: str):
    """
    Last predicted date by the model is one day before the effective date
    meaning that the last known date downloaded from the SQL DB must be
    the same as the effective date otherwise the prediction will be broken.
    """
    first_sql = dt.clone().select(pl.col("date")).to_numpy().flatten()
    effective_date = ha.clone().filter(pl.col('ticker') == ticker)['date_effect'].to_numpy().item()
    self.effective_date = effective_date
    if effective_date not in first_sql:
      self.logger.error(f"Check first available date from SQL for {ticker}")
      res = False
    else:
      last_sql = dt.clone().select(pl.col("date").max()).item()
      self.logger.info(f"Ticker {ticker}: last SQL date = {last_sql}")
      res = True
    return res
  
  def _garch_model_fc(self, train_resid, mu_hat):
    """
    Fits garch model and produces forecast
    """
    gm = arch_model(train_resid, 
                    vol='Garch', 
                    p=1, 
                    q=1, 
                    rescale=False, 
                    mean='Constant', 
                    dist='Normal').fit(update_freq=0, disp="off")
    gm_fore = gm.forecast(horizon=1)
    sigma2_hat = gm_fore.variance.iloc[-1]
    sigma_hat = np.sqrt(sigma2_hat).item()
    e_hat = 1
    epsilon_hat = e_hat * sigma_hat
    epsilon_hat = -1 * epsilon_hat if mu_hat < 0 else epsilon_hat
    return epsilon_hat

  
  def _forecast(self, test_returns, ticker, am):
    """
    Forecasts all the way until today and from the effective date of the
    model to cover for all days and match the predictions. Always consider that
    the last day is today's price, because the checks for data integrity happen
    before that in 'trading.db'

    :param test_returns: a numpy array of log returns to run the test on
    :param ticker: str, ticker name
    :param am: ARIMA model object
    """
    forecasts = []
    train_resid = am.resid
    for i in test_returns:
      mu_hat = am.forecast(steps=1)
      am = am.append([i], refit=False)
      p_value = acorr_ljungbox(am.resid ** 2, 
                               lags=[20], 
                               return_df=True)['lb_pvalue'].item()
      self.logger.info(f"Ticker {ticker}, p-value = {p_value:.2f}")
      if p_value < 0.05:
        epsilon_hat = self._garch_model_fc(train_resid, mu_hat)        
        y_hat = mu_hat + epsilon_hat
      else:
        y_hat = mu_hat
      epsilon_actual = i - mu_hat
      forecasts.append(y_hat.item())
      train_resid = np.append(train_resid, epsilon_actual)
    ## --- Next day forecast using the latest updates --- ##
    mu_hat = am.forecast(steps=1)
    am = am.append(mu_hat, refit=False)
    pv = acorr_ljungbox(am.resid**2, lags=[20], return_df=True)['lb_pvalue'].item()
    if pv < 0.05:
      epsilon_hat = self._garch_model_fc(train_resid, mu_hat)
      y_hat = mu_hat + epsilon_hat
    else:
      y_hat = mu_hat
    return y_hat  
  
  def run(self, dt: pl.DataFrame, ha: pl.DataFrame, ticker: str):
    """
    Forecast returns using ARMA-Model
    :param dt: daily price data frame
    :param ha: has arma data frame
    """
    edates_check = self._check_edate(dt, ha, ticker)
    signal = 'hold'
    if edates_check:
      path_to_model = self.model_folder + ha['file_name'].item()
      with open(path_to_model, 'rb') as f:
        model = pickle.load(f)
      test_prices = dt['price'].to_numpy()
      test_ret = np.diff(np.log(test_prices))
      test_dates = dt['date'].to_numpy()[1:]
      test_ret_df = pl.DataFrame({'date': test_dates, 'ret': test_ret})
      # Filter the test data frame enabling it to start from the first date
      # following the date of training end to have the right sequence of forecasts.
      test_ret_df = test_ret_df.filter(pl.col('date') > self.effective_date)
      test_returns = test_ret_df['ret'].to_numpy()
      self.logger.info(f"Forecasting next day returns for {ticker}...")
      next_day_ret = self._forecast(test_returns, ticker, model)
      if next_day_ret >= 0:
        signal = 'buy'
      else:
        signal = 'sell'
    return signal
    



