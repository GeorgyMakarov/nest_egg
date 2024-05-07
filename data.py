#!/usr/bin/python
# -*- coding: utf-8 -*-

# data.py

from __future__ import print_function

from abc import ABCMeta
from abc import abstractmethod

import datetime
import os
import os.path

import numpy  as np
import pandas as pd

from event import market_event


class data_handler(object):
  """
  The main idea of the class is to generate a set of bars for each symbol
  allowing to treat backtesting and live trading identically.
  """
  __metaclass__ = ABCMeta
  @abstractmethod
  def get_latest_bar(self, symbol):
    raise NotImplementedError("Implement get_latest_bar()")

  @abstractmethod
  def get_latest_bars(self, symbol, N=1):
    raise NotImplementedError("Implement get_latest_bars()")

  @abstractmethod
  def get_latest_bar_datetime(self, symbol):
    raise NotImplementedError("Implement get_latest_bar_datetime()")

  @abstractmethod
  def get_latest_bar_value(self, symbol, val_type):
    raise NotImplementedError("Implement get_latest_bar_value()")

  @abstractmethod
  def get_latest_bars_values(self, symbol, val_type, N=1):
    raise NotImplementedError("Implement get_latest_bars_values()")

  @abstractmethod
  def update_bars(self):
    raise NotImplementedError("Implement update_bars()")




class historic_csv_data_handler(data_handler):
  def __init__(self, events, csv_dir, symbol_list):
    self.events = events
    self.csv_dir = csv_dir
    self.symbol_list = symbol_list
    self.symbol_data = {}
    self.latest_symbol_data = {}
    self.continue_backtest  = {}

    self._open_convert_csv_files()

  def _open_convert_csv_files(self):
    comb_index = None
    for s in self.symbol_list:
      self.symbol_data[s] = pd.read_csv(os.path.join(self.csv_dir, '%s.csv' %s))

      if comb_index is None:
        comb_index = self.symbol_data[s].index
      else:
        comb_index.union(self.symbol_data[s].index)
      self.latest_symbol_data[s] = []
    for s in self.symbol_list:
      self.symbol_data[s] = self.symbol_data[s].\
                            reindex(index=comb_index, method='pad').iterrows()

  def _get_new_bar(self, symbol):
    for b in self.symbol_data[symbol]:
      yield b

  def get_latest_bar(self, symbol):
    try:
      bars_list = self.latest_symbol_data[symbol]
    except KeyError:
      print(f"Symbol {symbol} not found in historical data.")
      raise
    else:
      return bars_list[-1]
  
  def get_latest_bars(self, symbol, N=1):
    try:
      bars_list = self.latest_symbol_data[symbol]
    except KeyError:
      print(f"Symbol {symbol} not found in historical data.")
      raise
    else:
      return bars_list[-N:]
  
  def get_latest_bar_datetime(self, symbol):
    try:
      bars_list = self.latest_symbol_data[symbol]
    except KeyError:
      print(f"Symbol {symbol} not found in historical data.")
      raise
    else:
      return getattr(bars_list[-1][1], 'datetime')      
  
  def get_latest_bar_value(self, symbol, val_type):
    try:
      bars_list = self.latest_symbol_data[symbol]
    except KeyError:
      print(f"Symbol {symbol} not found in historical data.")
      raise
    else:
      return getattr(bars_list[-1][1], val_type)
  
  def get_latest_bars_values(self, symbol, val_type, N=1):
    try:
      bars_list = self.get_latest_bars(symbol, N)
    except KeyError:
      print(f"Symbol {symbol} not found in historical data.")
      raise
    else:
      return np.array([getattr(b[1], val_type) for b in bars_list])
  
  def update_bars(self):
    for s in self.symbol_list:
      try:
        bar = next(self._get_new_bar(s))
      except StopIteration:
        self.continue_backtest = False
      else:
        if bar is not None:
          self.latest_symbol_data[s].append(bar)
    self.events.put(market_event())