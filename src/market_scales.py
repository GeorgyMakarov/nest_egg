import polars as pl
import numpy as np

class MarketScales:
  def __init__(self, meat):
    self.data = meat

  def run(self):
    df = pl.DataFrame(self.data)
    breakpoint()