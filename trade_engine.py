#!user/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import pprint
import queue
import time

class trade_engine(object):
  """
  Contains all settings and components required to run trading algorithm based
  on event-driven engine.
  """
  def __init__(self, 
               folder, 
               symbols, 
               init_cap, 
               freq, 
               start_d, 
               data_handler,
               execution_handler,
               portfolio,
               strategy):
    """
    Initialises an application.

    Args:
        csv_path (str): The path to the folder containing historic CSV files.
        symb_l (list): The list of the symbols to look for.
        init_cap (decimal): The amount of initial capital.
        freq (int): The frequency of trading in seconds (set 0.0 for historic).
        start_d (timestamp): The start date and time of the trading.
        data_handler (class): The class handling the market data.
        execution_handler (class): The class handling the execution.
        portfolio (class): The class tracking positions.
        strategy (class): The class generating trading signals.
    """
    self.folder   = folder
    self.symbols  = symbols
    self.init_cap = init_cap
    self.freq     = freq
    self.start_d  = start_d
    
    self.data_handler_cls      = data_handler
    self.execution_handler_cls = execution_handler
    self.portfolio_cls         = portfolio
    self.strategy_cls          = strategy

    self.events = queue.Queue()

    self.signals    = 0
    self.orders     = 0
    self.fills      = 0
    self.num_strats = 1

    self._generate_trading_instances()
  
  def _generate_trading_instances(self):
    print("Generating trading instances ...")
    self.data_handler = self.data_handler_cls(self.events, self.folder, self.symbols)
    self.strategy = self.strategy_cls(self.data_handler, self.events)
    self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_d, self.init_cap)
    self.execution_handler = self.execution_handler_cls(self.events)


  def _run_engine(self):
    i = 0
    while True:
      i += 1
      if self.data_handler.continue_backtest == True:
        self.data_handler.update_bars()
      else:
        break
      
      while True:
        try:
          event = self.events.get(False)
        except queue.Empty:
          break
        else:
          if event is not None:
            if event.type == 'market':
              self.strategy.calculate_signals(event)
              self.portfolio.update_timeindex(event)
            elif event.type == 'signal':
              self.signals += 1
              self.portfolio.update_signal(event)
            elif event.type == 'order':
              self.orders += 1
              self.execution_handler.execute_order(event)
              print('Order event')
            elif event.type == 'fill':
              self.fills += 1
              self.portfolio.update_fill(event)
              print('Fill event')
    time.sleep(self.freq)
  
  def _output_performance(self):
    self.portfolio.create_equity_curve_dataframe()
    stats = self.portfolio.output_summary_stats()
    print(self.portfolio.equity_curve.tail(10))
    pprint.pprint(stats)
    print("Signals: %s" % self.signals)
    print("Orders: %s" % self.orders)
    print("Fills: %s" % self.fills)

  def simulate_trading(self):
    print("Running trading engine ...")
    self._run_engine()
    print("Printing out performance ...")
    self._output_performance()