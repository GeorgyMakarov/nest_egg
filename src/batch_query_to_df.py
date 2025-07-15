import polars as pl
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

def batch_query_to_df(con_str, q_str, schema, bs, logger):
  """
  Runs a query on a SQL database and returns the result in batches.
  :param con_str: str, path to database
  :param q_str: str, query string
  :param schema: list, the schema of a table
  :param bs: int, batch size
  :param logger: a logger object
  """
  con_text = f"sqlite:///{con_str}"
  engine = create_engine(con_text)
  logger.info(f"Query: {q_str}")
  with engine.connect() as conn:
    batches = list(pl.read_database(q_str, 
                                    conn, 
                                    infer_schema_length=100000, 
                                    schema_overrides=schema, 
                                    iter_batches=True, 
                                    batch_size=bs))
    if not batches:
      logger.error("The query returned an empty DataFrame, returning empty...")
      df = pl.DataFrame()
    else:
      logger.info(f"Returned {len(batches)} batches, concatenating...")
      df = pl.concat(batches, how="diagonal_relaxed")
  logger.info(f"Returning {df.shape[0]} rows, {df.shape[1]} columns...")
  return df