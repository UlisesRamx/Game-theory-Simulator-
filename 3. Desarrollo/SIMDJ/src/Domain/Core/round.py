from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .player import Player


@dataclass
class Round:
    round_id: int
    round_number: int = field(default=1)
    active_player: Optional[Player] = field(default=None, repr=False)
    description: str = field(default="")
    
    def __post_init__(self) -> None:
        if not self.description:
            self.description = f"Ronda {self.round_number}"
        
        self._validate_round_id(self.round_id)
        self._validate_round_number(self.round_number)

    def _validate_round_id(self, round_id: int) -> None:
        if not isinstance(round_id, int) or round_id <= 0:
            raise ValueError(f"ID de ronda debe ser entero positivo: {round_id}")

    def _validate_round_number(self, round_number: int) -> None:
        if not isinstance(round_number, int) or round_number <= 0:
            raise ValueError(f"Número de ronda debe ser entero positivo: {round_number}")

    @property
    def round_id(self) -> int:
        return self._round_id

    @round_id.setter
    def round_id(self, value: int) -> None:
        self._validate_round_id(value)
        self._round_id = value

    @property
    def round_number(self) -> int:
        return self._round_number

    @round_number.setter
    def round_number(self, value: int) -> None:
        self._validate_round_number(value)
        self._round_number = value

    def set_active_player(self, player: Player) -> None:
        self.active_player = player

    def get_active_player(self) -> Optional[Player]:
        return self.active_player

    def has_active_player(self) -> bool:
        return self.active_player is not None

    def get_active_player_id(self) -> Optional[int]:
        return self.active_player.player_id if self.active_player else None

    def get_active_player_name(self) -> str:
        if self.active_player:
            return self.active_player.name
        return "Sin jugador"

    def clear_active_player(self) -> None:
        self.active_player = None

    def is_player_active(self, player: Player) -> bool:
        return self.active_player == player

    def is_player_active_by_id(self, player_id: int) -> bool:
        if not self.active_player:
            return False
        return self.active_player.player_id == player_id

    def get_info(self) -> dict[str, any]:
        return {
            "round_id": self.round_id,
            "round_number": self.round_number,
            "description": self.description,
            "active_player_id": self.get_active_player_id(),
            "active_player_name": self.get_active_player_name(),
            "has_active_player": self.has_active_player(),
        }

    def describe(self) -> dict[str, any]:
        info = self.get_info()
        
        if self.active_player:
            info.update({
                "active_player_details": {
                    "player_id": self.active_player.player_id,
                    "name": self.active_player.name,
                    "strategy_count": self.active_player.get_strategy_count(),
                    "payoff_count": self.active_player.get_payoff_count(),
                }
            })
        
        return info

    def __hash__(self) -> int:
        return hash(self.round_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Round):
            return NotImplemented
        return self.round_id == other.round_id

    def __repr__(self) -> str:
        player_id = self.get_active_player_id()
        player_info = f", active_player={player_id}" if player_id else ", no_player"
        
        return (
            f"Round(id={self.round_id}, number={self.round_number}"
            f"{player_info})"
        )

    def __str__(self) -> str:
        player_name = self.get_active_player_name()
        return f"Ronda {self.round_number}: {player_name}"

    def compare_by_number(self, other: Round) -> int:
        if self.round_number < other.round_number:
            return -1
        elif self.round_number > other.round_number:
            return 1
        else:
            return 0