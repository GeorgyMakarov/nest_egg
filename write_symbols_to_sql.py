#!/usr/bin/python
# -*-coding:utf-8-*
# write_symbols_to_sql.py

import sqlite3
import numpy as np
import pandas as pd
from sql_query_helper import write_table_to_sql

ROOT = 'C:/Users/makar/OneDrive/Documents/project_george/'
CSV_PATH = 'csv_data/ticker_param.xlsx'
DB_PATH  = 'dbms/master_storage/master_storage.db'

symbols = pd.read_excel(ROOT + CSV_PATH)
write_table_to_sql(ROOT+DB_PATH, symbols, 'symbol')