#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import queue

import numpy as np
import pandas as pd

from math import floor

from events import order_event
from events import fill_event

class portfolio(object):
  def __init__(self, events, handler, start, init_cap):
    self.events   = events
    self.handler  = handler
    self.start    = start
    self.init_cap = init_cap
    self.tickers  = self.handler.tickers

    self.all_pos  = self._create_all_pos()
    self.cur_pos  = self._create_cur_pos()
    self.all_hold = self._create_all_hold()
    self.cur_hold = self._create_cur_hold()
  
  def _create_all_pos(self):
    d = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    d['datetime'] = self.start
    return [d]
  
  def _create_cur_pos(self):
    d = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    return d
  
  def _create_all_hold(self):
    d = dict( (k, v) for k, v in [(s, 0) for s in self.tickers] )
    d['datetime'] = self.start
    d['cash'] = self.init_cap
    d['commission'] = 0.0
    d['total'] = self.init_cap    
    return [d]
  
  def _create_cur_hold(self):
    d = dict( (k, v) for k, v in [(s, 0) for s in self.tickers] )
    d['cash'] = self.init_cap
    d['commission'] = 0.0
    d['total'] = self.init_cap
    return d
  
  def update_portfolio(self, event):
    dp = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    dp['datetime'] = self.handler.current_date
    for s in self.tickers:
      dp[s] = self.cur_pos[s]
    self.all_pos.append(dp)

    dh = dict( (k, v) for k, v in [(s, 0) for s in self.tickers] )
    dh['datetime'] = self.handler.current_date
    dh['cash'] = self.cur_hold['cash']
    dh['commission'] = self.cur_hold['commission']
    dh['total'] = self.cur_hold['total']

    # Appreciation / depreciation of inventory to market value
    for t in self.tickers:
      latest_price = self.handler.get_latest_bars_values(t, 'adj_close', 1)[0]
      mv = self.cur_pos[t] * latest_price
      dh[t] = mv
      dh['total'] += mv
    self.all_hold.append(dh)

  def generate_naive_order(self, signal):
    order = None
    
    ticker = signal.ticker
    direction = signal.sig_type
    strength  = signal.sig_str
    price = signal.price
    market_qty  = floor(20 * strength)
    current_qty = self.cur_pos[ticker]

    if direction == 'long' and current_qty == 0:
      print(f"Ticker {ticker}: long, buy, {price:.2f}, {market_qty}")
      order = order_event(ticker, market_qty, 'buy', price)
    if direction == 'short' and current_qty == 0:
      print(f"Ticker {ticker}: short, sell, {price:.2f}, {market_qty}")
      order = order_event(ticker, market_qty, 'sell', price)
    if direction == 'exit' and current_qty > 0:
      print(f"Ticker {ticker}: exit, sell, {price:.2f}, {abs(current_qty)}")
      order = order_event(ticker, abs(current_qty), 'sell', price)
    if direction == 'exit' and current_qty < 0:
      print(f"Ticker {ticker}: exit, buy, {price:.2f}, {abs(current_qty)}")
      order = order_event(ticker, abs(current_qty), 'buy', price)
    return order

  def update_signal(self, event):
    if event.type == 'signal':
      order_event = self.generate_naive_order(event)
      self.events.put(order_event)
  
  def update_fill(self, event):
    if event.type == 'fill':
      self.update_positions_from_fill(event)
      self.update_holdings_from_fill(event)
  
  def update_positions_from_fill(self, fill):
    fill_dir = 0
    if fill.direction == 'buy':
      fill_dir = 1
    if fill.direction == 'sell':
      fill_dir = -1
    self.cur_pos[fill.ticker] += fill_dir*fill.quantity
  
  def update_holdings_from_fill(self, fill):
    fill_dir = 0
    if fill.direction == 'buy':
      fill_dir = 1
    if fill.direction == 'sell':
      fill_dir = -1
    amount = fill_dir * fill.price * fill.quantity
    self.cur_hold[fill.ticker] += amount
    self.cur_hold['commission'] += fill.commission
    self.cur_hold['cash'] -= (amount + fill.commission)
    self.cur_hold['total'] -= (amount + fill.commission)
