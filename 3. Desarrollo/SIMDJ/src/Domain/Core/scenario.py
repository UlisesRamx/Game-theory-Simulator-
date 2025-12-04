from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .action import Action


@dataclass
class Scenario:
    scenario_id: int
    depth: int = field(default=0)
    scenario_type: str = field(default="normal")
    label: str = field(default="")
    children: List[Scenario] = field(default_factory=list, repr=False)
    outgoing_actions: List[Action] = field(default_factory=list, repr=False)
    
    NORMAL_TYPE = "normal"
    FINAL_TYPE = "final"
    VALID_TYPES = {NORMAL_TYPE, FINAL_TYPE}

    def __post_init__(self) -> None:
        if not self.label:
            self.label = f"X{self.scenario_id}"
        
        self._validate_scenario_type(self.scenario_type)
        
        self._validate_depth(self.depth)

    def _validate_scenario_type(self, scenario_type: str) -> None:
        if scenario_type.lower() not in self.VALID_TYPES:
            valid_types = ", ".join(self.VALID_TYPES)
            raise ValueError(
                f"Tipo de escenario inválido: '{scenario_type}'. "
                f"Usar: {valid_types}"
            )

    def _validate_depth(self, depth: int) -> None:
        if depth < 0:
            raise ValueError(f"La profundidad no puede ser negativa: {depth}")

    @property
    def scenario_type(self) -> str:
        return self._scenario_type

    @scenario_type.setter
    def scenario_type(self, value: str) -> None:
        self._validate_scenario_type(value)
        self._scenario_type = value.lower()

    @property
    def depth(self) -> int:
        return self._depth

    @depth.setter
    def depth(self, value: int) -> None:
        self._validate_depth(value)
        self._depth = value

    def is_terminal(self) -> bool:
        return self.scenario_type == self.FINAL_TYPE

    def is_decision_node(self) -> bool:
        return self.scenario_type == self.NORMAL_TYPE

    def add_outgoing_action(self, action: Action) -> None:
        if action not in self.outgoing_actions:
            self.outgoing_actions.append(action)
            action.origin_scenario = self

    def remove_outgoing_action(self, action: Action) -> bool:
        if action in self.outgoing_actions:
            self.outgoing_actions.remove(action)
            if action.origin_scenario == self:
                action.origin_scenario = None
            return True
        return False

    def get_outgoing_actions(self) -> List[Action]:

        return list(self.outgoing_actions)

    def add_child(self, child_scenario: Scenario) -> None:
        if child_scenario not in self.children:
            self.children.append(child_scenario)

    def remove_child(self, child_scenario: Scenario) -> bool:
        if child_scenario in self.children:
            self.children.remove(child_scenario)
            return True
        return False

    def get_children(self) -> List[Scenario]:
        return list(self.children)

    def has_outgoing_actions(self) -> bool:
        return len(self.outgoing_actions) > 0

    def has_children(self) -> bool:
        return len(self.children) > 0

    def describe(self) -> dict[str, any]:
        return {
            "scenario_id": self.scenario_id,
            "label": self.label,
            "depth": self.depth,
            "scenario_type": self.scenario_type,
            "is_terminal": self.is_terminal(),
            "outgoing_actions_count": len(self.outgoing_actions),
            "children_count": len(self.children),
        }

    def get_action_by_label(self, action_label: str) -> Optional[Action]:
        for action in self.outgoing_actions:
            if action.label == action_label:
                return action
        return None

    def __hash__(self) -> int:
        return hash(self.scenario_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Scenario):
            return NotImplemented
        return self.scenario_id == other.scenario_id

    def __repr__(self) -> str:
        return (
            f"Scenario(id={self.scenario_id}, label='{self.label}', "
            f"depth={self.depth}, type='{self.scenario_type}', "
            f"actions={len(self.outgoing_actions)}, children={len(self.children)})"
        )

    def __str__(self) -> str:
        node_type = "TERMINAL" if self.is_terminal() else "DECISION"
        return f"{self.label}({node_type}, d={self.depth})"