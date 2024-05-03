#!user/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import numpy  as np
import pandas as pd
import statsmodels.api as sm

from strategy import strategy
from event import signal_event

class moving_avg_cross_strategy(strategy):
  """
  Moving average crossover strategy with a short-long simple weighted 
  moving average.
  """
  def __init__(self, bars, events, short_w=100, long_w=400):
    self.bars    = bars
    self.symbols = self.bars.symbols
    self.events  = events
    self.short_w = short_w
    self.long_w  = long_w
    self.bought  = self._calculate_initial_bought()

  def _calculate_initial_bought(self):
    bought = {}
    for s in self.symbols:
      bought[s] = 'OUT'
    return bought
  
  def calculate_signals(self, event):
    if event.type == 'market':
      for s in self.symbols:
        bars = self.bars.get_latest_bars_values(s, "adj_close", n_bars=self.long_w)
        bar_date = self.bars.get_latest_bar_datetime(s)
        if bars is not None:
          short_sma = np.mean(bars[-self.short_w:])
          long_sma  = np.mean(bars[-self.long_w:])
          
          symbol = s
          dt = datetime.datetime.now()
          sig_dir = "" ## signal direction

          if short_sma > long_sma and self.bought[s] == 'OUT':
            print("LONG: %s" % bar_date)
            sig_dir = 'long'
            signal = signal_event(1, symbol, dt, sig_dir, 1.0)
            self.events.put(signal)
            self.bought[s] = 'LONG'
          elif short_sma < long_sma and self.bought[s] == 'LONG':
            print("SHORT: %s" % bar_date)
            sig_dir = 'EXIT'
            signal = signal_event(1, symbol, dt, sig_dir, 1.0)
            self.events.put(signal)
            self.bought[s] = 'OUT'