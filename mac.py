#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import numpy as np
import pandas as pd

from strategy import strategy
from events   import signal_event

class mac(strategy):
  def __init__(self, events, handler, short_window=100, long_window=400):
    self.events  = events
    self.handler = handler
    self.tickers = self.handler.tickers
    self.short_window = short_window
    self.long_window  = long_window
    self.bought = {}

    self._calc_init_bought()
  
  def _calc_init_bought(self):
    for s in self.tickers:
      self.bought[s] = 'out'
  
  def calculate_signal(self, event):
    if event.type == 'market':
      for ticker in self.tickers:
        bars = self.handler.get_latest_bars_values(ticker, 
                                                   "adj_close", 
                                                   self.long_window)
        if bars is not None:
          short_sma = np.mean(bars[-self.short_window:])
          long_sma  = np.mean(bars[-self.long_window:])
          dt = self.handler.current_date
          sig_dir = ""
          sig_str = 1.0
          price   = bars[-1]
          if short_sma > long_sma and self.bought[ticker] == 'out':
            sig_dir = 'long'
            signal  = signal_event(ticker, dt, sig_dir, sig_str, price)
            self.events.put(signal)
            self.bought[ticker] = 'long'
          elif short_sma < long_sma and self.bought[ticker] == 'long':
            sig_dir = 'exit'
            signal  = signal_event(ticker, dt, sig_dir, sig_str, price)
            self.events.put(signal)
            self.bought[ticker] = 'out'