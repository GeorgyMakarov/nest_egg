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
    self.z_low = z_low
    self.z_high = z_high
    self.pair = ('CSPX_L', 'CSUSS_SW')
  
  def calculate_signal(self, event):
    pass
