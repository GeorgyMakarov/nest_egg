import random
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import statsmodels.api as sm

from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error
from pandas.plotting import autocorrelation_plot
from statsmodels.tsa.stattools import pacf
from statsmodels.tsa.stattools import acf

from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf

from math import sqrt
from math import floor
from scipy import stats
from datetime import date
from datetime import datetime

from itertools import product

def readYfData(idx):
  start_date = datetime(2016, 1, 1)
  end_date   = date.today()
  etf_df = yf.download(idx, start=start_date, end=end_date)
  return etf_df

iuit_l = readYfData('IUIT.L')

def splitTrainTest(prices, k=0.8):
  split_point = int(len(prices) * k)
  train = prices.copy()
  test  = prices.copy()
  train = train[:split_point]
  test  = test[split_point:]
  return train, test

def computeReturns(prices):
  diffs   = np.diff(prices).tolist()
  prices  = np.delete(prices, len(prices) - 1).tolist()
  returns = [round(a / b, 5) for a,b in zip(diffs, prices)]
  returns = [0.00000] + returns
  return returns

def computeDiffs(prices):
  diffs = np.diff(prices).tolist()
  diffs = [0.000] + diffs
  return diffs

N       = 100
INITIAL = 1000
COST    = 5
DIFF    = 5 ## how many days of differencing to check for correlation

prices  = iuit_l['Close'].tolist()[-N:]
index   = [x for x in range(len(prices))]
train, test = splitTrainTest(prices, k=0.80)
returns = computeReturns(train)
differs = computeDiffs(train)
pacf_value = findARPvalue(train, 10)

# Straight growing line of cumulative sum shows that there is linear relationship
# in autoregression
cumul_prices = np.cumsum(prices)
plt.plot(cumul_prices, color='grey')
plt.show()

# The model may follow an ARIMA(p, d, 0) model if ACF is exponentially decaying
# or sinusoidal and PACF has a significant spike at lag p but none beyond lag p
plot_acf(pd.Series(differs))
plot_pacf(pd.Series(differs))

cor_lst = []
day_lst = []

for di in range(1, DIFF + 1):
  train_x = train[0:len(train) - di]
  train_y = train[di:len(train)]
  corr_xy = np.round(100 * np.corrcoef(train_x, train_y)[0][1], 2)
  cor_lst.append(corr_xy)
  day_lst.append(di)

pd.DataFrame({'difference':day_lst, 'impact': cor_lst})

plt.scatter(train_x, train_y)
plt.show()

model = ARIMA(train, order=(1, 1, 1))
model_fit = model.fit()
print(model_fit.summary())

mod = sm.tsa.statespace.SARIMAX(train, trend='c', order=(1, 1, 1))
res = mod.fit(disp=False)
print(res.summary())

log_train = np.log(train).tolist()
log_diffs = computeDiffs(log_train)
index     = [x for x in range(len(log_train))]

fig, ax = plt.subplots(1, 2, figsize=(15, 4))
ax[0].plot(index, log_train, '-')
ax[0].set(title='Log of stock prices')

ax[1].plot(index, log_diffs, '-')
ax[1].hlines(0, index[0], 'r')
ax[1].set(title='Difference of log prices')

# The data may follow an ARIMA(0, d, q) model if the ACF and the PACF plots of
# the differenced data show the following patterns:
# - ACF plot has significant spike at lag = 4, but not beyound that lag
# - PACF is exponentially decaying or sinusoidal
fig, ax = plt.subplots(1, 2, figsize=(15, 4))
fig = plot_acf(pd.Series(log_diffs), lags=20, ax=ax[0])
fig = plot_pacf(pd.Series(log_diffs), lags=20, ax=ax[1])

ar  = 1
ma  = (1, 0, 0, 1)
mod = sm.tsa.statespace.SARIMAX(train, trend='c', order=(ar, 1, ma))
res = mod.fit()
print(res.summary())

# The best model so far, that has low p-values and good test results
# This model allows to take effect in an additive way
ar  = 0
ma  = (0, 0, 0, 1) ## This way we exclude the first 3 lags and use 4th lag only
mod = sm.tsa.statespace.SARIMAX(train, trend='c', order=(ar, 1, ma))
res = mod.fit(disp=False)
print(res.summary())

# The best model on the log data
ar  = 0
ma  = (0, 0, 0, 1)
mod = sm.tsa.statespace.SARIMAX(log_train, trend='c', order=(ar, 1, ma))
res = mod.fit(disp=False)
print(res.summary())

# Fitting the model on the training data and then applying it to post-estimation
# to be able to reproduce dynamic forecasting
ar  = 0
ma  = (0, 0, 0, 1) ## This way we exclude the first 3 lags and use 4th lag only
mod = sm.tsa.statespace.SARIMAX(train, trend='c', order=(ar, 1, ma))
fit_res = mod.fit(disp=False)

mod = sm.tsa.statespace.SARIMAX(prices, trend='c', order=(ar, 1, ma))
res = mod.filter(fit_res.params)

# In-sample one-step-ahead prediction
predict    = res.get_prediction()
predict_ci = predict.conf_int()

# Dynamic predictions for test dataset using training parameters
predict_dy    = res.get_prediction(dynamic=81)
predict_dy_ci = predict_dy.conf_int()

yhat_onestep = predict.predicted_mean.tolist()
yhat_dynamic = predict_dy.predicted_mean.tolist()
yhat_onestep[0] = prices[0]
yhat_dynamic[0] = prices[0]

index   = [x for x in range(len(prices))]
plt.plot(index[80:], prices[80:], color='grey', label='actual', marker='o', linestyle='')
plt.plot(index[80:], yhat_onestep[80:], color='green', label='one-step', linestyle='dashed')
plt.plot(index[80:], yhat_dynamic[80:], color='red', label='dynamic', linestyle='solid')
plt.legend()
plt.show()

# Mean squared errors for one-step and dynamic forecast for 20 steps ahead
onestep = yhat_onestep[80:]
dynamic = yhat_dynamic[80:]
mae_onestep = mean_absolute_error(y_true=test, y_pred=onestep)
mae_dynamic = mean_absolute_error(y_true=test, y_pred=dynamic)
print('MAE: one-step = {:.2f}, dynamic 20 steps = {:.2f}'.format(mae_onestep, mae_dynamic))