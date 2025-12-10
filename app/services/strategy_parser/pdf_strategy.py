import pandas as pd
from .base_strategy import BaseStrategy

class PdfStrategy(BaseStrategy):
    """Необходимо реализовать логику"""
    def parse(self, file) -> pd.DataFrame:
        pass