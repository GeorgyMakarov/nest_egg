import sys
import time
import random
import numpy as np
import pandas as pd
import seaborn as sns
import yfinance as yf
import matplotlib.pyplot as plt
from math import floor
from datetime import date
from datetime import datetime
from datetime import timedelta
from itertools import product


def readYfData(idx):
  start_date = datetime(2016, 1, 1)
  end_date   = date.today()
  etf_df = yf.download(idx, start=start_date, end=end_date)
  return etf_df

def splitTrainTest(dt, k=0.8):
  split_point = int(dt.shape[0] * k)
  train = dt.copy()
  test  = dt.copy()
  train = train[:split_point]
  test  = test[split_point:]
  return train, test


iuit_l = readYfData('IUIT.L')
train, test = splitTrainTest(iuit_l, k=0.9)


def randomWalk(n_periods, start, r_state):
  np.random.seed(r_state)
  d = np.random.normal(loc=0.0, scale=0.05, size=n_periods)
  d = np.round(d, 4)
  res = []
  for idx, i in enumerate(d):
    if idx == 0:
      res.append(round(start * (1 + i), 4))
    else:
      res.append(round(res[idx - 1] * (1 + i), 4))
  return res

def computeReturns(prices):
  diffs   = np.diff(prices).tolist()
  prices  = np.delete(prices, len(prices) - 1).tolist()
  returns = [round(a / b, 5) for a,b in zip(diffs, prices)]
  returns = [0.00000] + returns
  return returns

def computeRsi(returns):
  up_close   = len(list(filter(lambda x: (x > 0), returns)))
  down_close = len(list(filter(lambda x: (x < 0), returns)))
  if down_close == 0:
    down_close = 1
  rs_val = round(up_close / down_close, 2)
  rsi    = round(100 - (100 / (1 + rs_val)), 2)
  return rsi

def computeRsiList(returns, burn_in, look_back):
  rsi = []
  first_rsi = 0.0
  for day in range(burn_in, len(returns)):
    ytd_returns = returns[0:day]
    day_rsi = computeRsi(ytd_returns[len(ytd_returns) - look_back:len(ytd_returns)])
    rsi.append(day_rsi)
    if day == burn_in:
      first_rsi == day_rsi
  if first_rsi >= 70:
    first_rsi = 50
  elif first_rsi <= 30:
    first_rsi = 50
  prefix_rsi = [first_rsi for x in range(burn_in)]
  res = prefix_rsi + rsi
  return res

def takeActions(rsi, oversold, overbought):
  actions = []
  for i in rsi:
    if i <= oversold:
      actions.append('buy')
    elif i >= overbought:
      actions.append('sell')
    else:
      actions.append('hold')
  return actions

def performTrade(prices, actions, budget, cost, entry, k):
  """
  This function performs trade if multiple conditions where met.
  prices  -- list of prices
  actions -- list of actions
  budget  -- initial investment
  cost    -- cost of 1 transaction
  entry   -- day when to enter the market, must be > burn in period
  k -- minimum n of items purchased condition, not to go below zero, trainable
  """
  cash    = budget
  stock   = 0
  profit  = 0
  memory  = []

  for i in range(entry, len(prices)):
    price  = prices[i]
    action = actions[i]
    if i == entry:
      action = 'buy'
    elif i == len(prices) - 1:
      action = 'sell'
  
    if action == 'buy':
      can_spend = cash - cost ## purchase - cost not to go into neg balance
      can_buy   = floor(can_spend / price)
      if can_buy >= k:
        pay = round(can_buy * price, 2) + cost
        cash    -= pay
        stock   += can_buy
    elif action == 'sell':
      if stock >= k:
        sale = round(stock * price, 2) - cost
        cash += sale
        stock = 0
    
    history = {'day': i, 'signal': action, 'price': price, 
               'stock': stock, 'cash': cash}
    memory.append(history)
  profit = round(cash, 2)
  return profit, memory

