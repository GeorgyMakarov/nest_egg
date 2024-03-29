# -*- coding: utf-8 -*-
"""way_to_forecast.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1VChnYf42Sf-gYzJXTh-yNoCy0M9AWr1g
"""

import random
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import statsmodels.api as sm

from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.metrics import confusion_matrix
from statsmodels.tsa.stattools import pacf
from statsmodels.tsa.stattools import acf

from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.diagnostic import kstest_normal
from statsmodels.stats.diagnostic import het_breuschpagan

from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf

from sklearn.preprocessing import StandardScaler

from math import sqrt
from math import floor
from scipy import stats
from datetime import date
from datetime import datetime

from itertools import product
from itertools import groupby

!pip install arch
from arch import arch_model

from scipy import optimize
from scipy.optimize import minimize

import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning
warnings.simplefilter('ignore', ConvergenceWarning)
warnings.filterwarnings('ignore', message="RuntimeWarning: Values in x were outside bounds during a minimize step, clipping to bounds")
warnings.filterwarnings('ignore', message="Values in x were outside bounds during a minimize step, clipping to bounds")

def readYfData(idx):
  start_date = datetime(2016, 1, 1)
  end_date   = date.today()
  etf_df = yf.download(idx, start=start_date, end=end_date)
  return etf_df

def computeReturns(prices):
  diffs   = np.diff(prices).tolist()
  prices  = np.delete(prices, len(prices) - 1).tolist()
  returns = [round(a / b, 5) for a,b in zip(diffs, prices)]
  returns = [0.00000] + returns
  return returns

def removeOutliers(returns, sigma_limit):
  scaler = StandardScaler()
  scaled_log_returns = scaler.fit_transform(np.array(returns).reshape(-1, 1))
  scaled_outliers = [i for i, x in enumerate(scaled_log_returns)\
                     if abs(x) > sigma_limit]
  rep = np.median(returns)
  log_returns = [rep if i in scaled_outliers else x for\
                 i, x in enumerate(returns)]
  return log_returns

def computeEpsilon(c, phi, theta, r):
  """
  This function computes epsilon for using the formula for an ARMA(p, q) process
  with intercept and returns an array of epsilons.
  c - coefficient of intercept
  phi - list of phi coefficients of length p
  theta - list of theta coefficients of length q
  r - an array of returns
  """
  T = len(r)
  eps = np.zeros(T)
  for t in range(T):
    if t < len(phi):
      eps[t] = r[t] - np.mean(r)
    else:
      ar_part = np.sum(np.array([phi[i] * r[t - 1 - i] for i in range(len(phi))], dtype=np.float64))
      ma_part = np.sum(np.array([theta[i] * eps[t - 1- i] for i in range(len(theta))], dtype=np.float64))
      eps[t]  = r[t] - c - ar_part - ma_part
  return eps

def getSigma2(omega, alpha, beta, gamma, r, eps):
  T = len(eps)
  sigma2 = np.zeros(T)
  if (1 - alpha - beta) == 0:
    sigma2[0] = omega / (1 - 0.9999999999999998)
  else:
    sigma2[0] = omega / (1 - alpha - beta)
  for t in range(1, T):
    sigma2[t] = omega + alpha * eps[t - 1] ** 2 + beta * sigma2[t - 1]
  return sigma2

def llhNormal(params, p, q, r):
  # We need constant, phi and theta for epsilon estimation in ARMA process
  c     = params[0]
  phi   = params[1:p+1]
  theta = params[p+1:p+q+1]
  # We need omega, alpha and beta params for GARCH process
  omega, alpha, beta = params[-3:]
  gamma = None
  et = computeEpsilon(c, phi, theta, r)
  sigma2 = getSigma2(omega, alpha, beta, gamma, r, et)
  if any(sigma2 < 0):
    sigma2[sigma2 < 0] = -1 * sigma2[sigma2 < 0]
  llh    = -0.5 * (np.log(2*np.pi) + np.log(sigma2) + et**2 / (2*sigma2))
  neg_llh   = -llh
  total_llh = np.sum(neg_llh)
  return total_llh

