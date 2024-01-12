# STAT 510: Applied Time Series Analysis

Source: https://online.stat.psu.edu/stat510/

## 1. Time Series Basics

### 1.1 Overview of Time Series Characteristics

List of important questions to consider when first looking at a time series is:

- is there a trend?  
- is there seasonality, meaning the repeated patterns related to calendar time?  
- are there outliers that are far away from the other data?  
- is there a periodic long-term pattern unrelated to seasonality?  
- is there constant variance over time?  
- are there any abrupt changes in the time series?  

**Note**: seasonality reflects patterns of lows and highs inside a year and is 
always related to calendar time, such as seasons, quarters, months, days of 
the week and so on.

**Note**: using seasonal effects in simple linear regression model with time as
a predictor and time series levels as outcomes require deleting the intercept 
from the model to be able to avoid multicollinearity issues.

The assumptions for residuals of time series linear models (both regression 
and ARIMA) are the same as for linear regression model:

- homoskedasticity  
- no autocorrelation  
- normality  

**Autocorrelation function (ACF)** is functional to determining the possible
structure of time series data. The ACF of residuals is also useful. The ideal
for the a sample ACF of residuals is that there aren't any significant
correlations for any lag.


### 1.2 Sample ACF and Properties of AR(1) Model

For an ACF to make sense the series must be **stationary** meaning that the
autocorrelation for any particular lag is the same regardless of where we are
in time.

A series is said to be stationary if it satisfies the following properties:

- the mean $E(x_t)$ is the same for all $t$  
- the variance of $x_t$ is the same for all $t$  
- the correlation between $x_t$ and $x_{(t - h)}$ is the same at each lag $h$  

Assumptions of first order AR model:

- the errors are independently distributed with mean 0 and constant variance  
- the errors are independent from the levels of the series  
- the series is stationary, meaning that slope coefficient is less than 1 

Pattern of ACF for AR(1) model:

- beta > 0: ACF exponentially decreases to 0 as the lag h increases  
- beta < 0: ACF exponentially decays to 0 but algebraic signs alternate by lags  

**Note**: the sample ACF will rarely fit a perfect theoretical pattern meaning
you have to try different models to see what fits. In other words, you should
not relate on the ACF too much and must be seeking an optimal solution.

To create a possibly stationary series, we examine the differences of the 1st
or the 2nd order. One must remember that running higher order differencing is
not optimal since it will introduce autocorrelation. It a series does not become
stationary after two differences, then one should try smoothing techniques.

**Note**: when lag 2 correlation is roughly equal to the squared value of the
lag 1 correlation, lag 3 correlation - to cubed value of the lag 1, lag 4 - to
the fourth power of the lag 1 correlation, this is pointing that an AR(1) model
may be a suitable model for the first differences.

When you model the differences, then you actually have to adjust you latest
value with the forecast difference at each step to be able to achieve the
forecast of the variable.


## 2. MA Models, Partial Autocorrelation, Notational Conventions

### 2.1 Moving Average Models

A **moving average** term in a time series model is a past error multiplied by 
a coefficient.

**Note**:The only non-zero value in the theoretical ACF of an MA(1) model is 
for lag 1. All other values of autocorrelation are 0. Consequently, the only
nonzero values in the theoretical ACF are for lags 1 and 2 in case of an MA(2)
model. All other lags behind it are equal to 0.

A property of MA(q) models in general is that there are nonzero autocorrelation
for the first $q$ lags and zero autocorrelation for all lags greater than $q$.

There is an invertibility requirement for MA models. An MA model is said to be
invertible if AR coefficients decrease to 0 as we move back in time.

### 2.2 Partial Autocorrelation Function (PACF)

A **partial autocorrelation** is a conditional correlation between two variables
under the assumption that we know and take into account the values of some other
set of variables.

Identification of an AR model is often best done by the PACF. The theoretical
PACF of an AR model is equal to 0 after the lag that represents the order of the
model.

On the opposite a clearer pattern for an MA model is in the ACF. The ACF of an
MA model will have nonzero autocorrelations only at lags involved in the model.
At the same time, the PACF of an MA model tapers to 0 in some manner (decays).


## 3. ARIMA models estimation and usage

### 3.1 Non-seasonal ARIMA models

Nonconstant variance in a stationary series must be addressed with a **GARCH** 
or an **ARCH** model which includes a model for changing variation over time. 
For data with a curved upward trend accompanied by increasing variance you 
better apply transformation with either a logarithm or a square root.

ACF and PACF must be considered together:

- AR models have PACF with non-zero values at the AR terms, ACF decays to zero  
- AR(2) has two spikes in the PACF and a sinusoidal that converges to zero  
- MA models have spikes in ACF at the MA terms, PACF decay to zero  
- ARMA models have ACF and PACF that both tail off to 0 with no clear order  

**Note**: one must perform a grid search of the order of an ARMA model to be
able to define the proper combination of $p$ and $q$. The combination of ACF and
PACF plots in this case just marks the presence of ARMA in data.

- if ACF does not tail off the series is non-stationary  
- if both plots do not show significant pikes, the series is random  
- if first differences were necessary and all the differenced autocorrelations
  are not significant then you see a random walk and you are done
  
**Note**: In financial time series, if the plots of the log returns of a series
show no significant spikes, then the series is a random walk, and you should use
naive forecast (ex., predicting with the last value).

When the order of a model has been selected and the model fitted, look at the
list of diagnostic parameters:

- p-values of the coefficients must be < 0.05  
- ACF of residuals must not have any significant peaks  
- Ljung-Box test of residuals must have p-value > 0.05  
- Breusch-Pagan test of residuals p-value > 0.05 (`het_breuschpagan`)  
- Jarque-Bera test of residuals p-value > 0.05 (`jarque_bera`)  

The lower the following values, the better the model is:

- AIC  
- AICc  
- BIC  

## 4. Seasonal ARIMA Models

### 4.1 Seasonal ARIMA models

With seasonal data you need to difference data twice: seasonal differencing
and de-trending to make the series stationary. In some cases, seasonal may be
enough to make the series stationary.
















