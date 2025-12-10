import pandas as pd
from .base_strategy import BaseStrategy


class XlsxStrategy(BaseStrategy):

    def parse(self, file) -> pd.DataFrame:
        return pd.read_excel(file)