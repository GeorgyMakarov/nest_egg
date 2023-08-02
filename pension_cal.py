import time
import sys
import random
import pandas as pd

SAVINGS = [1200, 2400, 3600, 4800, 6000, 7200, 8400, 9600, 10800, 12000, 13200, 16800]
START_SAVINGS = 10000
NUM_CASES     = 100000
CURRENT_AGE   = 40
MIN_YR = 16
MAX_YR = 35
MED_YR = 22
WITHDRAWAL = 45000

def read_to_list(file_name):
  with open(file_name) as in_file:
    lines = [float(line.strip()) for line in in_file]
    decimal = [round(line / 100, 5) for line in lines]
    return decimal


def montecarlo(returns, inflation, saving):
  case_count = 0
  bankrupt_count = 0
  outcome = []

  while case_count < int(NUM_CASES):
    # Part I: simulation of savings during work time
    savings = int(START_SAVINGS)

    # Start year of savings is different from the same of investments as those
    # activities happen in a different periods (i.e. investments satrt after
    # retirement)
    start_year = random.randrange(0, len(returns))
    duration   = 65 - CURRENT_AGE
    end_year   = start_year + duration

    worktime = [i for i in range(start_year, end_year)]
    worktime_returns   = []
    worktime_inflation = []

    for i in worktime:
      worktime_returns.append(returns[i % len(returns)])
      worktime_inflation.append(inflation[i % len(inflation)])

    for index, i in enumerate(worktime_returns):
      infl = worktime_inflation[index]
      if index == 0:
        addition_inf_adj = int(saving)
      else:
        addition_inf_adj = int(addition_inf_adj * (1 + infl))
      # Try without inflation
      addition_inf_adj = int(saving)
      savings += addition_inf_adj
      savings = int(savings * (1 + i))

    # Part II: simulation of retirement evolution
    start_year  = random.randrange(0, len(returns))
    duration    = int(random.triangular(MIN_YR, MAX_YR, MED_YR))
    end_year    = start_year + duration
    investments = savings

    lifespan = [i for i in range(start_year, end_year)]
    bankrupt = 'no'

    lifespan_returns = []
    lifespan_infl = []

    for i in lifespan:
      lifespan_returns.append(returns[i % len(returns)])
      lifespan_infl.append(inflation[i % len(inflation)])

    for index, i in enumerate(lifespan_returns):
      infl = lifespan_infl[index]
      if index == 0:
        withdraw_infl_adj = int(WITHDRAWAL)
      else:
        withdraw_infl_adj = int(withdraw_infl_adj * (1 + infl))
      investments -= withdraw_infl_adj
      investmetns = int(investments * (1 + i))

      if investments <= 0:
        bankrupt = 'yes'
        break
    if bankrupt == 'yes':
      outcome.append(0)
      bankrupt_count += 1
    else:
      outcome.append(investments)
    case_count += 1
  return outcome, bankrupt_count, savings


def bankrupt_prob(outcome, bankrupt_count, saving, start_value):
  total = len(outcome)
  odds  = round(100 * bankrupt_count / total, 1)

  result = {'Savings': int(saving),
            'Start value': int(start_value),
            'Odds': odds,
            'Min': min(i for i in outcome),
            'Avg': int(sum(outcome) / total),
            'Max': max(i for i in outcome)}
  
  return result


def main():
  returns   = read_to_list('SP500_returns_1926-2023_pct.txt')
  inflation = read_to_list('annual_infl_rate_1926-2023_pct.txt')
  results = []
  for saving in SAVINGS:
    outcome, bankrupt_count, start_value = montecarlo(returns, inflation, saving)
    odds = bankrupt_prob(outcome, bankrupt_count, saving, start_value)
    results.append(odds)
  output_dt = pd.DataFrame(results)
  print(output_dt)


if __name__ == '__main__':
  start_time = time.time()
  main()
  end_time = time.time()
  duration = round(end_time - start_time, 2)
  print("\nRuntime for this program was {} seconds".format(duration))
