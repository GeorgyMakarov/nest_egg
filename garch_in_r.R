library(ggplot2)
library(zoo)
library(quantmod)
library(xts)
library(PerformanceAnalytics)
library(rugarch)

getSymbols('IUIT.L', from = '2016-01-01', to = '2024-01-16')

returns <- CalculateReturns(IUIT.L$IUIT.L.Close)
returns <- na.omit(returns)

autoplot(returns)
hist(returns)

