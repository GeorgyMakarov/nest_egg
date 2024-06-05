#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import numpy as np
import pandas as pd

from strategy import strategy
from events   import signal_event

import statsmodels.api as sm

class mean_reverting(strategy):
  def __init__(self, events, handler, ols_w=100, z_low=0.5, z_high=3.0):
    self.events  = events
    self.handler = handler
    self.tickers = self.handler.tickers
    self.ols_w = ols_w
    self.z_low  = z_low
    self.z_high = z_high
    self.pair   = ('CSPX_L', 'CSUSS_SW')
    self.long_market  = False
    self.short_market = False
    self.hedge_ratio  = None
  
  def calculate_xy_signals(self, z_last, y, x):
    y_signal = None
    x_signal = None
    p0 = self.pair[0]
    p1 = self.pair[1]
    hr = abs(self.hedge_ratio)
    dt = self.handler.current_date

    if z_last <= -self.z_high and not self.long_market:
      self.long_market = True
      y_signal = signal_event(p0, dt, 'long',  1.0, y[-1])
      x_signal = signal_event(p1, dt, 'short', hr,  x[-1])
    if abs(z_last) <= self.z_low and self.long_market:
      self.long_market = False
      y_signal = signal_event(p0, dt, 'exit', 1.0, y[-1])
      x_signal = signal_event(p1, dt, 'exit', 1.0, x[-1])
    if z_last >= self.z_high and not self.short_market:
      self.short_market = True
      y_signal = signal_event(p0, dt, 'short', 1.0, y[-1])
      x_signal = signal_event(p1, dt, 'long',  hr, x[-1])
    if abs(z_last) <= self.z_low and self.short_market:
      self.short_market = False
      y_signal = signal_event(p0, dt, 'exit', 1.0, y[-1])
      x_signal = signal_event(p1, dt, 'exit', hr, x[-1])
    return y_signal, x_signal

  def calculate_signals_for_pairs(self):
    y = self.handler.get_latest_bars_values(self.pair[0], 'close', self.ols_w)
    x = self.handler.get_latest_bars_values(self.pair[1], 'close', self.ols_w)
    if y is not None and x is not None:
      if len(y) >= self.ols_w and len(x) >= self.ols_w:
        self.hedge_ratio = sm.OLS(y, x).fit().params[0]
        spread = y - self.hedge_ratio * x
        z_last = ( (spread - spread.mean())/spread.std() )[-1]
        y_signal, x_signal = self.calculate_xy_signals(z_last, y, x)
        if y_signal is not None and x_signal is not None:
          print(f"Date: {x_signal.dt}, px = {x_signal.price:.2f}, sx = {x_signal.sig_type}, powx = {x_signal.sig_str:.3f}")
          print(f"Date: {y_signal.dt}, py = {y_signal.price:.2f}, sy = {y_signal.sig_type}, powy = {y_signal.sig_str:.3f}")
          self.events.put(y_signal)
          self.events.put(x_signal)

  def calculate_signal(self, event):
    if event.type == 'market':
      self.calculate_signals_for_pairs()
