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

class order_event(event):
  def __init__(self, ticker, quantity, direction, price):
    self.type = 'order'
    self.ticker = ticker
    self.quantity = quantity
    self.direction = direction
    self.price = price

class fill_event(event):
  def __init__(self, ticker, quantity, direction, price):
    self.type = 'fill'
    self.ticker = ticker
    self.quantity = quantity
    self.direction = direction
    self.price = price

    com1 = 3.76
    com2 = self.price * self.quantity * 0.08 * 0.01

    self.commission = max([com1, com2])