def cons0(params, p, q, r):
  alpha, beta = params[-2:]
  return 1.0 - np.finfo(np.float64).eps - alpha - beta

def cons1(params, p, q, r):
  return 1.0 - np.sum(params[1:p+1]) - np.finfo(np.float64).eps

def trainModel(r, p, q):
  np.seterr(divide='ignore', invalid='ignore', over='ignore')
  e = np.finfo(np.float64).eps
  bounds = [(-10*np.abs(np.mean(r)), 10*np.abs(np.mean(r)))] + \
           [(-0.999999, 0.999999) for _ in range(p + q)] + \
           [(e, 2 * np.var(r))]
  alpha_bounds, beta_bounds = [(e, 1.0 - e) for _ in range(2)]
  initial_params = [0.001 for _ in range(p + q + 1)]
  initial_params = initial_params + [0.001, 0.1, 0.8]
  bounds = bounds + [alpha_bounds, beta_bounds]
  min_func = llhNormal
  eqcons   = []
  ieqcons  = [cons0, cons1]
  result = optimize.fmin_slsqp(func = min_func,
                               x0   = initial_params,
                               ieqcons = ieqcons,
                               eqcons  = eqcons,
                               bounds  = bounds,
                               epsilon = 1e-6,
                               acc     = 1e-7,
                               full_output = True,
                               iprint  = 0,
                               args    = (p, q, r),
                               iter    = 300)
  return result

def simultaneousLlh(r, max_p, max_q):
  orders   = list(product(np.arange(max_p + 1), np.arange(max_q + 1)))
  best_aic = np.inf
  for order in orders:
    p = order[0]
    q = order[1]
    result = trainModel(r, p, q)
    current_aic = 2 * result[1] + 2 * len(result[0])
    if current_aic < best_aic:
      best_aic = current_aic
      best_p, best_q = p, q
      best_params = result[0]
  return best_p, best_q

def trainArma(r, p, q):
  arima_model = sm.tsa.statespace.SARIMAX(r,
                                          trend = 'c',
                                          order = (p, 0, q),
                                          enforce_stationarity=False,
                                          enforce_invertibility=False)
  arima_result = arima_model.fit(disp=False)
  arima_resids = arima_result.resid
  return arima_result, arima_resids

def trainGarch(scaled_traning):
  archm = arch_model(scaled_training,
                     mean = 'zero',
                     vol  = 'garch',
                     p    = 1,
                     q    = 1,
                     dist = 'Normal')
  gjr = archm.fit(update_freq=100, disp=False)
  return gjr

def predictArma(arima_result, look_ahead, r):
  predicted_mu = arima_result.forecast(steps=look_ahead).tolist()
  q25 = np.quantile(r, 0.25)
  q75 = np.quantile(r, 0.75)
  iqr = q75 - q25
  lower  = q25 - 1.5*iqr
  higher = q75 + 1.5*iqr

  new_predicted_mu = []

  for mu in predicted_mu:
    new_mu = mu
    if mu < lower:
      new_mu = q25
    if mu > higher:
      new_mu = q75
    new_predicted_mu.append(new_mu)

  predicted_mu = new_predicted_mu.copy()
  return predicted_mu

def findDirection(predicted_mu, predicted_et):
  # Adjust the sign of volatility using the direction defined by ARIMA model
  mu0 = predicted_mu[0]
  direction = [0 if mu0 == 0 else 1 if mu0 > 0 else -1] + \
              [0 if x == 0 else 1 if x > 0 else -1
               for x in np.diff(predicted_mu).tolist()]

  predicted_et = [x * y for x,y in zip(direction, predicted_et)]

  # If predicted_et is bad (i.e. super-high volatility, maybe 1.5 times higher)
  # then replace the volatility with zero to minimize the risk of drawing the
  # return into wrong direction
  #training_vol = np.round(np.std(training) * np.sqrt(len(training)), 5)
  training_vol = 0.03
  new_predicted_et = []
  for et in predicted_et:
    new_et = et
    abs_et = np.round(abs(et), 5)
    if abs_et > training_vol:
      new_et = 0.0
    new_predicted_et.append(new_et)

  predicted_et = new_predicted_et.copy()

  return predicted_et

