#!user/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import numpy  as np
import pandas as pd

from event import signal_event ## complete
from data  import historic_csv_data_handler ## complete
from mac   import moving_avg_cross_strategy  ## complete
from portfolio import portfolio
from trade_engine import trade_engine
from execution_handlers import simulated_execution_handler

if __name__ == "__main__":
  folder    = "/content/"
  symbols   = ["IUIT_L"]
  capital   = 10000
  frequency = 0.0
  start_day = datetime.datetime(2021, 11, 19, 0, 0, 0)

  backtest = trade_engine(folder   = folder,
                          symbols  = symbols,
                          init_cap = capital,
                          freq     = frequency,
                          start_d  = start_day,
                          data_handler      = historic_csv_data_handler,
                          execution_handler = simulated_execution_handler,
                          portfolio         = portfolio,
                          strategy          = moving_avg_cross_strategy)

  backtest.simulate_trading()