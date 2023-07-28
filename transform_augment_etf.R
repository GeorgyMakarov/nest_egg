invisible(lapply(c('dplyr', 'data.table'), library, character.only = T))

idx <- c('Date', 'Adj Close')
spx <- fread('gspc.csv')[, .SD, .SDcols = idx] %>% setnames(., idx, c('date', 'spx'))
etf <- fread('etf.csv')[, .SD, .SDcols = idx] %>% setnames(., idx, c('date', 'etf'))
dt  <- merge(etf, spx, by = 'date', all.x = T) %>% .[, !c('date'), with = F]

# Find correlation between SPX and ETF to understand if it is possible to use SPX
# old returns as a basis for ETF
cor.test(dt$etf, dt$spx) ## ETF and SPX are significantly correlated: cor = 0.99, p-val < 0.05

# Use older returns from SPX + error term and connect to actual ETF data
spx_differences <- c(diff(spx$spx), 0)
spx_returns <- 100 * spx_differences / spx$spx
idx <- seq(nrow(spx) - nrow(etf))
spx_old_ret <- spx_returns[idx]

etf_differences <- c(diff(etf$etf), 0)
etf_returns <- 100 * etf_differences / etf$etf
etf_returns <- c(spx_old_ret, etf_returns)

idx <- seq(nrow(spx))
plot(x = idx, y = spx_returns, type = 'l', col = 'grey')
lines(x = idx, y = etf_returns, type = 'l', col = 'red')

etf_returns <- etf_returns[1:5427] ## drop last value since it is for dev purpose

write.table(round(etf_returns, 4), 'etf_returns.txt', row.names = F, col.names = F)
