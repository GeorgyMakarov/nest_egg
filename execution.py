#!/usr/bin/python
# -*- coding: utf-8 -*-

# execution.py

from __future__ import print_function

from abc import ABCMeta
from abc import abstractmethod

import datetime
import queue

from event import fill_event
from event import order_event


class execution_handler(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def execute_order(self, event):
    raise NotImplementedError("Should implement execute_order()")


class simulated_execution_handler(execution_handler):  
  def __init__(self, events):
    self.events = events

  def execute_order(self, event):
    if event.type == 'order':
      fill_event = fill_event(datetime.datetime.utcnow(), 
                              event.symbol,
                              'ARCA', 
                              event.quantity, 
                              event.direction, 
                              None)
      self.events.put(fill_event)