from datetime import date
from datetime import timedelta

def get_year_ago():
  """
  Gets the same day year ago in string format.
  """
  today = date.today()
  year_ago = today - timedelta(days=365)
  return year_ago.strftime("%Y-%m-%d")
