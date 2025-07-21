import polars as pl
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

def batch_df_to_sql(con_str, table_name, df, bs, logger):
  """
  Writes a Polars DataFrame to a SQL database in batches.
  :param con_str: str, path to database
  :param table_name: str, name of the destination table
  :param df: polars.DataFrame, the DataFrame to be written
  :param bs: int, batch size
  :param logger: a logger object
  """
  con_text = f"sqlite:///{con_str}"
  engine = create_engine(con_text)
  n_batch = bs
  row = 0
  height = df.height
  try:
    while row < height:
      df_batch = df.slice(row, n_batch)
      df_batch.write_database(table_name = table_name, 
                              connection = engine, 
                              if_table_exists = 'append')
      row += n_batch
      logger.info(f"Successfully wrote {row} rows to SQL...")  
  except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    raise TypeError("Database error.")
  