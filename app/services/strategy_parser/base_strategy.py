from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):

    @abstractmethod
    def parse(self, file) -> pd.DataFrame:
        raise NotImplementedError("Метод parse должен быть реализован в дочернем классе")