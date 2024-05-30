#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import queue

from math import floor

import pandas as pd

from performance import plot_equity
from performance import compute_sharpe_ratio
from performance import compute_drawdowns

class backtest(object):
  def __init__(self, tickers, folder, start, init_cap, 
               handler, portfolio, strategy):
    self.tickers  = tickers
    self.folder   = folder
    self.start    = start
    self.init_cap = init_cap

    self.handler_cls   = handler
    self.portfolio_cls = portfolio
    self.strategy_cls  = strategy

    self.signal_list  = []
    self.signal_df = pd.DataFrame()
    self.signal_count = 0

    self.events = queue.Queue()
    self._generate_instances()
  
  def _generate_instances(self):
    self.handler   = self.handler_cls(self.events, self.folder, 
                                      self.tickers, self.start)
    self.strategy  = self.strategy_cls(self.events, self.handler)
    self.portfolio = self.portfolio_cls(self.events, self.handler, 
                                        self.start, self.init_cap)
  
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
              self._update_signal_list(event)
              self.signal_count += 1
              self.portfolio.update_signal(event)
  
  def _update_signal_list(self, event):
    datetime  = event.dt
    direction = event.sig_type
    price     = event.price
    ds = (datetime, direction, price)
    self.signal_list.append(ds)

  def _create_balance_sheet(self, balance_sheet):
    balance_sheet.set_index('datetime', inplace=True)
    balance_sheet['equity']  = balance_sheet['capital'] + balance_sheet['profit']
    balance_sheet['returns'] = balance_sheet['equity'].pct_change()
    balance_sheet.fillna(value=0.0, inplace=True)
    balance_sheet['equity_curve'] = (1.0 + balance_sheet['returns']).cumprod()
    return balance_sheet

  def _output_summary(self, balance_sheet, baseline, base_rate=0.002):
    total_return = balance_sheet['equity_curve'][-1]
    sharpe   = compute_sharpe_ratio(balance_sheet['returns'])
    drawdown, max_dd, dd_duration = compute_drawdowns(balance_sheet['returns'])    
    npv_power = balance_sheet.shape[0] / 365
    npv_denom = (1 + base_rate) ** npv_power
    cash_flow = balance_sheet['profit'][-1] + balance_sheet['capital'][-1]
    npv_val = (cash_flow / npv_denom) - self.init_cap

    print("Baseline total = ", "%0.2f%%" % (baseline['total'] * 100.00))
    print("Total return = ", "%0.2f%%" % ((total_return - 1.0) * 100.00))
    print("Sharpe ratio = ", "%0.2f" % sharpe)
    print("Max drawdown = ", "%0.2f%%" % (max_dd * 100))
    print("Drawdown duration = ", "%d" % dd_duration)
    print("NPV = ", "%0.2f" % npv_val)
    print(f"Total signals = {self.signal_count}")
  
  def _output_signals(self):
    tmp = pd.DataFrame(self.signal_list)
    tmp.columns = ['datetime', 'direction', 'price']
    self.signal_df = tmp.copy()
  
  def generate_baseline(self, bs):
    result = {'total': 0.0, 'year': 0.0}
    inventory = {}
    cash = self.init_cap
    direct_cost = 3.76
    fixed_cost  = 200
    start = bs.index[0]
    end   = bs.index[-1]
    
    # Buy part
    for s in self.tickers:
      buy_price  = self.handler.base_buy_price[s]
      if cash - direct_cost > 0:
        qty = floor((cash - direct_cost) / buy_price)
        inventory[s] = qty
        cash -= buy_price * qty
        cash -= direct_cost
    
    # Sell part
    for s in self.tickers:
      sell_price = self.handler.base_sell_price[s]
      if inventory[s] > 0:
        revenue = inventory[s] * sell_price
        cash += revenue
        cash -= direct_cost
    
    dt_start = start.to_pydatetime()
    dt_end = end.to_pydatetime()
    delta = dt_end - dt_start
    delta = delta.days
    total_fixed_cost = 0
    if delta > 365:
      total_fixed_cost = fixed_cost * delta / 365
    cash -= total_fixed_cost
    total_return = (cash - self.init_cap) / self.init_cap
    year_return = total_return
    if delta > 365:
      year_return = total_return * 365 / delta
    result['total'] = total_return
    result['year'] = year_return
    return result
      

  def _generate_results(self):
    physical_inventory = pd.DataFrame(self.portfolio.all_pos)
    balance_sheet = pd.DataFrame(self.portfolio.all_hold)
    balance_sheet = self._create_balance_sheet(balance_sheet)
    baseline = self.generate_baseline(balance_sheet)
    plot_equity(balance_sheet, self.portfolio.all_pos, self.signal_df)
    self._output_summary(balance_sheet, baseline)
    self._output_signals()