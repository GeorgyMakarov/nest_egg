#!/usr/bin/python
# -*- coding: utf-8 -*-

# portfolio.py

from __future__ import print_function

import datetime
import queue

from math import floor
import math

import numpy  as np
import pandas as pd

from event import fill_event
from event import order_event

from performance import create_sharpe_ratio
from performance import create_drawdowns


class portfolio(object):
  def __init__(self, bars, events, start_date, initial_capital):
    self.bars        = bars
    self.events      = events
    self.symbol_list = self.bars.symbol_list
    self.start_date  = start_date
    self.initial_capital = initial_capital

    self.all_positions     = self.construct_all_positions()
    self.current_positions = dict((k, v) for k, v \
                                  in [(s, 0) for s in self.symbol_list])
    
    self.all_holdings     = self.construct_all_holdings()
    self.current_holdings = self.construct_current_holdings()

  def construct_all_positions(self):
    d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
    d['datetime'] = self.start_date
    return [d]
  
  def construct_all_holdings(self):
    d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
    d['datetime']  = self.start_date
    d['cash']      = self.initial_capital
    d['commission'] = 0.0
    d['total']     = self.initial_capital
    return [d]
  
  def construct_current_holdings(self):
    d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
    d['cash']      = self.initial_capital
    d['commission'] = 0.0
    d['total']     = self.initial_capital
    return d
  
  def update_timeindex(self, event):
    latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])
    dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
    dp['datetime'] = latest_datetime
    for s in self.symbol_list:
      dp[s] = self.current_positions[s]
    self.all_positions.append(dp)
    dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
    dh['datetime'] = latest_datetime
    dh['cash'] = self.current_holdings['cash']
    dh['commission'] = self.current_holdings['commission']
    dh['total'] = self.current_holdings['cash']

    for s in self.symbol_list:
      market_value = self.current_positions[s] *\
                     self.bars.get_latest_bar_value(s, 'adj_close')
      dh[s] = market_value
      dh['total'] += market_value
    
    self.all_holdings.append(dh)
  
  def update_positions_from_fill(self, fill):
    fill_dir = 0
    if fill.direction == 'buy':
      fill_dir = 1
    if fill.direction == 'sell':
      fill_dir = 0
    self.current_positions[fill.symbol] += fill_dir * fill.quantity
  
  def update_holdings_from_fill(self, fill):
    fill_dir = 0
    if fill.direction == 'buy':
      fill_dir = 1
    if fill.direction == 'sell':
      fill_dir = 0
    fill_cost = self.bars.get_latest_bar_value(fill.symbol, 'adj_close')
    cost = fill_dir * fill_cost * fill.quantity
    self.current_holdings[fill.symbol] += cost
    self.current_holdings['commission'] += fill.commission
    self.current_holdings['cash'] -= (cost + fill.commission)
    self.current_holdings['total'] -= (cost + fill.commission)
  
  def update_fill(self, event):
    if event.type == 'fill':
      self.update_positions_from_fill(event)
      self.update_holdings_from_fill(event)
  

  def generate_naive_order(self, signal):
    order = None
    symbol = signal.symbol
    direction = signal.signal_type
    strength = signal.strength

    mkt_quantity = 100
    cur_quantity = self.current_positions[symbol]
    order_type = 'MKT'

    if direction == 'long' and cur_quantity == 0:
      order = order_event(symbol, order_type, mkt_quantity, 'buy')
    if direction == 'short' and cur_quantity == 0:
      order = order_event(symbol, order_type, mkt_quantity, 'sell')   
  
    if direction == 'exit' and cur_quantity > 0:
      order = order_event(symbol, order_type, abs(cur_quantity), 'sell')
    if direction == 'exit' and cur_quantity < 0:
      order = order_event(symbol, order_type, abs(cur_quantity), 'buy')
    return order

  def update_signal(self, event):
    if event.type == 'signal':
      order_event = self.generate_naive_order(event)
      self.events.put(order_event)

  def create_equity_curve_dataframe(self):
    curve = pd.DataFrame(self.all_holdings)
    curve.set_index('datetime', inplace=True)
    curve['returns'] = curve['total'].pct_change()
    curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
    self.equity_curve = curve

  def output_summary_stats(self):
    total_return = self.equity_curve['equity_curve'][-1]
    returns      = self.equity_curve['returns']
    pnl = self.equity_curve['equity_curve']

    sharpe_ratio = create_sharpe_ratio(returns, periods=252)
    drawdown, max_dd, dd_duration = create_drawdowns(pnl)
    self.equity_curve['drawdown'] = drawdown

    if math.isnan(dd_duration):
      dd_duration = 0

    stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
             ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
             ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
             ("Drawdown Duration", "%d" % dd_duration)]
    return stats