def trainRsiModel(dt, burn_in, look_back, lower, higher, init, cost, min_trade, days):
  """
  Trains trainable parameters for maximum profit using RSI. Trainable parameters:
  burn_in -- time of entry
  look_back -- number of days to take into considerations for RSI computation
  lower -- oversold RSI
  higher -- overbought RSI
  min_trade -- minimal trade volume
  """
  params = {'burn in': burn_in, 
            'look back': look_back, 
            'lower': lower, 
            'higher': higher, 
            'min trade': min_trade,
            'cash': 0.0}
  index  = [x for x in range(days)]
  prices = dt['Close'].tolist()
  returns = computeReturns(prices)
  rsi     = computeRsiList(returns, burn_in, look_back)
  actions = takeActions(rsi, lower, higher)
  profit, mem = performTrade(prices, actions, init, cost, burn_in, min_trade)
  params['cash'] = profit
  return params



N         = train.shape[0]
BURN_IN   = 15
LOOK_BACK = 5
INITIAL   = 1000
COST      = 5
O_SOLD    = 30 ## oversold RSI
O_BOUGHT  = 70 ## overbought RSI
MIN_TRADE = 10

index   = [x for x in range(N)]
prices  = train['Close'].tolist()
returns = computeReturns(prices)
rsi     = computeRsiList(returns, BURN_IN, LOOK_BACK)
actions = takeActions(rsi, O_SOLD, O_BOUGHT)
profit, mem = performTrade(prices, actions, INITIAL, COST, BURN_IN, MIN_TRADE)
print('RSI computed cash at exit: {}'.format(profit))

## Non-machine learning baseline for train
entry_price = round(prices[BURN_IN], 5)
entry_qty   = floor((INITIAL - COST) / entry_price)
entry_cash  = round(INITIAL - entry_price * entry_qty - COST, 2)
exit_price  = round(prices[len(prices)- 1], 5)
exit_cash   = round(entry_cash + exit_price * entry_qty - COST, 2)
print('No machine learning baseline: {:.2f}'.format(exit_cash))


p_area = {'burn in': [5, 10, 15, 20, 25], 
          'look back': [5, 10, 15, 20, 25, 30, 35, 40, 45, 50], 
          'lower':[10, 15, 20, 25, 30, 35, 40, 45],
          'higher': [55, 60, 65, 70, 75, 80, 85, 90], 
          'min trade': [5, 10, 15, 20, 25]}
param_grid = product(p_area['burn in'], 
                     p_area['look back'], 
                     p_area['lower'], 
                     p_area['higher'], 
                     p_area['min trade'])

param_history = []
i    = 0
errm = 'Step {}: burn = {}, look back = {}, lower = {}, higher = {}, trade = {}'
for item in param_grid:
  i += 1
  burn_in_par   = item[0]
  look_back_par = item[1]
  lower_par     = item[2]
  higher_par    = item[3]
  min_trade_par = item[4]
  
  if i % 5000 == 0:
    print(errm.format(i, burn_in_par, look_back_par, lower_par, 
                      higher_par, min_trade_par))
  step = trainRsiModel(train, burn_in_par, look_back_par, lower_par, higher_par,
                       INITIAL, COST, min_trade_par, N)
  param_history.append(step)

temp = pd.DataFrame(param_history)
temp.sort_values('cash', ascending=False, inplace=True)
temp.head(10)


N         = test.shape[0]
BURN_IN   = 25
LOOK_BACK = 20
INITIAL   = 1000
COST      = 5
O_SOLD    = 45 ## oversold RSI
O_BOUGHT  = 80 ## overbought RSI
MIN_TRADE = 20

index   = [x for x in range(N)]
prices  = test['Close'].tolist()
returns = computeReturns(prices)
rsi     = computeRsiList(returns, BURN_IN, LOOK_BACK)
actions = takeActions(rsi, O_SOLD, O_BOUGHT)
profit, mem = performTrade(prices, actions, INITIAL, COST, BURN_IN, MIN_TRADE)
print('RSI computed cash at exit: {}'.format(profit))

## Non-machine learning baseline for train
entry_price = round(prices[BURN_IN], 5)
entry_qty   = floor((INITIAL - COST) / entry_price)
entry_cash  = round(INITIAL - entry_price * entry_qty - COST, 2)
exit_price  = round(prices[len(prices)- 1], 5)
exit_cash   = round(entry_cash + exit_price * entry_qty - COST, 2)
print('No machine learning baseline: {:.2f}'.format(exit_cash))