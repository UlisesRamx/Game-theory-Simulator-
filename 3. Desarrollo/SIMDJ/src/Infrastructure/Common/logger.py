from __future__ import annotations
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

@dataclass
class Logger:    
    log_file: Optional[Path] = None
    log_level: str = "INFO"
    log_history: List[str] = field(default_factory=list)
    console_output: bool = True
    max_log_size_mb: float = 10.0
    LOG_LEVELS = {"INFO": 1, "WARNING": 2, "ERROR": 3}

    def __post_init__(self) -> None:
        if self.log_file is None:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.log_file = base_dir / "Tests" / "Logs" / "simdj.log"
        
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._rotate_if_needed()

    def _rotate_if_needed(self) -> None:
        if not self.log_file.exists():
            return
            
        file_size_mb = self.log_file.stat().st_size / (1024 * 1024)
        
        if file_size_mb > self.max_log_size_mb:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.log_file.with_name(f"{self.log_file.stem}_{timestamp}{self.log_file.suffix}")
            
            try:
                self.log_file.rename(backup_file)
                self.log_info(f"Log rotado: {backup_file.name}")
            except OSError as e:
                print(f"Error rotando log: {e}", file=sys.stderr)

    def _get_current_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_log_entry(self, level: str, message: str) -> None:
        timestamp = self._get_current_timestamp()
        entry = f"[{timestamp}] {level}: {message}"
        
        self.log_history.append(entry)
        
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except OSError as e:
            print(f"ERROR CRÍTICO: No se pudo escribir log: {e}", file=sys.stderr)
        
        if self.console_output:
            print(entry)

    def log_info(self, message: str) -> None:
        self._write_log_entry("INFO", message)

    def log_warning(self, message: str) -> None:
        self._write_log_entry("WARNING", message)

    def log_error(self, message: str) -> None:
        self._write_log_entry("ERROR", message)