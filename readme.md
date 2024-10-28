## Action sequence

### 1. Update daily prices

Every day update daily prices by running the `write_daily_prices_to_sql.py`
script for every sector that you are interested in. Example commands for
*consumer defensive* and *consumer cyclical* sectors.

```
python write_daily_prices_to_sql.py --sector='consumer defensive'
python write_daily_prices_to_sql.py --sector='consumer cyclical'
```
