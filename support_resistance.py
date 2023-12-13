import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from math import floor
from datetime import date
from datetime import datetime
from datetime import timedelta
import random
import time
import sys

#### ------------------------- Custom functions -------------------------- ####
#### Test of support and resistance levels trading for a day trading bot.  ####

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

def findSupport(dt, l, n1, n2):
  for i in range(l-n1+1, l+1):
    if (dt['Low'][i] > dt['Low'][i-1]):
      return 0
  for i in range(i+1, l+n2+1):
    if (dt['Low'][i] < dt['Low'][i-1]):
      return 0
  return 1

def findResistance(dt, l, n1, n2):
  for i in range(l-n1+1, l+1):
    if (dt['High'][i] < dt['High'][i-1]):
      return 0
  for i in range(l+1, l+n2+1):
    if (dt['High'][i] > dt['High'][i-1]):
      return 0
  return 1

def findLevels(dt, n1, n2, dur):
  sr_list = []
  for row in range(n1, dur):
    if findSupport(train, row, n1, n2):
      sr_list.append((row, train['Low'][row], 'support'))
    if findResistance(train, row, n1, n2):
      sr_list.append((row, train['High'][row], 'resistance'))
  res = pd.DataFrame(sr_list)
  res.columns = ['idx', 'value', 'type']
  return res

def findLatest(dt, day):
  tmp = dt.copy()
  tmp = tmp[tmp['idx'] <= day]
  support    = 0.0
  resistance = 0.0
  if ('support' in tmp['type'].unique().tolist()):
    support = tmp[tmp['type'] == 'support']['value'].tolist()[-1]
  if ('resistance' in tmp['type'].unique().tolist()):
    resistance = tmp[tmp['type'] == 'resistance']['value'].tolist()[-1]
  return {'support': support, 'resistance': resistance}

def generateSignal(dt, sr, day):
  close = dt['Close'][day]
  result = {'day':day,
            'support':sr['support'],
            'resistance':sr['resistance'],
            'price': close,
            'action': 'hold'}
  if close < sr['support']:
    result['action']  = 'buy'
  if close > sr['resistance']:
    result['action'] = 'sell'
  return result

def sendSignal(dt, n1, n2, duration, burn_in):
  errm1  = 'Day = {}, support = {:.4f}, resistance = {:.4f}, close = {:.4f}, signal = {}'
  levels = findLevels(train, n1, n2, duration)
  trade_sign = {'day':0,
                'support': 0.0,
                'resistance':0.0,
                'price':0.0,
                'action':'hold'}
  result = []
  for day in range(n1, duration):
    sr_values = findLatest(levels, day)
    if day >= burn_in:
      trade_sign = generateSignal(dt, sr_values, day)
    result.append(trade_sign)
  result = pd.DataFrame(result)
  return result

def tradingResults(dt, init_inv, days, trans_cost):
  tmp = dt.copy()
  tmp = tmp[['day', 'price', 'action']]
  start = min(tmp['day'])
  money    = init_inv
  quantity = 0
  transaction_cost = 0
  for day in range(start, days):
    action = dt[dt['day'] == day]['action'].tolist()[0]
    price  = dt[dt['day'] == day]['price'].tolist()[0]
    if (action == 'buy' and money > price):
      affordable_qty = floor(money / price)
      purchase = round(price * affordable_qty, 2)
      money -= purchase
      quantity += affordable_qty
      transaction_cost += trans_cost
    if (action == 'sell' and quantity > 0):
      sell = round(price * quantity, 2)
      quantity = 0
      money =+ sell
      transaction_cost += trans_cost
    profit = money - init_inv - transaction_cost
    margin = profit / init_inv
  errm = 'Investment = {}, profit = {:.2f}, margin = {:.2f}%'
  print(errm.format(init_inv, profit, 100*margin)) 


#### ------------------------- Trading test -------------------------- ####

iuit_l = readYfData('IUIT.L')
train, test = splitTrainTest(iuit_l, k=0.8)


N1  = 3
N2  = 2
DUR = len(train) - N2
INIT_INV   = 1000
TRANS_COST = 5

signals = sendSignal(train, N1, N2, DUR, 15)
signals = signals[signals['day'] > 0]

tradingResults(signals, INIT_INV, DUR, TRANS_COST)


#### ----------------------------- Baseline -------------------------- ####

money   = INIT_INV
p_start = train['Close'][0]
p_end   = train['Close'][-1]
count_etf = floor(money / p_start)
purchase  = round(count_etf * p_start, 2)
money  = money - purchase
sale   = round(count_etf * p_end, 2)
money  = money + sale
profit = money - INIT_INV - TRANS_COST*2
margin = profit / INIT_INV
errm = 'Investment = {}, profit = {:.2f}, margin = {:.2f}%'
print(errm.format(INIT_INV, profit, 100*margin))
