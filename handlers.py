#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import os
import os.path

import numpy  as np
import pandas as pd

from abc import ABCMeta
from abc import abstractmethod

from events import market_event

class data_handler(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def update_bars(self):
    raise NotImplementedError("Please implement update_bars()")


class csv_handler(data_handler):
  def __init__(self, events, folder, tickers, start):
    self.events  = events
    self.folder  = folder
    self.tickers = tickers
    self.start   = start

    self.history     = {}
    self.latest_data = {}

    self.base_buy_price  = {}
    self.base_sell_price = {}

    self.continue_backtest = True

    self.date_idx     = None
    self.current_date = None

    self._read_csv()
    self._fill_gaps()
    self._create_iterator()

  def _read_csv(self):    
    for s in self.tickers:
      s_file = os.path.join(self.folder, '%s.csv' % s)
      self.history[s] = pd.read_csv(s_file)
      self.history[s].set_index('Unnamed: 0', inplace=True)
      self.history[s].index.name = None
      if self.date_idx is None:
        self.date_idx = self.history[s].index.tolist()
      else:
        self.date_idx.extend(self.history[s].index.tolist())
  
  def _fill_gaps(self):
    date_idx = np.sort(np.unique(self.date_idx))
    new_series = pd.DataFrame(index=date_idx)
    for s in self.tickers:
      new_frame = pd.merge(new_series, 
                           self.history[s], 
                           left_index=True, 
                           right_index=True, 
                           how='left')
      new_frame.ffill(inplace=True)
      new_frame.bfill(inplace=True)
      self.history[s] = new_frame.copy()
      self.history[s]['returns'] = self.history[s]['adj_close'].pct_change()
      self.history[s].fillna(value=0.0, inplace=True)
      self.history[s]['returns'] = np.where(self.history[s]['returns'] == 0, 
                                            0.00001, 
                                            self.history[s]['returns'])
      start_date = self.start.strftime('%Y-%m-%d')
      self.base_buy_price[s]  = self.history[s]['adj_close'][start_date]
      self.base_sell_price[s] = self.history[s]['adj_close'].iloc[-1]
  
  def _create_iterator(self):
    for s in self.tickers:
      self.latest_data[s] = []
      self.history[s] = self.history[s].iterrows()
  
  def _get_new_bar(self, ticker):
    for b in self.history[ticker]:
      yield b
  
  def get_latest_bars(self, ticker, nb):
    bars_list = self.latest_data[ticker]
    return bars_list[-nb:]
  
  def get_latest_bars_values(self, ticker, value_type, nb):
    bars_list = self.get_latest_bars(ticker, nb)
    return np.array([getattr(b[1], value_type) for b in bars_list])

  def update_bars(self):
    for s in self.tickers:
      try:
        bar = next(self._get_new_bar(s))
      except StopIteration:
        self.continue_backtest = False
      else:
        if bar is not None:
          self.latest_data[s].append(bar)
          self.current_date = datetime.datetime.strptime(bar[0], '%Y-%m-%d')
          if self.current_date >= self.start:
            self.events.put(market_event())