#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from events import order_event
from events import fill_event

from abc import ABCMeta
from abc import abstractmethod

class execution_handler(object):
  __metaclass__ = ABCMeta
  
  @abstractmethod
  def execute_order(self, event):
    raise NotImplementedError("Implement execute_order")

class daily_handler(execution_handler):
  def __init__(self, events):
    self.events = events
  
  def execute_order(self, event):
    if event.type == 'order':
      fe = fill_event(event.ticker, event.quantity, event.direction, event.price)
      self.events.put(fe)
