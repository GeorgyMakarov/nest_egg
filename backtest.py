#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import queue

import pandas as pd

from performance import plot_equity
from performance import compute_sharpe_ratio
from performance import compute_drawdowns

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
  
  def _create_balance_sheet(self, balance_sheet):
    balance_sheet.set_index('datetime', inplace=True)
    balance_sheet['equity']  = balance_sheet['capital'] + balance_sheet['profit']
    balance_sheet['returns'] = balance_sheet['equity'].pct_change()
    balance_sheet.fillna(value=0.0, inplace=True)
    balance_sheet['equity_curve'] = (1.0 + balance_sheet['returns']).cumprod()
    return balance_sheet

  def _output_summary(self, balance_sheet):
    total_return = balance_sheet['equity_curve'][-1]
    sharpe   = compute_sharpe_ratio(balance_sheet['returns'])
    drawdown, max_dd, dd_duration = compute_drawdowns(balance_sheet['returns'])
    npv_val  = 0.0
    stats = [("Total return = ", "%0.2f%%" % ((total_return - 1.0) * 100.00)), 
             ("Sharpe ratio = ", "%0.2f" % sharpe), 
             ("Max drawdown = ", "%0.2f%%" % (max_dd * 100)), 
             ("Drawdown duration = ", "%d" % dd_duration), 
             ("NPV = ", "%0.2f" % npv_val)]
    return stats

  def _generate_results(self):
    physical_inventory = pd.DataFrame(self.portfolio.all_pos)
    balance_sheet = pd.DataFrame(self.portfolio.all_hold)
    balance_sheet = self._create_balance_sheet(balance_sheet)
    plot_equity(balance_sheet)
    stats = self._output_summary(balance_sheet)
    print(stats)