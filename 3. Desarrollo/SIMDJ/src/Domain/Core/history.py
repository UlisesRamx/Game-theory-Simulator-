from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from functools import reduce
from operator import mul

from .action import Action


@dataclass
class History:
    history_id: int
    actions: List[Action] = field(default_factory=list)
    total_probability: float = field(default=0.0)
    description: str = field(default="")
    
    def __post_init__(self) -> None:
        if not self.description:
            self.description = f"Historia {self.history_id}"
        
        self._validate_history_id(self.history_id)
        self._validate_actions_sequence()
        
        # Calcular probabilidad inicial si hay acciones
        if self.actions:
            self.calculate_probability()

    def _validate_history_id(self, history_id: int) -> None:
        if not isinstance(history_id, int) or history_id <= 0:
            raise ValueError(f"ID de historia debe ser entero positivo: {history_id}")

    def _validate_actions_sequence(self) -> None:
        for i, action in enumerate(self.actions):
            if not 0 <= action.probability <= 1:
                raise ValueError(
                    f"Acción {i} (ID: {action.action_id}) tiene probabilidad "
                    f"inválida: {action.probability}"
                )

    @property
    def history_id(self) -> int:
        return self._history_id

    @history_id.setter
    def history_id(self, value: int) -> None:
        self._validate_history_id(value)
        self._history_id = value

    def calculate_probability(self) -> float:
        if not self.actions:
            self.total_probability = 0.0
            return 0.0
        
        try:
            probabilities = [action.probability for action in self.actions]
            self.total_probability = reduce(mul, probabilities, 1.0)
            return self.total_probability
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error calculando probabilidad de historia: {e}")

    def get_actions(self) -> List[Action]:
        return list(self.actions)

    def add_action(self, action: Action, recalculate_probability: bool = True) -> None:
        self.actions.append(action)
        if recalculate_probability:
            self.calculate_probability()

    def insert_action(self, index: int, action: Action, recalculate_probability: bool = True) -> None:
        if index < 0 or index > len(self.actions):
            raise IndexError(f"Índice {index} fuera de rango para historia con {len(self.actions)} acciones")
        
        self.actions.insert(index, action)
        if recalculate_probability:
            self.calculate_probability()

    def remove_action(self, action: Action, recalculate_probability: bool = True) -> bool:
        if action in self.actions:
            self.actions.remove(action)
            if recalculate_probability:
                self.calculate_probability()
            return True
        return False

    def get_action_at(self, index: int) -> Optional[Action]:
        try:
            return self.actions[index]
        except IndexError:
            return None

    def get_first_action(self) -> Optional[Action]:
        return self.actions[0] if self.actions else None

    def get_last_action(self) -> Optional[Action]:
        return self.actions[-1] if self.actions else None

    def get_action_count(self) -> int:
        return len(self.actions)

    def has_actions(self) -> bool:
        return len(self.actions) > 0

    def is_empty(self) -> bool:
        return len(self.actions) == 0

    def get_action_labels(self) -> List[str]:
        return [action.label for action in self.actions]

    def get_action_ids(self) -> List[int]:
        return [action.action_id for action in self.actions]

    def get_actions_string(self, separator: str = " -> ") -> str:
        return separator.join(self.get_action_labels())

    def get_probability(self) -> float:
        return self.total_probability

    def is_certain(self) -> bool:
        return abs(self.total_probability - 1.0) < 1e-10

    def is_impossible(self) -> bool:
        return abs(self.total_probability) < 1e-10

    def describe(self) -> dict[str, any]:
        return {
            "history_id": self.history_id,
            "description": self.description,
            "action_count": self.get_action_count(),
            "actions": self.get_action_labels(),
            "action_ids": self.get_action_ids(),
            "total_probability": self.total_probability,
            "is_certain": self.is_certain(),
            "is_impossible": self.is_impossible(),
            "actions_string": self.get_actions_string(),
        }

    def get_short_description(self) -> str:
        actions_str = self.get_actions_string()
        return f"{self.description}: {actions_str} (p={self.total_probability:.3f})"

    def __hash__(self) -> int:
        return hash(self.history_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, History):
            return NotImplemented
        return self.history_id == other.history_id

    def __repr__(self) -> str:
        return (
            f"History(id={self.history_id}, "
            f"actions={len(self.actions)}, "
            f"probability={self.total_probability:.3f})"
        )

    def __str__(self) -> str:
        return self.get_short_description()

    def __len__(self) -> int:
        return len(self.actions)

    def __getitem__(self, index: int) -> Action:
        return self.actions[index]

    def __contains__(self, action: Action) -> bool:
        return action in self.actions