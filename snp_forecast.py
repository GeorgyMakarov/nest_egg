#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import numpy as np
import pandas as pd

from strategy import strategy
from events   import signal_event


class snp_daily_forecast(strategy):
  def __init__(self, events, handler):
    self.events  = events
    self.handler = handler
    self.tickers = self.handler.tickers
    self.start   = self.handler.start

    self.bought = {}
    self._calc_init_bought()
    
    self.historic_data = self._load_historic_data()
    self.train_data = self._create_training_data()
    self.model = self._train_new_model()
  
  def _calc_init_bought(self):
    for s in self.tickers:
      self.bought[s] = 'out'

  def _create_training_data(self):
    
    pass


  def _train_new_model(self):
    """
    """
    pass
