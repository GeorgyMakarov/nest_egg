#!/usr/bin/python
# -*- coding: utf-8 -*-

class event(object):
  pass

class market_event(event):
  def __init__(self):
    self.type = 'market'

class signal_event(event):
  def __init__(self, ticker, dt, sig_type, sig_str, price):
    self.type     = 'signal'
    self.ticker   = ticker
    self.dt       = dt
    self.sig_type = sig_type
    self.sig_str  = sig_str
    self.price    = price
