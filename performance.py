#!/usr/bin/python
# -*- coding: utf-8 -*-

# performance.py

from __future__ import print_function

import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods=252):
  r_std = np.std(returns) + 0.000001 ## to account for zero std
  r_mean = np.mean(returns)
  res = np.sqrt(periods) * r_mean / r_std
  return res

def create_drawdowns(pnl):
  hwm =[0]
  idx = pnl.index
  drawdown = pd.Series(index = idx)
  duration = pd.Series(index = idx)
  for t in range(1, len(idx)):
    hwm.append(max(hwm[t-1], pnl[t]))
    drawdown[t] = (hwm[t] - pnl[t])
    duration[t] = (0 if drawdown[t] == 0 else duration[t-1] + 1)
  return drawdown, drawdown.max(), duration.max()