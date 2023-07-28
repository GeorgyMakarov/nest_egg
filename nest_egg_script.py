#!/usr/bin/python3

import time
import sys
import random
import matplotlib.pyplot as plt

def read_to_list(file_name):
  with open(file_name) as in_file:
    lines   = [float(line.strip()) for line in in_file]
    decimal = [round(line / 100, 5) for line in lines]
    return decimal

def default_input(prompt, default=None):
  prompt = '{} [{}]: '.format(prompt, default)
  response = input(prompt)
  if not response and default:
    return default
  else:
    return response

print("\nNote: Input data should be in percent, not decimal!\n")
try:
  bonds = read_to_list('10-yr_TBond_returns_1926-2013_pct.txt')
  stocks = read_to_list('SP500_returns_1926-2013_pct.txt')
  blend_40_50_10 = read_to_list('S-B-C_blend_1926-2013_pct.txt')
  blend_50_50 = read_to_list('S-B_blend_1926-2013_pct.txt')
  infl_rate = read_to_list('annual_infl_rate_1926-2013_pct.txt')
except IOError as e:
  print("{}. \nTerminating program.".format(e), file=sys.stderr)
  sys.exit(1)

investment_type_args = {'bonds': bonds, 'stocks': stocks, 'sb_blend': blend_50_50,
                        'sbc_blend': blend_40_50_10}

print("     stocks = SP500")
print("      bonds = 10-yr Treasury Bond")
print("   sb_blend = 50% SP500 50% TBond")
print("  sbc_blend = 40% SP500 50% TBond 10% Cash\n")
print("Press ENTER to take default value shown in [brackets]. \n")

# Get user input
invest_type = default_input("Enter investment type: (stocks, bonds, sb_blend, sbc_blend: \n",
                            'bonds').lower()
while invest_type not in investment_type_args:
  invest_type = input("Invalid investment. Enter investment type as listed in prompt: ")

start_value = default_input("Input start value of investments: \n", '2000000')
while not start_value.isdigit():
  start_value = input("Invalid input! Input integer only: ")

withdrawal = default_input("Input annual pre-tax withdrawal (today's $): \n", '80000')
while not withdrawal.isdigit():
  withdrawal = input("Invalid input! Input integer only: ")

min_years = default_input("Input minimum years in retirement: \n", '18')
while not min_years.isdigit():
  min_years = input("Invalid input! Input integer only: ")

most_likely_years = default_input("Input most likely years: \n", '25')
while not most_likely_years.isdigit():
  most_likely_years = input("Invalid input! Input integer only: ")

max_years = default_input("Input maximum years in retirement: \n", '40')
while not max_years.isdigit():
  max_years = input("Invalid input! Input integer only: ")

num_cases = default_input("Input number of cases to run: \n", '50000')
while not num_cases.isdigit():
  num_cases = input("Invalid input! Input integer only: ")

# Check for other erroneous input
if not int(min_years) < int(most_likely_years) < int(max_years) or int(max_years) > 99:
  print("\nProblem with input years.", file=sys.stderr)
  print("Requires Min < ML < Max with Max <= 99.", file=sys.stderr)
  sys.exit(1)


# Randomly determine starting year as a part of Monte Carlo engine
def montecarlo(returns):
  case_count = 0
  bankrupt_count = 0
  outcome = []
  
  while case_count < int(num_cases):
    investments = int(start_value)
    start_year  = random.randrange(0, len(returns))
    duration    = int(random.triangular(int(min_years), 
                                        int(max_years), 
                                        int(most_likely_years)))
    end_year = start_year + duration
    # Lifespan is a sample of continuous piece of historic data. Selecting an
    # interval at random is much better than selecting an individual year at
    # random as it allows to use similar history for each asset class and also
    # to catch important patterns. Catching the same behaviour for different
    # asset classes is important as financial markets have similar bull or
    # bear behaviour -- i.e. they are correlated.
    lifespan = [i for i in range(start_year, end_year)]
    bankrupt = 'no'

    lifespan_returns = []
    lifespan_infl    = []
    for i in lifespan:
      # If lifespan index is out of range (88 years or more) use % to wrap index
      # It is important to wrap index around because then index starts from the
      # beginning and catches black swans that happened in the past (like two
      # recession and great depression). Modulo operator allows to use the lists
      # as infinite loops.
      lifespan_returns.append(returns[i % len(returns)])
      lifespan_infl.append(infl_rate[i % len(infl_rate)])
    
    # Loop each year of retirement for each case run and adjust investments
    for index, i in enumerate(lifespan_returns):
      infl = lifespan_infl[index]
      if index == 0:
        withdraw_infl_adj = int(withdrawal)
      else:
        withdraw_infl_adj = int(withdraw_infl_adj * (1 + infl))
      
      investments -= withdraw_infl_adj
      investments = int(investments * (1 + i))

      if investments <= 0:
        bankrupt = 'yes'
        break
    
    if bankrupt == 'yes':
      outcome.append(0)
      bankrupt_count += 1
    else:
      outcome.append(investments)
    case_count += 1

  return outcome, bankrupt_count


# Compute probability of ruin
def bankrupt_prob(outcome, bankrupt_count):
  total = len(outcome)
  odds  = round(100 * bankrupt_count / total, 1)

  print("\nInvestment type: {}".format(invest_type))
  print("Start value: ${:,}".format(int(start_value)))
  print("Annual withdrawal: ${:,}".format(int(withdrawal)))
  print("Years in retirement (min-ml-max): {}-{}-{}".format(min_years,
                                                            most_likely_years,
                                                            max_years))
  print("Number of runs: {:,}\n".format(len(outcome)))
  print("Odds of ruin: {}%\n".format(odds))
  print("Average outcome: ${:,}".format(int(sum(outcome) / total)))
  print("Minimum outcome: ${:,}".format(min(i for i in outcome)))
  print("Maximum outcome: ${:,}".format(max(i for i in outcome)))
  
  return odds


def main():
  outcome, bankrupt_count = montecarlo(investment_type_args[invest_type])
  odds = bankrupt_prob(outcome, bankrupt_count)
  plotdata = outcome[:3000]


if __name__ == '__main__':
  start_time = time.time()
  main()
  end_time = time.time()
  duration = round(end_time - start_time, 2)
  print("\nRuntime for this program was {} seconds".format(duration))

