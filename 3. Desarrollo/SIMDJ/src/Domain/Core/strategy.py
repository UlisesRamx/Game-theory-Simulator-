from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scenario import Scenario
    from .action import Action


@dataclass(unsafe_hash=True)
class Strategy:
    strategy_id: int
    from_scenario: 'Scenario'
    action: 'Action'
    description: str = field(default="")
    
    def __post_init__(self) -> None:
        if not self.description:
            self.description = f"Estrategia {self.strategy_id}"
        
        self._validate_strategy_id(self.strategy_id)
        self._validate_scenario_action_relationship()

    def _validate_strategy_id(self, strategy_id: int) -> None:
        if not isinstance(strategy_id, int) or strategy_id <= 0:
            raise ValueError(f"ID de estrategia debe ser entero positivo: {strategy_id}")

    def _validate_scenario_action_relationship(self) -> None:
        if self.from_scenario and self.action:
            if self.action not in self.from_scenario.outgoing_actions:
                raise ValueError(
                    f"La acción {self.action.action_id} no pertenece al escenario "
                    f"{self.from_scenario.scenario_id}. Las acciones válidas son: "
                    f"{[a.action_id for a in self.from_scenario.outgoing_actions]}"
                )

    def get_from_scenario(self) -> 'Scenario':
        return self.from_scenario

    def get_action(self) -> 'Action':
        return self.action

    def get_scenario_id(self) -> int:
        return self.from_scenario.scenario_id

    def get_action_id(self) -> int:

        return self.action.action_id

    def get_action_probability(self) -> float:
        return self.action.probability

    def get_action_label(self) -> str:
        return self.action.label

    def get_scenario_label(self) -> str:
        return self.from_scenario.label

    def is_valid(self) -> bool:

        try:
            self._validate_scenario_action_relationship()
            return True
        except ValueError:
            return False

    def describes_same_decision(self, other: Strategy) -> bool:
        return (self.from_scenario == other.from_scenario and 
                self.action == other.action)

    def describes_same_scenario(self, other: Strategy) -> bool:
        return self.from_scenario == other.from_scenario

    def describes_same_action(self, other: Strategy) -> bool:
        return self.action == other.action

    def describe(self) -> dict[str, any]:
        return {
            "strategy_id": self.strategy_id,
            "description": self.description,
            "from_scenario_id": self.from_scenario.scenario_id,
            "from_scenario_label": self.from_scenario.label,
            "action_id": self.action.action_id,
            "action_label": self.action.label,
            "action_probability": self.action.probability,
            "is_valid": self.is_valid(),
            "scenario_type": self.from_scenario.scenario_type,
            "scenario_depth": self.from_scenario.depth,
        }

    def get_short_description(self) -> str:
        return f"En {self.from_scenario.label} -> {self.action.label}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Strategy):
            return NotImplemented
        return self.strategy_id == other.strategy_id

    def __repr__(self) -> str:
        return (
            f"Strategy(id={self.strategy_id}, "
            f"scenario={self.from_scenario.scenario_id}, "
            f"action={self.action.action_id}, "
            f"valid={self.is_valid()})"
        )

    def __str__(self) -> str:
        return f"{self.description}: {self.get_short_description()}"