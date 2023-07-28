#!/usr/bin/python3

import time
import sys
import random
import numpy as np
import yfinance as yf
from datetime import date
from datetime import datetime
from datetime import timedelta

NUM_CASES   = 100000
START_VALUE = 1000
MIN_HOLD = 60
MAX_HOLD = 365
CUT_OFF_DATE = date(2024, 4, 13)


def compute_median_hold(cut_off_date):
  '''Compute difference in days between cut-off date and current date'''
  today = date.today()
  if today >= cut_off_date:
    cut_off_date = cut_off_date + timedelta(days = 365)
  median_hold = cut_off_date - today
  return median_hold.days

def read_to_list(file_name):
  '''Read history of returns and convert to decimal'''
  with open(file_name) as in_file:
    lines   = [float(line.strip()) for line in in_file]
    decimal = [round(line / 100, 5) for line in lines]
    return decimal

def read_yesterday(today):
  '''Return yesterday history or zero if no history in pct'''
  t1 = today
  t2 = today - timedelta(days = 2)
  ticker = yf.download('IUIT.L', start=t2, end=t1)['Adj Close'].to_numpy()
  if len(ticker) == 2:
    return round(100 * (ticker[1] - ticker[0]) / ticker[0], 5)
  else:
    return 0.0

def montecarlo(returns, median_hold):
  '''Run Monte Carlo Simulation'''
  case_count = 0
  # Bankrupt here means final investment < initial investment. We do not use
  # NPV since deposit yield is 0.03% p.a. which makes alternative investment
  # useless
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


def bankrupt_prob(outcome, bankrupt_count, median_hold):
  total = len(outcome)
  odds  = round(100 * bankrupt_count / total, 1)

  min_out = min(i for i in outcome)
  avg_out = int(sum(outcome) / total)
  max_out = max(i for i in outcome)

  # Reverse loss and gain to be able to apply the computation of 0.95 quantile
  # and find critical range and the 95% probability that a loss will not exceed
  # certain amount
  reverse_outcome = [i - START_VALUE for i in outcome]
  reverse_outcome = [-1 * i for i in reverse_outcome]
  reverse_outcome.sort()
  q95 = int(NUM_CASES * 0.95)
  loss = reverse_outcome[q95]


  print("\nInitial investments = ${:,}".format(START_VALUE))
  print("Days hold (min-med-max): {}-{}-{}\n".format(MIN_HOLD, median_hold, MAX_HOLD))
  print("Odds of ruin: {}%".format(odds))
  print("Minimum outcome: ${:,}".format(min_out))
  print("Average outcome: ${:,}".format(avg_out))
  print("Maximum outcome: ${:,}".format(max_out))
  print("Earnings at risk: ${:,}".format(loss))

  return odds


def main():
  median_hold = compute_median_hold(CUT_OFF_DATE)
  etf_history = read_to_list('etf_returns.txt')
  etf_yesterday = read_yesterday(date.today())
  hist_file = open("etf_returns.txt", "a")
  hist_file.writelines(str(etf_yesterday)+"\n")
  hist_file.close()
  etf_history.append(round(etf_yesterday / 100, 5))
  
  # Compute outcome and probs
  outcome, bankrupt_count = montecarlo(etf_history, median_hold)
  odds = bankrupt_prob(outcome, bankrupt_count, median_hold)


if __name__ == '__main__':
  start_time = time.time()
  main()
  end_time = time.time()
  duration = round(end_time - start_time, 2)
  print("\nRuntime for this program was {} seconds".format(duration))
