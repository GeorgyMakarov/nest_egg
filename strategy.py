#!/usr/bin/python
# -*- coding: utf-8 -*-

# strategy.py

from __future__ import print_function

from abc import ABCMeta
from abc import abstractmethod

import datetime
import queue

import numpy  as np
import pandas as pd

from event import signal_event

class strategy(object):
  __metaclass__ = ABCMeta
  
  @abstractmethod
  def calculate_signals(self):
    raise NotImplementedError("Implement caclulate_signals()")