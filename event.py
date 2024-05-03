#!user/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from math import ceil

class event(object):
  """
  Base class with an interface for all inherited events.
  """
  pass

class market_event(event):
  """
  Receives a new market update for selected bars.
  """
  def __init__(self):
    self.type = 'market'

class signal_event(event):
  """
  Sends a signal from strategy to portfolio allowing the latter to act based on
  the signal.
  """
  def __init__(self, id, symb, datetime, s_type, s_power):
    """
    Initialises a signal event.

    Args:
        id (str): The unique strategy identifier.
        symb (str): The name of a ticker symbol, e.g. 'AAPL'.
        datetime (timestamp): The timestamp at which a signal was generated.
        s_type (str): The type of a signal: 'long' | 'short'
        s_power (decimal): An adjustment factor suggestion for pair trading.
    """
    self.type = 'signal'
    self.id = id
    self.symb = symb
    self.datetime = datetime
    self.s_type = s_type
    self.s_power = s_power

class order_event(event):
  """
  Sends an order to an execution system supplying information about a symbol,
  quantity and direction.
  """
  def __init__(self, symb, qnt, direct):
    """
    Initialises an order event.

    Args:
        symb (str): The name of a ticker symbol, e.g. 'AAPL'.
        qnt (int): The quantity of an order, always integer
        direct (str): The direction of an order: 'buy' | 'sell'
    """
    self.type = 'order'
    self.symb = symb
    self.qnt  = qnt
    self.direct = direct

  def print_order(self):
    """
    Prints out the values of an order
    """
    print(f"OD: symbol = {self.symb}, vol = {self.qnt}, dir = {self.direct}")

class fill_event(event):
  """
  Stores the quantity of stocks filled, prices, costs.
  """
  def __init__(self, t_idx, symb, qnt, direct, f_cost):
    """
    Initialises a fill event object.

    Args:
        t_idx (timestamp):
        symb (str): The name of a ticker symbol, e.g. 'AAPL'.
        qnt (int): The quantity of an order, always integer
        direct (str): The direction of an order: 'buy' | 'sell'
        f_cost (decimal): The cost of transaction.
    """
    self.type = 'fill'
    self.t_idx = t_idx
    self.symb = symb
    self.qnt = qnt
    self.direct = direct

    if f_cost is None:
      self.f_cost = self.calculate_cost()
    else:
      self.f_cost = f_cost
    
  def calculate_cost(self):
    """
    Calculates the cost of transaction based on the costs stated in Saxo Trader
    platform for IUIT.L instrument. If the volume of an order is lower that
    some required level, then minimal cost is applied, otherwise -- the cost is
    computed using exchange rates and order volume.
    """
    min_cost = 3.76 ## USD
    comission = 0.08 / 100 ## 0.08%
    f_cost = max(min_cost, self.qnt * comission)
    return f_cost
  
  def print_fill_event(self):
    """
    Prints out fill event parameters
    """
    print(f"FE: symbol = {self.symb}, vol = {self.qnt}, cost = {self.f_cost}")