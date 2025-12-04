from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .strategy import Strategy
    from .payoff import Payoff


@dataclass
class Player:
    player_id: int
    strategies: List[Strategy] = field(default_factory=list, repr=False)
    payoffs: List[Payoff] = field(default_factory=list, repr=False)
    name: str = field(default="")
    
    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"Jugador_{self.player_id}"
        
        self._validate_player_id(self.player_id)

    def _validate_player_id(self, player_id: int) -> None:
        if not isinstance(player_id, int) or player_id <= 0:
            raise ValueError(f"ID de jugador debe ser entero positivo: {player_id}")

    @property
    def player_id(self) -> int:
        return self._player_id

    @player_id.setter
    def player_id(self, value: int) -> None:
        self._validate_player_id(value)
        self._player_id = value

    def add_strategy(self, strategy: Strategy) -> None:
        if strategy not in self.strategies:
            self.strategies.append(strategy)

    def remove_strategy(self, strategy: Strategy) -> bool:
        if strategy in self.strategies:
            self.strategies.remove(strategy)
            return True
        return False

    def get_strategies(self) -> List[Strategy]:
        return list(self.strategies)

    def get_strategies_for_scenario(self, scenario_id: int) -> List[Strategy]:
        return [
            strategy for strategy in self.strategies
            if strategy.from_scenario.scenario_id == scenario_id
        ]

    def add_payoff(self, payoff: Payoff) -> None:
        if payoff.player != self:
            raise ValueError(
                f"El pago {payoff.payoff_id} no pertenece al jugador {self.player_id}"
            )
        
        if payoff not in self.payoffs:
            self.payoffs.append(payoff)

    def remove_payoff(self, payoff: Payoff) -> bool:
        if payoff in self.payoffs:
            self.payoffs.remove(payoff)
            return True
        return False

    def get_payoffs(self) -> List[Payoff]:
        return list(self.payoffs)

    def get_payoff_by_history(self, history_id: int) -> Optional[Payoff]:
        for payoff in self.payoffs:
            if payoff.history.history_id == history_id:
                return payoff
        return None

    def has_strategies(self) -> bool:
        return len(self.strategies) > 0

    def has_payoffs(self) -> bool:
        return len(self.payoffs) > 0

    def get_strategy_count(self) -> int:
        return len(self.strategies)

    def get_payoff_count(self) -> int:
        return len(self.payoffs)

    def calculate_total_utility(self) -> float:
        return sum(payoff.expected_utility for payoff in self.payoffs)

    def get_summary(self) -> dict[str, any]:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "strategy_count": self.get_strategy_count(),
            "payoff_count": self.get_payoff_count(),
            "total_utility": self.calculate_total_utility(),
            "has_strategies": self.has_strategies(),
            "has_payoffs": self.has_payoffs(),
        }

    def describe(self) -> dict[str, any]:
        summary = self.get_summary()
        summary.update({
            "strategies": [
                {
                    "strategy_id": strategy.strategy_id,
                    "from_scenario_id": strategy.from_scenario.scenario_id,
                    "action_id": strategy.action.action_id
                }
                for strategy in self.strategies
            ],
            "payoffs": [
                {
                    "payoff_id": payoff.payoff_id,
                    "history_id": payoff.history.history_id,
                    "value": payoff.value,
                    "expected_utility": payoff.expected_utility
                }
                for payoff in self.payoffs
            ]
        })
        return summary

    def __hash__(self) -> int:
        return hash(self.player_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Player):
            return NotImplemented
        return self.player_id == other.player_id

    def __repr__(self) -> str:
        return (
            f"Player(id={self.player_id}, name='{self.name}', "
            f"strategies={len(self.strategies)}, payoffs={len(self.payoffs)})"
        )

    def __str__(self) -> str:
        return f"{self.name} (ID: {self.player_id})"