#!/usr/bin/python
# -*- coding: utf-8 -*-

# sql_query_helper.py

import sqlite3
import pandas as pd

def sql_query(db_path, query):
  """
  Send text query to SQL lite database and returns result. The purpose of the
  function is to reduce code size by avoiding manual connection every time
  a new query appears.

  Params:
    db_path (string): The path to a data base.
    query (string): The text of a SQL query.
  """
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute(query)
  res = cursor.fetchall()
  conn.close()
  return res

def read_sql_to_pd(db_path, query):
  """
  Send text query to SQL lite database and returns result in a pandas data 
  frame. The purpose of the function is to reduce code size by avoiding 
  manual connection every time a new query appears.

  Params:
    db_path (string): The path to a data base.
    query (string): The text of a SQL query.
  """
  conn = sqlite3.connect(db_path)
  res = pd.read_sql_query(query, conn)
  conn.close()
  return res

def write_table_to_sql(db_path, df, t_name):
  """
  Write pandas data table to SQL database by connecting to the data base
  and replacing the records which already exist in it.

  Params:
    db_path (string): The path to a data base.
    df (data frame): A pandas data frame.
    t_name (string): The name of a SQL table to write into.
  """
  print(f"write_table_to_sql(): Writing {df.shape[0]} rows to {t_name} ...")
  conn = sqlite3.connect(db_path)
  df.to_sql(t_name, conn, if_exists='append', index=False)
  conn.close()