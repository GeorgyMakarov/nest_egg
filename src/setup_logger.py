import sys
import logging
import inspect

def setup_log(name=None):
  """
  Sets up a logger and returns it.
  :param name: logger name's string
  """
  if name is None:
    frame = inspect.currentframe().f_back
    name = frame.f_code.co_name
  logger = logging.getLogger(name)
  logger.setLevel(logging.INFO)
  ch = logging.StreamHandler()
  fm = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  ch.setFormatter(fm)
  logger.addHandler(ch)
  return logger