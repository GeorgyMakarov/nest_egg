#!/usr/bin/python
# -*- coding: utf-8 -*-

# event.py

from __future__ import print_function

class event(object):
  pass

class market_event(event):
  def __init__(self):
    self.type = 'market'

class signal_event(event):
  def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
    self.type = 'signal'
    self.strategy_id = strategy_id
    self.symbol      = symbol
    self.datetime    = datetime
    self.signal_type = signal_type
    self.strength    = strength

class order_event(event):
  def __init__(self, symbol, order_type, quantity, direction):
    self.type       = 'order'
    self.symbol     = symbol
    self.order_type = order_type
    self.quantity   = quantity
    self.direction  = direction
  
  def print_order(self):
    print(
        "Order: symbol = %s, type = %s, quantity = %s, direction = %s" %
        (self.symbol, self.order_type, self.quantity, self.direction)
    )

class fill_event(event):
  def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission):
    self.type = 'fill'
    self.timeindex = timeindex
    self.symbol    = symbol
    self.exchange  = exchange
    self.quantity  = quantity
    self.direction = direction
    self.fill_cost = fill_cost
    
    if commission is None:
      self.commission = self.calculate_commission()
    else:
      self.commission = commission
  
  def calculate_commission(self):
    min_commission = 3.76
    percentage_commission = 0.08 / 100
    full_cost = max(min_commission, percentage_commision * self.quantity)
    return full_cost