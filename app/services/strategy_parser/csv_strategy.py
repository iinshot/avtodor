import pandas as pd
from .base_strategy import BaseStrategy

class CsvStrategy(BaseStrategy):

    def parse(self, file) -> pd.DataFrame:
        return pd.read_csv(file, encoding="utf-8", sep=";")