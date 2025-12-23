from ..services.strategy_parser.pdf_strategy import PdfStrategy
from ..services.strategy_parser.csv_strategy import CsvStrategy
from ..services.strategy_parser.xlsx_strategy import XlsxStrategy
from ..services.strategy_parser.base_strategy import BaseStrategy
from ..services.avtodor_db import AvtodorDB
from ..services.normalize_files import normalize_dataframe
from ..services.progress_tracker import progress_tracker

class FileImport:

    PARSERS = {
        "pdf": PdfStrategy(),
        "xlsx": XlsxStrategy(),
        "csv": CsvStrategy(),
    }

    @classmethod
    async def import_file(cls, ext: str, file):
        await progress_tracker.set(10)
        parser: BaseStrategy = cls.PARSERS.get(ext)
        await progress_tracker.set(20)
        if not parser:
            raise ValueError(f"Неподдерживаемый тип файла: {ext}")
        await progress_tracker.set(30)
        await progress_tracker.set(40)
        await progress_tracker.set(50)
        df = parser.parse(file)
        await progress_tracker.set_items(len(df))
        await progress_tracker.set(60)
        await progress_tracker.set(70)
        df_norm = normalize_dataframe(df)
        await progress_tracker.set_items(len(df_norm))
        await progress_tracker.set(80)
        await progress_tracker.set(90)
        saved = await AvtodorDB.bulk_create_transactions(df_norm)
        await progress_tracker.set(100)
        return saved, len(df_norm)
