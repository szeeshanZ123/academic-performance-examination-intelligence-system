import os
import pandas as pd

def load_students():
  base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  csv_path = os.path.join(base_dir, 'data', 'students.csv')
  df = pd.read_csv(csv_path)
  return df
