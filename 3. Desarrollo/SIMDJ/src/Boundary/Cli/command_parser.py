from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParsedCommand:
    raw: str
    tokens: List[str]


class CommandParser:
    def read_input(self, prompt: str = "> ") -> str:
        return input(prompt)

    def parse(self, raw: str) -> ParsedCommand:
        raw = (raw or "").strip()
        tokens = raw.split() if raw else []
        return ParsedCommand(raw=raw, tokens=tokens)

    def parse_menu_option(self, raw: str) -> Optional[int]:
        raw = (raw or "").strip()
        if not raw or not raw.isdigit():
            return None
        return int(raw)

    def parse_probabilities_csv(self, raw: str) -> Optional[List[float]]:
        raw = (raw or "").strip()
        if not raw:
            return None
        try:
            parts = [p.strip() for p in raw.split(",")]
            return [float(p) for p in parts]
        except ValueError:
            return None

    def is_cancel(self, raw: str) -> bool:
        return (raw or "").strip().upper() == "C"

    def is_yes(self, raw: str) -> bool:
        return (raw or "").strip().upper() == "S"

    def is_no(self, raw: str) -> bool:
        return (raw or "").strip().upper() == "N"


__all__ = ["CommandParser", "ParsedCommand"]
