from strategy_parser.pdf_strategy import PdfStrategy
from strategy_parser.csv_strategy import CsvStrategy
from strategy_parser.xlsx_strategy import XlsxStrategy
from strategy_parser.base_strategy import BaseStrategy
from ..services.avtodor_db import AvtodorDB
from ..services.normalize_files import normalize_dataframe

class FileImport:

    PARSERS = {
        "pdf": PdfStrategy(),
        "xlsx": XlsxStrategy(),
        "csv": CsvStrategy(),
    }

    @classmethod
    async def import_file(cls, ext: str, file):
        parser: BaseStrategy = cls.PARSERS.get(ext)
        if not parser:
            raise ValueError(f"Неподдерживаемый тип файла: {ext}")

        df = parser.parse(file)
        df_norm = normalize_dataframe(df)
        saved = await AvtodorDB.bulk_create_transactions(df_norm)
        return saved, len(df_norm)
