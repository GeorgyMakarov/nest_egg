import numpy as np
import polars as pl
import sys

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

  def compute_strategy(self, ticker, df, args):
    """
    Computes strategy output for a buy-and-hold strategy, produces today's 
    signal.
    """
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

    for i in range(1, df.height):
      self.budget += self.increment
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
          self.budget -= payment
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
    return df
    
  def evaluate_strategy(self, trades, row):
    sales_price = self.last_price * (1 + self.commission['transaction'])
    sales = np.round(sales_price * self.balance, 2)
    self.budget += sales
    # Compute total return as a relative difference between the final value of
    # portfolio and total investments, where the former is calculated as if sold
    # at the last date of trading, and the latter is a sum of all increments.
    total_return = 100 * (self.budget - self.invested) / self.invested
    # Compute normalized equity curve filtering out zero balance values and using
    # the first value as a normalization constant.
    temp = trades.clone()
    temp = temp.filter(pl.col('balance') > 0)
    self.logger.info(f"Filter {trades.height - temp.height} rows with 0 bs...")
    first_row = temp.select(pl.col(['price', 'balance']).first())
    nor_c = np.round(first_row['price'].item() * first_row['balance'].item(), 2)
    temp = temp.with_columns((pl.col("price") * pl.col("balance") / nor_c).alias("norm_value"))
    temp = temp.with_columns((pl.col('price') * pl.col('balance')).alias('bs_amount'))
    temp = temp.with_columns((pl.col("bs_amount").pct_change()).alias('returns'))
    # Assume an average annual Sharpe ratio based on the excess daily returns
    temp = temp.with_columns((pl.col('returns') - 0.02 / 252).alias('excess_returns'))
    ret_col = ['returns', 'excess_returns']
    temp = temp.with_columns(pl.col(ret_col).fill_null(strategy='zero'))
    ex_ret = temp['excess_returns'].to_numpy()
    # Rule of thumb:
    # Annual Sharpe < 1 -- bad
    # 1 <= Annual Sharpe < 2 -- somewhat acceptable
    # Annual Sharpe >= 2 -- good
    annual_sharpe = np.sqrt(252) * ex_ret.mean() / ex_ret.std()
    # Create drawdowns as the largest peak-to-trough drawdown of the PnL curve
    # as well as the duration of the drawdown.
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
    res = {
      'ticker': row.upper(),
      'total_ret': total_return,
      'sharpe': annual_sharpe,
      'drawback_pct': drawback,
      'duration': duration,
      'transactions': self.transaction_counter,
      'last_buy': self.latest_signal[0],
      'last_signal': self.latest_signal[1]
    }
    return res
    

    
