from __future__ import annotations
from datetime import datetime
from pathlib import Path


class NamingService:
    
    def __init__(self, date_format: str = "%Y%m%d-%H%M"):
        self._date_format = date_format

    def get_timestamp(self) -> str:
        return datetime.now().strftime(self._date_format)

    def get_date_format(self) -> str:
        return self._date_format

    def format_prefix(self, prefix: str) -> str:
        prefix = (prefix or "").strip()
        return prefix.replace(" ", "_") if prefix else "export"

    def validate_name(self, file_name: str) -> bool:
        if not file_name or not isinstance(file_name, str):
            return False
        bad_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        return not any(c in file_name for c in bad_chars)

    def generate_file_name(
        self, 
        players: int, 
        rounds: int, 
        strategies: int, 
        prefix: str
    ) -> str:
        prefix_f = self.format_prefix(prefix)
        timestamp = self.get_timestamp()
        return f"{prefix_f}_J{players}_R{rounds}_E{strategies}_{timestamp}"

    def resolve_file_conflict(self, full_path: str) -> str:
        if not full_path:
            raise ValueError("NamingService.resolve_file_conflict: ruta vacía.")

        path = Path(full_path)
        directory = path.parent
        base_name = path.stem
        extension = path.suffix

        if not path.exists():
            return full_path

        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = directory / new_name
            if not new_path.exists():
                return str(new_path)
            counter += 1