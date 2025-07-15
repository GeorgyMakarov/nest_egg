import sys
import argparse

class ArgParser:
  def __init__(self, arg_list, logger):
    """
    :param arg_list: a list of argument strings, like ['test', 'write'] etc.
    :param logger: a logger object
    """
    self.arg_list = arg_list
    self.logger = logger
  
  def parse(self) -> argparse.Namespace:
    if len(sys.argv) == 1:
      self.logger.error("No command line arguments provided, exiting...")
      raise SystemExit("No command line arguments provided.")
    parser = argparse.ArgumentParser()
    for arg in self.arg_list:
      parser.add_argument("--" + arg, type=str)
    args = parser.parse_args()
    return args