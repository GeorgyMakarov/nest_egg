#!user/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import queue
import numpy  as np
import pandas as pd

from math import floor
from event import fill_event
from event import order_event
from performance import create_sharpe_ratio
from performance import create_drawdowns

class portfolio(object):
  def __init__(self, bars, events, start_d, init_cap):
    self.bars     = bars
    self.events   = events
    self.symbols  = self.bars.symbols
    self.start_d  = start_d
    self.init_cap = init_cap
    self.all_pos  = self.construct_all_positions()
    self.cur_pos  = dict( (k, v) for k, v in [(s, 0) for s in self.symbols] )
    self.all_hold = self.construct_all_holdings()
    self.cur_hold = self.construct_current_holdings()

  def construct_all_positions(self):
    d = dict( (k, v) for k, v in [(s, 0) for s in self.symbols] )
    d['datetime'] = self.start_d
    return [d]
  
  def construct_all_holdings(self):
    d = dict( (k, v) for k, v in [(s, 0) for s in self.symbols] )
    d['datetime'] = self.start_d
    d['cash'] = self.init_cap
    d['commission'] = 0.0
    d['total'] = self.init_cap
    return [d]
  
  def construct_current_holdings(self):
    d = dict( (k, v) for k, v in [(s, 0) for s in self.symbols] )
    d['cash'] = self.init_cap
    d['commission'] = 0.0
    d['total'] = self.init_cap
    return d

  def update_timeindex(self, event):
    latest_datetime = self.bars.get_latest_bar_datetime(self.symbols[0])
    dp = dict( (k, v) for k, v in [(s, 0) for s in self.symbols] )
    dp['datetime'] = latest_datetime
    for s in self.symbols:
      dp[s] = self.cur_pos[s]
    self.all_pos.append(dp)

    dh = dict( (k, v) for k, v in [(s, 0) for s in self.symbols] )
    dh['datetime'] = latest_datetime
    dh['cash'] = self.cur_hold['cash']
    dh['commission'] = self.cur_hold['commission']
    dh['total'] = self.cur_hold['cash']

    for s in self.symbols:
      market_value = self.cur_pos[s] * self.bars.get_latest_bar_value(s, "adj_close")
      dh[s] = market_value
      dh['total'] += market_value
    self.all_hold.append(dh)

  def update_fill(self, event):
    if event.type == 'fill':
      self.update_positions_from_fill(event)
      self.update_holdings_from_fill(event)
  
  def update_positions_from_fill(self, fill):
    fill_dir = 0
    if fill.direct == 'buy':
      fill_dir = 1
    if fill.direct == 'sell':
      fill_dir = -1
    
    self.cur_pos[fill.symb] += fill_dir * fill.qnt
  
  def update_holdings_from_fill(self, fill):
    fill_dir = 0
    if fill.direct == 'buy':
      fill_dir = 1
    if fill.direct == 'sell':
      fill_dir = -1
    fill_cost = self.bars.get_latest_bar_value(fill.symb, "adj_close")
    cost = fill_dir * fill_cost * fill.qnt
    self.cur_hold[fill.symb] += cost
    self.cur_hold['commission'] += fill.f_cost
    self.cur_hold['cash'] -= (cost + fill.f_cost)
    self.cur_hold['total'] -= (cost + fill.f_cost)

  def generate_naive_order(self, signal):
    order     = None
    symbol    = signal.symb
    direction = signal.s_type
    strength  = signal.s_power
    mkt_quantity = 100
    cur_quantity = self.cur_pos[symbol]
    
    if direction == 'LONG' and cur_quantity == 0:
      order = order_event(symbol, mkt_quantity, 'buy')
    if direction == 'SHORT' and cur_quantity == 0:
      order = order_event(symbol, mkt_quantity, 'sell')

    if direction == 'EXIT' and cur_quantity > 0:
      order = order_event(symbol, abs(cur_quantity), 'sell')
    if direction == 'EXIT' and cur_quantity < 0:
      order = order_event(symbol, abs(cur_quantity), 'buy')
    
    return order
  
  def update_signal(self, event):
    if event.type == 'signal':
      order_event = self.generate_naive_order(event)
      self.events.put(order_event)
  
  def create_equity_curve_dataframe(self):
    curve = pd.DataFrame(self.all_hold)
    curve['returns'] = curve['total'].pct_change()
    curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
    self.equity_curve = curve
  
  def output_summary_stats(self):
    total_return = self.equity_curve['equity_curve'].tolist()[-1]
    returns = self.equity_curve['returns']
    pnl = self.equity_curve['equity_curve']
    sharpe_ratio = create_sharpe_ratio(returns, periods=252)
    drawdown, max_dd, dd_duration = create_drawdowns(pnl)
    stats = [(f"Total return = {(total_return - 1) * 100}"), 
             (f"Sharpe ratio = {sharpe_ratio}"), 
             (f"Max drawdown = {max_dd}"), 
             (f"Drawdown duration = {dd_duration}")]
    return stats