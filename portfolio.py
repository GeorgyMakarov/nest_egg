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
    d = dict()
    d['datetime']  = self.start
    # Simplified balance sheet
    d['inventory'] = 0.0
    d['cash']      = self.init_cap
    d['capital']   = self.init_cap
    d['profit']    = 0.0
    d['balance_check'] = d['cash'] + d['inventory'] - d['capital'] - d['profit']
    return [d]
  
  def _make_cur_hold(self):
    d = dict()
    d['inventory'] = 0.0
    d['cash']      = self.init_cap
    d['capital']   = self.init_cap
    d['profit']    = 0.0
    d['balance_check'] = d['cash'] + d['inventory'] - d['capital'] - d['profit']
    return d
  
  def update_data(self, event):
    dp = dict((k, v) for k, v in [(s, 0) for s in self.tickers])
    dp['datetime'] = self.handler.current_date
    for s in self.tickers:
      dp[s] = self.cur_pos[s]
    self.all_pos.append(dp)
    dh = dict()
    dh['datetime'] = self.handler.current_date
    dh['inventory'] = self.cur_hold['inventory']
    dh['cash'] = self.cur_hold['cash']
    dh['capital'] = self.cur_hold['capital']
    dh['profit'] = self.cur_hold['profit']
    dh['balance_check'] = self.cur_hold['balance_check']
    self.all_hold.append(dh)

  def _compute_qty(self, ticker, price):
    res   = 0.0
    cash  = self.cur_hold['cash']
    commission = 3.76
    res = floor((cash - commission) / price)
    return res
  
  def _compute_comission(self, qty):
    cost = 3.76
    return cost

  def buy_transaction(self, comission, trans_qty, price, ticker):
    market_value = round(trans_qty * price, 2)
    payment = round(market_value + comission, 2)
    self.cur_hold['inventory'] += market_value
    self.cur_hold['cash'] -= payment
    self.cur_hold['profit'] = self.cur_hold['inventory'] +\
                              self.cur_hold['cash'] -\
                              self.cur_hold['capital']
    self.cur_hold['balance_check'] = self.cur_hold['inventory'] +\
                                     self.cur_hold['cash'] -\
                                     self.cur_hold['capital'] -\
                                     self.cur_hold['profit']
    self.cur_pos[ticker] += trans_qty
  
  def sell_transaction(self, comission, trans_qty, price, ticker):
    market_value = round(trans_qty * price, 2)
    income = round(market_value - comission, 2)
    self.cur_hold['inventory'] = 0
    self.cur_hold['cash'] += income
    self.cur_hold['profit'] = self.cur_hold['inventory'] +\
                              self.cur_hold['cash'] -\
                              self.cur_hold['capital']
    self.cur_hold['balance_check'] = self.cur_hold['inventory'] +\
                                     self.cur_hold['cash'] -\
                                     self.cur_hold['capital'] -\
                                     self.cur_hold['profit']
    self.cur_pos[ticker] = 0
    
  def update_signal(self, event):
    direct  = event.sig_type
    ticker  = event.ticker
    price   = event.price
    cur_qty = self.cur_pos[ticker]
    if direct == 'long' and cur_qty == 0:
      trans_qty = self._compute_qty(ticker, price)
      comission = self._compute_comission(trans_qty)
      self.buy_transaction(comission, trans_qty, price, ticker)      
    if direct == 'exit' and cur_qty > 0:
      trans_qty = self.cur_pos[ticker]
      comission = self._compute_comission(trans_qty)
      self.sell_transaction(comission, trans_qty, price, ticker)