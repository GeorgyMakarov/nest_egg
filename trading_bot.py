import numpy as np
import pandas as pd
import yfinance as yf
from datetime import date
from datetime import datetime
from datetime import timedelta
import random
import time
import sys


LOOKBACK_PERIOD = 15
NUM_CASES    = 100000
START_VALUE  = 1000
MIN_HOLD     = 60
MAX_HOLD     = 365
CUT_OFF_DATE = date(2024, 4, 13)


def compute_returns(prices):
  differences = np.diff(prices).tolist()
  prices = np.delete(prices, len(prices) - 1)
  prices = prices.tolist()
  returns = [round(a / b, 5) for a, b in zip(differences, prices)]
  returns = [0.00000] + returns
  return returns


def compute_rsi(returns):
  up_close   = len(list(filter(lambda x: (x > 0), returns)))
  down_close = len(list(filter(lambda x: (x < 0), returns)))
  if down_close == 0:
    down_close = 1
  rs_val = round(up_close / down_close, 2)
  rsi    = round(100 - (100 / (1 + rs_val)), 2)
  return rsi


def take_action(rsi):
  if rsi <= 30:
    return 'buy' 
  elif rsi >= 70:
    return 'sell'
  else:
    return 'hold'


def compute_median_hold(cut_off_date):
  today = date.today()
  if today > cut_off_date:
    cut_off_date = cut_off_date + timedelta(days = 365)
  median_hold = cut_off_date - today
  return median_hold.days
  

def montecarlo(returns, median_hold):
  case_count = 0
  bankrupt_count = 0
  outcome = []
  while case_count < int(NUM_CASES):
    investments = START_VALUE
    start_day = random.randrange(0, len(returns))
    duration  = int(random.triangular(MIN_HOLD, MAX_HOLD, int(median_hold)))
    end_day   = start_day + duration
    lifespan  = [i for i in range(start_day, end_day)]
    bankrupt  = 'no'
    lifespan_returns = []
    for i in lifespan:
      lifespan_returns.append(returns[i % len(returns)])
    for index, i in enumerate(lifespan_returns):
      investments = int(investments * (1 + i))
    if investments < START_VALUE:
      bankrupt = 'yes'
      bankrupt_count += 1
    outcome.append(investments)
    case_count += 1
  return outcome, bankrupt_count


def bankrupt_prob(outcome, bankrupt_count, median_hold, action):
  total = len(outcome)
  odds  = round(100 * bankrupt_count / total, 1)
  min_out = min(i for i in outcome)
  avg_out = int(sum(outcome) / total)
  max_out = max(i for i in outcome)
  reverse_outcome = [i - START_VALUE for i in outcome]
  reverse_outcome = [-1 * i for i in reverse_outcome]
  reverse_outcome.sort()
  q95 = int(NUM_CASES * 0.95)
  loss = reverse_outcome[q95]
  print("\nInitial investments = ${:,}".format(START_VALUE))
  print("Days hold (min-med-max): {}-{}-{}\n".format(MIN_HOLD, median_hold, MAX_HOLD))
  print("Odds of ruin: {}%".format(odds))
  print("Min outcome: ${:,}".format(min_out))
  print("Avg outcome: ${:,}".format(avg_out))
  print("Max outcome: ${:,}".format(max_out))
  print("Earnings at risk: ${:,}".format(loss))
  print("Action: {}".format(action))
  return odds


def read_etf_data(etf):
  start_date = datetime(2016, 1, 1)
  end_date   = date.today()
  etf_df = yf.download(etf, start=start_date, end=end_date)
  return etf_df

def main():
  etf = read_etf_data('IUIT.L')
  returns = compute_returns(etf['Adj Close'].to_numpy())
  rsi     = compute_rsi(returns[len(returns) - LOOKBACK_PERIOD:len(returns)])
  action  = take_action(rsi)

  median_hold = compute_median_hold(CUT_OFF_DATE)
  outcome, bankrupt_count = montecarlo(returns, median_hold)
  odds = bankrupt_prob(outcome, bankrupt_count, median_hold, action)


if __name__ == '__main__':
  start_time = time.time()
  main()
  end_time = time.time()
  duration = round(end_time - start_time, 2)
  print("\nRuntime for this programs was {} seconds".format(duration))
