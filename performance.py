#!user/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods=252):
  """
  Creates the Sharpe ratio for a strategy based on the zero benchmark, i.e. no
  risk-free rate information.

  Args:
      returns (pd.series): The pandas series representing daily returns.
      periods (int): Number of periods in a year if daily trading (252).
  """
  return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)

def create_drawdowns(pnl):
  """
  Creates the largest peak-to-trough drawdown of the PnL curve and its duration.

  Args:
      pnl (pd.series): The series representing period returns.
  
  Returns:
      drawdown (decimal): The value of the drawdown.
      duration (int): The length of the drawdown in days.
  """
  # Set up High Water Mark
  hwm = [0]
  idx = pnl.index
  drawdown = pd.Series(index=idx)
  duration = pd.Series(index=idx)
  for t in range(1, len(idx)):
    hwm.append(max(hwm[t-1], pnl[t]))
    drawdown[t] = (hwm[t] - pnl[t])
    duration[t] = (0 if drawdown[t] == 0 else duration[t - 1] + 1)
  return drawdown, drawdown.max(), duration.max()