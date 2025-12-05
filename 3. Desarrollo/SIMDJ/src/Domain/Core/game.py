from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from .player import Player
from .round import Round
from .scenario import Scenario
from .action import Action
from .history import History
from .payoff import Payoff


class GameState(Enum):
    """Estados posibles del juego."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED" 
    DELETED = "DELETED"


@dataclass
class Game:
    game_id: int
    players: List[Player] = field(default_factory=list)
    rounds: List[Round] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    state: GameState = field(default=GameState.CREATED)
    scenarios: List[Scenario] = field(default_factory=list, repr=False)
    actions: List[Action] = field(default_factory=list, repr=False)
    root: Optional[Scenario] = field(default=None, repr=False)
    adjacency: Dict[int, List[Action]] = field(default_factory=dict, repr=False)
    histories: List[History] = field(default_factory=list, repr=False)
    payoffs: List[Payoff] = field(default_factory=list, repr=False)
    name: str = field(default="")
    description: str = field(default="")
    
    total_scenarios: int = field(default=0)
    total_actions: int = field(default=0)
    total_histories: int = field(default=0)
    max_depth: int = field(default=0)
    strategies_per_player: int = field(default=0)
    num_rounds: int = field(default=0)
    num_strategies: int = field(default=0)
    
    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"Juego_{self.game_id}"
        
        if not self.description:
            self.description = f"Juego de teoría de juegos {self.game_id}"
        
        self._validate_game_id(self.game_id)
        self._validate_initial_state()

    def _validate_game_id(self, game_id: int) -> None:
        if not isinstance(game_id, int) or game_id <= 0:
            raise ValueError(f"ID de juego debe ser entero positivo: {game_id}")

    def _validate_initial_state(self) -> None:
        if not isinstance(self.state, GameState):
            raise ValueError(f"Estado inválido: {self.state}")

    def set_state(self, new_state: GameState) -> None:
        if not isinstance(new_state, GameState):
            raise ValueError(f"Estado inválido: {new_state}")
        
        self._validate_state_transition(self.state, new_state)
        self.state = new_state

    def _validate_state_transition(self, current: GameState, new: GameState) -> None:
        valid_transitions = {
            GameState.CREATED: [GameState.RUNNING, GameState.DELETED],
            GameState.RUNNING: [GameState.COMPLETED, GameState.DELETED],
            GameState.COMPLETED: [GameState.DELETED],
            GameState.DELETED: []  # Estado terminal
        }
        
        if new not in valid_transitions.get(current, []):
            raise ValueError(
                f"Transición inválida: {current.value} -> {new.value}. "
                f"Transiciones válidas desde {current.value}: "
                f"{[s.value for s in valid_transitions[current]]}"
            )

    def get_id(self) -> int:
        return self.game_id

    def add_player(self, player: Player) -> None:
        if player not in self.players:
            self.players.append(player)

    def remove_player(self, player: Player) -> bool:
        if player in self.players:
            self.players.remove(player)
            return True
        return False

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None

    def add_round(self, round_obj: Round) -> None:
        if round_obj not in self.rounds:
            self.rounds.append(round_obj)

    def remove_round(self, round_obj: Round) -> bool:
        if round_obj in self.rounds:
            self.rounds.remove(round_obj)
            return True
        return False

    def get_round_by_number(self, round_number: int) -> Optional[Round]:
        for round_obj in self.rounds:
            if round_obj.round_number == round_number:
                return round_obj
        return None

    def add_scenario(self, scenario: Scenario) -> None:
        if scenario not in self.scenarios:
            self.scenarios.append(scenario)

    def get_scenario_by_id(self, scenario_id: int) -> Optional[Scenario]:
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def add_action(self, action: Action) -> None:
        if action not in self.actions:
            self.actions.append(action)

    def add_history(self, history: History) -> None:
        if history not in self.histories:
            self.histories.append(history)

    def add_payoff(self, payoff: Payoff) -> None:
        if payoff not in self.payoffs:
            self.payoffs.append(payoff)

    def get_players(self) -> List[Player]:
        return list(self.players)

    def get_rounds(self) -> List[Round]:
        return list(self.rounds)

    def get_scenarios(self) -> List[Scenario]:
        return list(self.scenarios)

    def get_histories(self) -> List[History]:
        return list(self.histories)

    def get_payoffs(self) -> List[Payoff]:
        return list(self.payoffs)

    def get_player_count(self) -> int:
        return len(self.players)

    def get_round_count(self) -> int:
        return len(self.rounds)

    def get_scenario_count(self) -> int:
        return len(self.scenarios)

    def get_history_count(self) -> int:
        return len(self.histories)

    def get_payoff_count(self) -> int:
        return len(self.payoffs)

    def has_players(self) -> bool:
        return len(self.players) > 0

    def has_rounds(self) -> bool:
        return len(self.rounds) > 0

    def has_scenarios(self) -> bool:
        return len(self.scenarios) > 0

    def has_histories(self) -> bool:
        return len(self.histories) > 0

    def has_payoffs(self) -> bool:
        return len(self.payoffs) > 0

    def is_executed(self) -> bool:
        return self.state == GameState.COMPLETED

    def is_running(self) -> bool:
        return self.state == GameState.RUNNING

    def is_created(self) -> bool:
        return self.state == GameState.CREATED

    def is_deleted(self) -> bool:
        return self.state == GameState.DELETED

    def can_start(self) -> bool:
        return (self.state == GameState.CREATED and 
                self.has_players() and 
                self.has_rounds() and 
                self.has_scenarios())

    def start(self) -> None:
        if not self.can_start():
            raise ValueError(
                "El juego no puede iniciarse. Verifique que tenga jugadores, "
                "rondas y escenarios definidos."
            )
        self.set_state(GameState.RUNNING)

    def complete(self) -> None:
        if self.state != GameState.RUNNING:
            raise ValueError(
                f"El juego no puede completarse desde el estado {self.state.value}. "
                "Debe estar en estado RUNNING."
            )
        self.set_state(GameState.COMPLETED)

    def delete(self) -> None:
        self.set_state(GameState.DELETED)

    def get_summary(self) -> Dict[str, any]:
        return {
            "game_id": self.game_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "state": self.state.value,
            "player_count": self.get_player_count(),
            "round_count": self.get_round_count(),
            "scenario_count": self.get_scenario_count(),
            "history_count": self.get_history_count(),
            "payoff_count": self.get_payoff_count(),
            "has_root": self.root is not None,
            "is_executed": self.is_executed(),
            "is_running": self.is_running(),
            "can_start": self.can_start(),
            "total_scenarios": self.total_scenarios,
            "total_actions": self.total_actions,
            "total_histories": self.total_histories,
            "max_depth": self.max_depth,
            "strategies_per_player": self.strategies_per_player,
            "num_rounds": self.num_rounds,
            "num_strategies": self.num_strategies,
        }

    def as_export_dict(self) -> Dict[str, any]:
        return {
            "game": self.get_summary(),
            "players": [player.get_summary() for player in self.players],
            "rounds": [round_obj.get_info() for round_obj in self.rounds],
            "scenarios": [scenario.describe() for scenario in self.scenarios],
            "actions": [action.describe() for action in self.actions],
            "histories": [history.describe() for history in self.histories],
            "payoffs": [payoff.describe() for payoff in self.payoffs],
        }

    def get_total_expected_utility(self) -> float:
        return sum(payoff.expected_utility for payoff in self.payoffs)

    def get_player_utilities(self) -> Dict[int, float]:
        utilities = {}
        for payoff in self.payoffs:
            player_id = payoff.player.player_id
            utilities[player_id] = utilities.get(player_id, 0.0) + payoff.expected_utility
        return utilities

    def __hash__(self) -> int:
        return hash(self.game_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Game):
            return NotImplemented
        return self.game_id == other.game_id

    def __repr__(self) -> str:
        return (
            f"Game(id={self.game_id}, name='{self.name}', "
            f"players={len(self.players)}, rounds={len(self.rounds)}, "
            f"state='{self.state.value}')"
        )

    def __str__(self) -> str:
        return f"{self.name} (ID: {self.game_id}, Estado: {self.state.value})"