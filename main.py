import time
from src.argparser import ArgParser
from src.setup_logger import setup_log
from src.data_loader import DataLoader
from src.market_scales import MarketScales
from src.buy_hold_strategy import BuyHoldStrategy

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

  for idx, row in tickers.iter_rows():     
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