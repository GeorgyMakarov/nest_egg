import random
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error

from math import sqrt
from math import floor
from scipy import stats
from datetime import date
from datetime import datetime

from itertools import product


def computeReturns(prices):
  diffs   = np.diff(prices).tolist()
  prices  = np.delete(prices, len(prices) - 1).tolist()
  returns = [round(a / b, 5) for a,b in zip(diffs, prices)]
  returns = [0.00000] + returns
  return returns

def splitTrainTest(prices, k=0.8):
  split_point = int(len(prices) * k)
  train = prices.copy()
  test  = prices.copy()
  train = train[:split_point]
  test  = test[split_point:]
  return train, test

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


prices  = randomWalk(2011, 4.5756, 42)
index   = [x for x in range(len(prices))]
returns = computeReturns(prices)
train, test = splitTrainTest(prices)
adf_test = adfuller(prices, autolag='AIC')[1]
print('ADF test p-value: {:.2f}, p > 0.05 = non-stationary'.format(adf_test))


train_x = prices[0:len(prices) - 1]
train_y = prices[1:len(prices)]
plt.scatter(train_x, train_y)
plt.show()


model = ARIMA(train, order=(1, 1, 0))
model_fit = model.fit()
print(model_fit.summary())


residuals = pd.DataFrame(model_fit.resid)
print(residuals.describe())


history     = train.copy()
predictions = []
for day in range(len(test)):
  model = ARIMA(history, order=(1, 1, 0))
  model_fit = model.fit()
  output = model_fit.forecast()
  y_hat  = output[0]
  y_act  = test[day]
  predictions.append(y_hat)
  history.append(y_act)


rmse = sqrt(mean_squared_error(test, predictions))
print('Mean squared error = {:.2f}'.format(rmse))