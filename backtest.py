#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import queue

from math import floor

import pandas as pd

from performance import plot_equity
from performance import compute_sharpe_ratio
from performance import compute_drawdowns
from performance import add_result

class backtest(object):
  def __init__(self, tickers, folder, start, init_cap, 
               handler, execution_handler, 
               portfolio, strategy, params_d):
    self.tickers  = tickers
    self.folder   = folder
    self.start    = start
    self.init_cap = init_cap
    self.params_d = params_d

    self.handler_cls   = handler
    self.portfolio_cls = portfolio
    self.strategy_cls  = strategy
    self.execution_handler_cls = execution_handler
    
    self.signal_count = 0
    self.order_count  = 0
    self.fill_count   = 0

    self.events = queue.Queue()
    # self._generate_instances()
  
  def _generate_instances(self, params_d):
    self.handler   = self.handler_cls(self.events, self.folder, 
                                      self.tickers, self.start)
    self.strategy  = self.strategy_cls(self.events, 
                                       self.handler, **params_d)
    self.portfolio = self.portfolio_cls(self.events, self.handler, 
                                        self.start, self.init_cap)
    self.execution_handler = self.execution_handler_cls(self.events)
  
  def run_simulation(self):
    out = open('output_options.csv', 'w')
    spl = len(self.params_d)
    for i, sp in enumerate(self.params_d):
      self._generate_instances(sp)
      self._run_backtest()
      stats = self._generate_results(False)
      print("Step %s of %s: %s,%s,%s,%s,%s,%s,%s" % (
        i+1, 
        spl,
        sp['short_window'],
        sp['long_window'],
        # sp['ols_w'],
        # sp['z_low'],
        # sp['z_high'],
        stats['ret'],
        stats['sharpe'],
        stats['max_dd'],
        stats['dur_dd'],
        'mac'
      ))
      out.write("%s,%s,%s,%s,%s,%s,%s\n" % (
        sp['short_window'],
        sp['long_window'],
        # sp['ols_w'],
        # sp['z_low'],
        # sp['z_high'],
        stats['ret'],
        stats['sharpe'],
        stats['max_dd'],
        stats['dur_dd'],
        'mac'
      ))
  
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
              self.portfolio.update_portfolio(event)
            elif event.type == 'signal':
              self.signal_count += 1
              self.portfolio.update_signal(event)
            elif event.type == 'order':
              self.order_count += 1
              self.execution_handler.execute_order(event)
            elif event.type == 'fill':
              self.fill_count += 1
              self.portfolio.update_fill(event)

  def _generate_results(self, verbose=True):
    if verbose == True:
      print(f"Signals: {self.signal_count}")
      print(f"Orders: {self.order_count}")
      print(f"Fills: {self.fill_count}")
      plot_equity(self.portfolio.all_hold)
    else:
      return add_result(self.portfolio.all_hold)