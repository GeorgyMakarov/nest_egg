#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import queue

import numpy as np
import pandas as pd

from math import floor

class portfolio(object):
  def __init__(self, events, handler, start, init_cap):
    self.events   = events
    self.handler  = handler
    self.start    = start
    self.init_cap = init_cap
    self.tickers  = self.handler.tickers

    self.all_pos  = self._make_all_pos()
    self.cur_pos  = self._make_cur_pos()
    self.all_hold = self._make_all_hold()
    self.cur_hold = self._make_cur_hold()
  
  def _make_all_pos(self):
    d = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    d['datetime'] = self.start
    return [d]
  
  def _make_cur_pos(self):
    d = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    return d
  
  def _make_all_hold(self):
    d = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    d['datetime']  = self.start
    # Simplified balance sheet
    d['inventory'] = 0.0
    d['cash']      = self.init_cap
    d['capital']   = self.init_cap
    d['profit']    = 0.0
    return [d]
  
  def _make_cur_hold(self):
    d = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    d['inventory'] = 0.0
    d['cash']      = self.init_cap
    d['capital']   = self.init_cap
    d['profit']    = 0.0
    return d
  
  def update_data(self, event):
    dp = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    dp['datetime'] = self.handler.current_date
    for s in self.tickers:
      dp[s] = self.cur_pos[s]
    self.all_pos.append(dp)
    print(self.all_pos)

  def _compute_qty(self, ticker, price):
    res   = 0.0
    cash  = self.cur_hold['cash']
    min_cost  = 3.76
    norm_cost = 0.08 / 100
    # Use comission value that is higher by choosing the
    # available quantity that is lower
    q1 = floor((cash - min_cost) / price)
    q2 = floor(cash / (price + norm_cost))




    return res


  def update_signal(self, event):
    direct  = event.sig_type
    ticker  = event.ticker
    price   = event.price
    cur_qty = self.cur_pos[ticker]
    if direct == 'long' and cur_qty == 0:
      trans_qty, comission = self._compute_qty(ticker, price)
      print(f"Date: {event.dt}, type: {event.sig_type}, trans_qty: {trans_qty}")

    if direct == 'exit' and cur_qty > 0:
      action = 'sell'
