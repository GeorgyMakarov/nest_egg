import time
from src.argparser import ArgParser
from src.setup_logger import setup_log
from src.data_loader import DataLoader
from src.market_scales import MarketScales
from src.buy_hold_strategy import BuyHoldStrategy
from src.arma_garch_strat import ArmaGarchStrategy

# TODO: REMOVE this after testing is done, temp workaround
import polars as pl

# Constants in CAPITAL
CON  = r"C:\sqlite\\trading.db"
AMT  = 1000
INCR = 20
# Brokers take commissions for their services. Typically, it is 5% per one
# transaction, or $50 if there is no activity during 3 months (quarter)
COMMS = {'transaction': 0.05, 'no_activity': 50.0}

def main():
  parser   = ArgParser(['cat', 'ma', 'test'], setup_log('ArgParser'))
  args     = parser.parse()
  loader   = DataLoader(CON, setup_log('DataLoader'))
  tickers  = loader.get_tickers(args)
  baseline = loader.get_history(103)
  
  benchmarker = BuyHoldStrategy(AMT, INCR, COMMS, setup_log(f"Benchmark"))
  benchmarks = benchmarker.compute_strategy('gspc', baseline, args)
  benchmarks = benchmarker.evaluate_strategy(benchmarks, 'gspc', baseline)

  stats = []

  # Get the list of tickers that have ARMA-GARCH models to save time by bypassing
  # the ARMA-GARCH strategy if no model exists for a ticker.
  has_arma = loader.get_arma_tickers(args)
  has_arma_tickers = has_arma['ticker'].to_list()

  # # TODO: Temporary to avoid waiting for a long time -- REMOVE WHEN DONE TESTING
  # tickers = tickers.filter(pl.col('ticker').is_in(has_arma_tickers))

  for idx, row in tickers.iter_rows():
    if row in has_arma_tickers:
      arga = ArmaGarchStrategy(AMT, INCR, COMMS, setup_log(f"ArmaGarch-{idx}"))
      data = loader.get_arma_test_data(idx, row, has_arma)
      trading_signal = arga.run(data, has_arma, row)
      # TODO: write out trading signal to a table of trading signals, leave out
      # the strategy evaluation outside of the engine because otherwise the
      # use of pre-trained model would not be possible.      
    computer = BuyHoldStrategy(AMT, INCR, COMMS, setup_log(f"BuyHold-{idx}"))
    data     = loader.get_history(idx)
    trades   = computer.compute_strategy(row, data, args)
    stat     = computer.evaluate_strategy(trades, row, baseline)
    stats.append(stat)
  market_scales = MarketScales(stats, args, benchmarks, setup_log('MarketScales'))
  market_scales.run(CON)

if __name__ == '__main__':
  start_time = time.time()
  main()
  end_time = time.time()
  print(f"This programm took {end_time - start_time} seconds to run.")