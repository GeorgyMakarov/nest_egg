#!/usr/bin/python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

def plot_equity(bs, pos_history, signal_history):
  s1 = bs['equity_curve']
  s2 = bs['equity_curve'] * 0.7 # TODO: replace this with baseline
  dates = s1.index
  fig, ax = plt.subplots()
  ax.plot(dates, s1, color='green', label='strategy')
  ax.plot(dates, s2, color='grey', label='base line')
  ax.set(xlabel='Date', ylabel='Equity', title='Strategy vs Baseline')
  plt.xticks(rotation=90)
  plt.legend()
  plt.tight_layout()
  plt.show()

def compute_sharpe_ratio(returns):
  return np.sqrt(252) * (np.mean(returns)) / np.std(returns)

def compute_drawdowns(returns):
  hwm = [0]
  idx = returns.index
  drawdown = pd.Series(index = idx)
  duration = pd.Series(index = idx)
  for t in range(1, len(idx)):
    hwm.append(max(hwm[t - 1], returns[t]))
    drawdown[t] = (hwm[t] - returns[t])
    duration[t] = (0 if drawdown[t] == 0 else duration[t-1] + 1)
  return drawdown, drawdown.max(), duration.max()