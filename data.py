#!user/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from abc import ABCMeta
from abc import abstractmethod

import datetime
import os
import os.path

import numpy as np
import pandas as pd

from event import market_event

# An abstract base class (ABC) meaning it is impossible to instantiate
# an instance directly. Only subclasses can be instantiated.
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
  def get_latest_bars(self, symbol, n_bars=1):
    raise NotImplementedError("Implement get_latest_bars()")

  @abstractmethod
  def get_latest_bar_datetime(self, symbol):
    raise NotImplementedError("Implement get_latest_bar_datetime()")

  @abstractmethod
  def get_latest_bar_value(self, symbol, v_type):
    raise NotImplementedError("Implement get_latest_bar_value()")

  @abstractmethod
  def get_latest_bars_values(self, symbol, v_type, n_bars=1):
    raise NotImplementedError("Implement get_latest_bars_values()")

  @abstractmethod
  def update_bars(self):
    raise NotImplementedError("Implement update_bars()")

class historic_csv_data_handler(data_handler):
  """
  Reads CSV files for each requested symbol from disk.
  """
  def __init__(self, events, folder, symbols):
    """
    Initialises the handler given a path to CSV files and a list of symbols to
    include. The requirement is that the names of the files match the names of
    the symbols, e.g. 'AAPL' -- 'AAPL.csv'

    Args:
        events (queue object): The queue of events.
        csv_path (str): The full path to the folder with CSV files.
        symb_l (list): The list of tickers to include.
    """
    self.events  = events
    self.folder  = folder
    self.symbols = symbols

    self.symbol_data        = {}
    self.latest_symbol_data = {}
    self.continue_backtest  = True

    self._open_convert_csv_files()

  def _open_convert_csv_files(self):
    """
    Opens CSV files and converts them into a dictionary of pandas dataframes.
    Requires CSV files to be in Yahoo Finance format.
    """
    comb_index = None

    for s in self.symbols:
      path_to_file = os.path.join(self.folder, '%s.csv' % s)
      self.symbol_data[s] = pd.read_csv(path_to_file)
      if comb_index is None:
        comb_index = self.symbol_data[s].index
      else:
        comb_index.union(self.symbol_data[s].index)
      self.latest_symbol_data[s] = []

    print("Generating symbols' iterator")
    for s in self.symbols:
      self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()

  def update_bars(self):
    """
    Updates the latest bar for each of the symbols
    """
    for s in self.symbols:
      try:
        bar = next(self._get_new_bar(s))
      except StopIteration:
        self.continue_backtest = False
      else:
        if bar is not None:
          self.latest_symbol_data[s].append(bar)
    self.events.put(market_event())

  def _get_new_bar(self, symbol):
    """
    Returns the latest bar from the data feed.
    """
    for b in self.symbol_data[symbol]:
      yield b

  def get_latest_bar(self, symbol):
    try:
      bars_list = self.latest_symbol_data[symbol]
    except KeyError:
      print(f"Symbol {symbol} is not present in the data.")
      raise
    else:
      return bars_list[-1]

  def get_latest_bars(self, symbol, n_bars=1):
    try:
      bars_list = self.latest_symbol_data[symbol]
    except KeyError:
      print(f"Symbol {symbol} is not present in the data.")
      raise
    else:
      return bars_list[-n_bars:]
  
  def get_latest_bar_datetime(self, symbol):
    try:
      bars_list = self.latest_symbol_data[symbol]
    except KeyError:
      print(f"Symbol {symbol} is not present in the data.")
      raise
    else:
      return bars_list[-1][0]
  
  def get_latest_bar_value(self, symbol, v_type):
    try:
      bars_list = self.latest_symbol_data[symbol]
    except KeyError:
      print(f"Symbol {symbol} is not present in the data.")
      raise
    else:
      return getattr(bars_list[-1][1], v_type)
  
  def get_latest_bars_values(self, symbol, v_type, n_bars=1):
    try:
      bars_list = self.get_latest_bars(symbol, n_bars)
    except KeyError:
      print(f"Symbol {symbol} is not present in the data.")
      raise
    else:
      return np.array([getattr(b[1], v_type) for b in bars_list])