from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .scenario import Scenario


@dataclass
class Action:
    action_id: int
    probability: float = field(default=0.0)
    destination_scenario: Optional[Scenario] = field(default=None, repr=False)
    origin_scenario: Optional[Scenario] = field(default=None, repr=False)
    label: str = field(default="")
    
    def __post_init__(self) -> None:
        if not self.label:
            self.label = f"a{self.action_id}"
        
        self._validate_probability(self.probability)

    def _validate_probability(self, probability: float) -> None:
        if not 0.0 <= probability <= 1.0:
            raise ValueError(f"Probabilidad debe estar entre 0 y 1, se recibió: {probability}")

    @property
    def probability(self) -> float:
        return self._probability

    @probability.setter
    def probability(self, value: float) -> None:
        self._validate_probability(value)
        self._probability = float(value)

    def set_probability(self, probability: float) -> None:
        self.probability = probability

    def get_probability(self) -> float:
        return self.probability

    def describe(self) -> dict[str, any]:
        return {
            "action_id": self.action_id,
            "label": self.label,
            "probability": self.probability,
            "origin_scenario_id": (
                self.origin_scenario.scenario_id if self.origin_scenario else None
            ),
            "destination_scenario_id": (
                self.destination_scenario.scenario_id if self.destination_scenario else None
            ),
        }

    def is_connected(self) -> bool:
        return self.origin_scenario is not None and self.destination_scenario is not None

    def get_connection_info(self) -> tuple[Optional[int], Optional[int]]:
        origin_id = self.origin_scenario.scenario_id if self.origin_scenario else None
        dest_id = self.destination_scenario.scenario_id if self.destination_scenario else None
        return origin_id, dest_id

    def __hash__(self) -> int:
        return hash(self.action_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Action):
            return NotImplemented
        return self.action_id == other.action_id

    def __repr__(self) -> str:
        origin_id = self.origin_scenario.scenario_id if self.origin_scenario else None
        dest_id = self.destination_scenario.scenario_id if self.destination_scenario else None
        
        return (
            f"Action(id={self.action_id}, label='{self.label}', "
            f"probability={self.probability:.3f}, "
            f"origin={origin_id}, destination={dest_id})"
        )

    def __str__(self) -> str:
        return f"{self.label}(p={self.probability:.2f})"