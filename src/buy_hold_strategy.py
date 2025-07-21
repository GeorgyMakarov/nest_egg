import numpy as np
import polars as pl
import sys
from src.sharpe_ratio import sharpe_ratio
from src.log_return import compute_log_returns

class BuyHoldStrategy:
  def __init__(self, budget, increment, commission, logger):
    self.budget = budget
    self.increment = increment
    self.commission = commission
    self.logger = logger
    self.balance = 0
    self.transaction_counter = 0
    self.invested = budget
    self.latest_signal = None
    self.last_price = None
    self.ticker = None

  def compute_strategy(self, ticker, df, args):
    """
    Computes strategy output for a buy-and-hold strategy, produces today's 
    signal.
    """
    self.ticker = ticker.upper()
    self.logger.info(f"Computing strategy for: {ticker.upper()}")
    df = df.with_columns([pl.col('date').str.to_date("%Y-%m-%d").alias('date')])
    df = df.sort('date')
    roll_mean = 200
    if hasattr(args, 'ma'):
      ma = int(args.ma)
      roll_mean = ma if df.height >= 2 * ma else int(df.height * 0.5)
    # Avoid MA greater than the number of observations in a dataframe to prevent
    # computation errors
    half_df   = int(df.height * 0.5)
    roll_mean = half_df if roll_mean >= df.height else roll_mean
    self.logger.info(f"Using: ma = {roll_mean}, obs = {df.height}")
    df = df.with_columns([pl.col('price')
                          .rolling_mean(window_size=roll_mean)
                          .alias('rollmean')])
    self.logger.info(f"Loaded {df.height} rows for {ticker.upper()}")
    df = df.drop_nulls()
    df = df.with_columns([pl.lit(0).alias('balance')])
    self.logger.info(f"Rows after NaN dropped {df.height}")

    balances = np.zeros(df.height)
    self.logger.info(f"Beginning: budget = {self.budget}, invested = {self.invested}")
    for i in range(1, df.height):
      
      self.budget   += self.increment
      self.invested += self.increment
      
      close_price_current = (
        df.filter(pl.col('date') == df['date'][i]).select('price').item()
      )
      ma_current = (
        df.filter(pl.col('date') == df['date'][i]).select('rollmean').item()
      )

      close_price_prev = (
        df.filter(pl.col('date') == df['date'][i-1]).select('price').item()
      )
      ma_prev = (
        df.filter(pl.col('date') == df['date'][i-1]).select('rollmean').item()
      )

      signal = None
      if close_price_prev < ma_prev and close_price_current > ma_current:
        signal = 'buy'
      if signal:
        self.latest_signal = (df['date'][i], signal)
        price_incl_commission = close_price_current * 1.02
        shares_to_buy = int(self.budget / price_incl_commission)
        payment = np.round(price_incl_commission * shares_to_buy, 2)
        if self.budget - payment >= 0:
          self.budget  -= payment
          self.balance += shares_to_buy
          self.transaction_counter += 1
      if self.budget < 0:
        self.logger.error(f"Budget is Negative for {ticker}...")
      # Add new balance figure daily to be able to compute drawdown, equity curve
      # in evaluation phase.
      balances[i] = self.balance
    if len(balances) == df.height:
      df = df.with_columns(pl.Series(name='balance', values=balances))
    else:
      self.logger.error("Len Balances and DF height mismatch...")
      sys.exit(1)
    self.last_price = df.select(pl.col('price').last()).item()
    self.logger.info(f"Closing: budget = {self.budget:.2f}, invested = {self.invested:.2f}")
    return df
    
  def evaluate_strategy(self, trades, row, baseline):
    sales_price = self.last_price * (1 + self.commission['transaction'])
    sales = np.round(sales_price * self.balance, 2)
    self.budget += sales
    # Compute total return as a relative difference between the final value of
    # portfolio and total investments, where the former is calculated as if sold
    # at the last date of trading, and the latter is a sum of all increments.
    total_return = 100 * (self.budget - self.invested) / self.invested
    # Compute annualized Sharpe ratio using the baseline
    baseline = baseline.rename({'price': 'baseline'})
    col   = 'date'
    forma = "%Y-%m-%d"
    baseline = baseline.with_columns(pl.col(col).str.strptime(pl.Date, forma))
    temp = trades.join(baseline, on='date', how='left')
    temp = temp.filter(pl.col('balance') > 0)
    ra, rb = compute_log_returns(temp)
    sharpe = sharpe_ratio(ra, rb, 252).item()
    self.logger.info(f"Ticker {self.ticker} Sharpe ratio = {sharpe:.3f}")
    # Create drawdowns as the largest peak-to-trough drawdown of the PnL curve
    # as well as the duration of the drawdown.
    temp = temp.with_columns((pl.col('price') * pl.col('balance')).alias('bs_amount'))
    temp = temp.with_columns([
      pl.col('bs_amount').cum_max().alias('running_max'),
      (pl.col('bs_amount') - pl.col('bs_amount').cum_max()).alias('drawdown'),
      ((pl.col('bs_amount') / pl.col('bs_amount').cum_max()) - 1).alias('drawdown_pct')
    ])
    temp = temp.with_columns([
      (pl.col("bs_amount") == pl.col("running_max")).alias("is_new_peak")
    ])
    temp = temp.with_columns([
      pl.when(pl.col("is_new_peak"))
      .then(1)
      .otherwise(0)
      .cum_sum()
      .alias("peak_id")
    ])
    duration = (
      temp
      .group_by(pl.col('peak_id'))
      .agg(pl.count())
      .sort(by='count', descending=True)
    )
    duration = duration['count'].max()
    drawback = np.abs(temp['drawdown_pct'].min())
    self.logger.info(f"Ticker {self.ticker}: drawback = {drawback:.2f}, duration = {duration}")
    res = {
      'ticker': self.ticker,
      'total_ret_pct': total_return,
      'sharpe': sharpe,
      'drawback_pct': drawback,
      'duration_days': duration,
      'transactions': self.transaction_counter,
      'last_buy': self.latest_signal[0],
      'last_signal': self.latest_signal[1]
    }
    return res
    

    
