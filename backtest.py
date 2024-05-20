#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import queue

import pandas as pd

class backtest(object):
  def __init__(self, tickers, folder, start, init_cap, handler, portfolio, strategy):
    self.tickers  = tickers
    self.folder   = folder
    self.start    = start
    self.init_cap = init_cap

    self.handler_cls   = handler
    self.portfolio_cls = portfolio
    self.strategy_cls  = strategy

    self.signal_list  = {}
    self.signal_count = 0

    self.events = queue.Queue()
    self._generate_instances()
  
  def _generate_instances(self):
    self.handler   = self.handler_cls(self.events, self.folder, self.tickers, self.start)
    self.strategy  = self.strategy_cls(self.events, self.handler)
    self.portfolio = self.portfolio_cls(self.events, self.handler, self.start, self.init_cap)
  
  def run_simulation(self):
    self._run_backtest()
    self._generate_results()
  
  def _run_backtest(self):
    while True:
      if self.handler.continue_backtest == True:
        self.handler.update_bars()
      else:
        break
      while True:
        try:
          event = self.events.get(False)
        except queue.Empty:
          break
        else:
          if event is not None:
            if event.type == 'market':
              self.strategy.calculate_signal(event)
              self.portfolio.update_data(event)
            if event.type == 'signal':
              self.portfolio.update_signal(event)
  
  def _generate_results(self):
    physical_inventory = pd.DataFrame(self.portfolio.all_pos)
    balance_sheet = pd.DataFrame(self.portfolio.all_hold)
    print(balance_sheet.head(15))