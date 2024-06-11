#!/usr/bin/python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

def plot_equity(holdings):
  hold_df = pd.DataFrame(holdings)
  hold_df.drop_duplicates(inplace=True)
  hold_df.set_index('datetime', inplace=True)
  hold_df['returns'] = hold_df['total'].pct_change()
  hold_df.fillna(0, inplace=True)
  hold_df['equity_curve'] = (1.0 + hold_df['returns']).cumprod()

  sharpe_ratio = compute_sharpe_ratio(hold_df['returns'])
  drawdown, max_dd, dd_duration = compute_drawdowns(hold_df['returns'])
  total_return = hold_df['equity_curve'][-1]
  npv = compute_npv(hold_df)

  s1 = hold_df['equity_curve']
  s2 = hold_df['cash']
  dates = s1.index
  fig, ax = plt.subplots()
  ax.plot(dates, s1, color='green', label='strategy')
  ax.set(xlabel='Date', ylabel='Equity', title='Equity curve')
  plt.xticks(rotation=90)
  plt.legend()
  plt.tight_layout()
  plt.show()

  print()

  fig, ax = plt.subplots()
  ax.plot(dates, s2, color='darkgrey', label='cash')
  ax.set(xlabel='Date', ylabel='Cash', title='Cash')
  plt.xticks(rotation=90)
  plt.legend()
  plt.tight_layout()
  plt.show()

  print(f"Total return = {(total_return - 1)*100:.2f}%")
  print(f"Sharpe ratio = {sharpe_ratio:.3f}")
  print(f"Max drawdown = {max_dd*100:.2f}%")
  print(f"Drawdown duration = {dd_duration}")
  print(f"NPV = {npv:.2f}")

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

def compute_npv(holdings):
  daily_rate = 0.25*0.01 / 365
  periods = holdings.shape[0]
  discount_factor = (1 + daily_rate) ** periods
  return (holdings['total'][-1] - holdings['total'][0]) / discount_factor