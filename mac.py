class mac(strategy):
  def __init__(self, bars, events, short_window=100, long_window=400):
    self.bars = bars
    self.symbol_list = self.bars.symbol_list
    self.events = events
    self.short_window = short_window
    self.long_window = long_window
    self.bought = self._calculate_initial_bought()

  def _calculate_initial_bought(self):
    bought = {}
    for s in self.symbol_list:
      bought[s] = 'out'
    return bought

  def calculate_signals(self, event):
    if event.type == 'market':
      for symbol in self.symbol_list:
        bars = self.bars.get_latest_bars_values(symbol, "close", N=self.long_window)               

        if bars is not None and bars != []:
          short_sma = np.mean(bars[-self.short_window:])
          long_sma = np.mean(bars[-self.long_window:])

          dt = self.bars.get_latest_bar_datetime(symbol)
          sig_dir = ""
          strength = 1.0
          strategy_id = 1

          if short_sma > long_sma and self.bought[symbol] == "out":
            sig_dir = 'long'
            signal = signal_event(strategy_id, symbol, dt, sig_dir, strength)
            self.events.put(signal)
            self.bought[symbol] = 'long'

          elif short_sma < long_sma and self.bought[symbol] == "long":
            sig_dir = 'exit'
            signal = signal_event(strategy_id, symbol, dt, sig_dir, strength)
            self.events.put(signal)
            self.bought[symbol] = 'out'


if __name__ == "__main__":
  csv_dir = '/content/'
  symbol_list = ['IUIT_L']
  initial_capital = 100000.0
  start_date = datetime.datetime(2021,11,19,0,0,0)
  heartbeat = 0.0

  backtest = backtest(csv_dir, 
                      symbol_list, 
                      initial_capital, 
                      heartbeat,
                      start_date,
                      historic_csv_data_handler, 
                      simulated_execution_handler, 
                      portfolio, 
                      mac)
  
  backtest.simulate_trading()