iuit_l = readYfData('IUIT.L')

# Define constants to control trading
ENTRY_POINT =   21.559999 # Price of 19-11-2021 when we started trading
ENTRY_IDX   = 1489        # Index of 19-11-2021 when we started trading
LOOK_BACK   =  365        # Number of days to look back when building a model
LOOK_AHEAD  =    1        # Number of days to forecast ahead
BURN_IN     =   30        # Burn in period to allow RSI to stabilize
OUTLIER_SIG =  3.3        # Outlier sigma to cut-off outliers
INITIAL_INV = 1000        # Initial investment amount
TRANS_COST  =    8        # Cost per one transaction
IDLE_COST   =  120        # Cost if now transactions in 365 days
MIN_PURCHAS =   10        # Minimal number of stocks to buy in a batch
MAX_P       =    3
MAX_Q       =    3

prices      = iuit_l['Close'].tolist()
log_prices  = np.log(prices).tolist()
returns     = computeReturns(log_prices)
price_trend = pd.Series(prices).rolling(100).mean()

lows  = iuit_l['Low']
highs = iuit_l['High']

# We use standardized log returns to detect outliers since other methods like
# IQR are too sensitive to outliers and identify too many of them in the series
# which might lead to loosing some valuable information.
returns = removeOutliers(returns, OUTLIER_SIG)
n_steps  = len(returns) - (ENTRY_IDX + LOOK_AHEAD)
last_idx = len(returns) + 1 - LOOK_AHEAD

steps = 0

cash_history = []
invt_history = []

testing_history = []
forecast_history = []
volatility_history = []

cash = INITIAL_INV
inventory = 0

for step in range(ENTRY_IDX, last_idx):
  window_ret = returns[step - LOOK_BACK:step + LOOK_AHEAD]
  training   = window_ret[:LOOK_BACK]
  testing    = window_ret[LOOK_BACK:]

  p, q = simultaneousLlh(training, MAX_P, MAX_Q)
  arima_result, arima_resids = trainArma(training, p, q)

  scaler = StandardScaler()
  scaled_training = scaler.fit_transform(np.array(arima_resids).reshape(-1, 1))
  gjr = trainGarch(scaled_training)

  predicted_mu = predictArma(arima_result, len(testing), training)
  predicted_et = gjr.forecast(horizon=len(testing)).variance
  predicted_et = scaler.inverse_transform(predicted_et).tolist()[0]
  volatil_fc   = predicted_et.copy()
  predicted_et = findDirection(predicted_mu, predicted_et)

  if (p == 0 and q == 0):
    y_hat = predicted_mu.copy()
  else:
    y_hat = [mu + et for mu, et in zip(predicted_mu, predicted_et)]

  today_price    = prices[step]
  tomorrow_price = today_price * (1 + y_hat[0])

  if today_price < tomorrow_price:
    affordable_qty = floor((cash - TRANS_COST) / today_price)
    if  affordable_qty >= MIN_PURCHAS:
      inventory += affordable_qty
      cash -= ((today_price * affordable_qty) + TRANS_COST)
  elif today_price > tomorrow_price:
    # we do not need additional conditions since inventory cannot be less than
    # the minimal purchase
    if inventory > 0:
      cash += inventory * today_price
      inventory = 0

  if step == last_idx - 1:
    if inventory > 0:
      cash += inventory * today_price
      inventory = 0

  cash_history.append(cash)
  invt_history.append(inventory)
  testing_history.extend(testing)
  forecast_history.extend(y_hat)
  volatility_history.extend(volatil_fc)

  steps += 1

  if steps % 10 == 0:
    print('Processed steps = {}'.format(steps))

  #if steps == 10:
  #  break