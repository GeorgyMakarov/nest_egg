#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import ABCMeta
from abc import abstractmethod

class strategy(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def calculate_signal(self):
    raise NotImplementedError("Please implement calculate_signal()")