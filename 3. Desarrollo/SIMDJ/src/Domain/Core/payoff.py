from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .player import Player
    from .history import History


@dataclass
class Payoff:
    payoff_id: int
    player: Player
    history: Optional[History] = None
    value: float = 0.0
    
    expected_utility: float = 0.0
    description: str = field(default="")
    
    def __post_init__(self) -> None:
        if not self.description:
            self.description = f"Pago {self.payoff_id}"
        
        self._validate_payoff_id(self.payoff_id)
        self._validate_value(self.value)
        self._validate_player_history_relationship()
        
        if self.history and hasattr(self.history, 'total_probability') and self.history.total_probability > 0:
            self.calculate_expected_utility(self.history.total_probability)

    def _validate_payoff_id(self, payoff_id: int) -> None:
        if not isinstance(payoff_id, int) or payoff_id <= 0:
            raise ValueError(f"ID de pago debe ser entero positivo: {payoff_id}")

    def _validate_value(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError(f"Valor de pago debe ser un número: {value}")

    def _validate_player_history_relationship(self) -> None:
        if not self.player:
            raise ValueError("Payoff debe tener jugador definido")

    def assign_history(self, history: History) -> None:
        if not history:
            raise ValueError("Historia no puede ser None")
        
        self.history = history
        if hasattr(self.history, 'total_probability'):
            self.calculate_expected_utility(self.history.total_probability)

    def calculate_expected_utility(self, history_probability: float) -> float:
        if not 0 <= history_probability <= 1:
            raise ValueError(f"Probabilidad de historia debe estar entre 0 y 1: {history_probability}")
        
        self.expected_utility = self.value * history_probability
        return self.expected_utility

    def recalculate_expected_utility(self) -> float:
        if hasattr(self.history, 'total_probability'):
            return self.calculate_expected_utility(self.history.total_probability)
        return 0.0

    def get_player_id(self) -> int:
        return self.player.player_id

    def get_player_name(self) -> str:
        return getattr(self.player, 'name', f'Jugador {self.player.player_id}')

    def get_history_id(self) -> int:
        return self.history.history_id

    def get_history_description(self) -> str:
        return getattr(self.history, 'description', f'Historia {self.history.history_id}')

    def get_history_probability(self) -> float:
        return getattr(self.history, 'total_probability', 0.0)

    def get_actions_sequence(self) -> str:
        if hasattr(self.history, 'get_actions_string'):
            return self.history.get_actions_string()
        return "Secuencia no disponible"

    def is_positive(self) -> bool:
        return self.value > 0

    def is_negative(self) -> bool:
        return self.value < 0

    def is_zero(self) -> bool:
        return abs(self.value) < 1e-10

    def has_expected_utility_calculated(self) -> bool:
        return abs(self.expected_utility) > 1e-10

    def get_efficiency_ratio(self) -> float:
        if self.value == 0:
            return 0.0
        return self.expected_utility / self.value

    def describe(self) -> dict[str, any]:
        return {
            "payoff_id": self.payoff_id,
            "description": self.description,
            "player_id": self.get_player_id(),
            "player_name": self.get_player_name(),
            "history_id": self.get_history_id(),
            "history_description": self.get_history_description(),
            "history_probability": self.get_history_probability(),
            "actions_sequence": self.get_actions_sequence(),
            "value": self.value,
            "expected_utility": self.expected_utility,
            "is_positive": self.is_positive(),
            "is_negative": self.is_negative(),
            "is_zero": self.is_zero(),
            "has_expected_utility_calculated": self.has_expected_utility_calculated(),
            "efficiency_ratio": self.get_efficiency_ratio(),
        }

    def get_short_description(self) -> str:
        sign = "+" if self.is_positive() else ""
        return (
            f"Pago {self.payoff_id}: {self.get_player_name()} -> "
            f"{sign}{self.value:.2f} (u={self.expected_utility:.3f})"
        )

    def __hash__(self) -> int:
        return hash(self.payoff_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Payoff):
            return NotImplemented
        return self.payoff_id == other.payoff_id

    def __repr__(self) -> str:
        return (
            f"Payoff(id={self.payoff_id}, "
            f"player={self.get_player_id()}, "
            f"history={self.get_history_id()}, "
            f"value={self.value:.2f}, "
            f"utility={self.expected_utility:.3f})"
        )

    def __str__(self) -> str:
        return self.get_short_description()

    def __lt__(self, other: Payoff) -> bool:
        if not isinstance(other, Payoff):
            return NotImplemented
        return self.value < other.value

    def __gt__(self, other: Payoff) -> bool:
        if not isinstance(other, Payoff):
            return NotImplemented
        return self.value > other.value