from __future__ import annotations
from typing import List, Dict

from Domain.Core.game import Game, GameState
from Domain.Core.player import Player
from Domain.Core.round import Round
from Domain.Core.scenario import Scenario
from Domain.Core.action import Action

from Domain.Common.domain_validator import DomainValidator
from Domain.Common.exceptions import (TreeBuilderError,ValidationError)

from Infrastructure.Common.logger import Logger


class TreeBuilder:

    def __init__(
        self, 
        logger: Logger,
        domain_validator: DomainValidator
    ):
        self.game: Game
        self.scenarios: List[Scenario] = []
        self.actions: List[Action] = []
        self.adjacency: Dict[int, List[Action]] = {}

        self.max_depth: int = 0
        self.strategies_per_player: int = 0

        self.logger = logger
        self.domain_validator = domain_validator

    def calculate_total_scenarios(self, rounds: int, strategies: int) -> int:
        S, E = strategies, rounds
        if S == 1:
            return 1
        return (S ** E - 1) // (S - 1)

    def calculate_total_strategies(self, rounds: int, strategies: int) -> int:
        S, E = strategies, rounds
        if S == 1:
            return 1
        return ((S ** E - S ** 2) // (S - 1)) + 2 * S

    def calculate_total_histories(self, rounds: int, strategies: int) -> int:
        return strategies ** rounds

    def create_scenarios(self, rounds: int, strategies: int) -> List[Scenario]:
        try:
            scenarios: List[Scenario] = []
            scenario_id = 0

            root = Scenario(
                scenario_id=scenario_id, 
                depth=0, 
                scenario_type="normal", 
                label="X0"
            )
            scenarios.append(root)

            level = [root]
            x_count = 0
            z_count = 0

            for depth in range(1, rounds + 1):
                next_level = []

                for parent in level:
                    for _ in range(strategies):
                        scenario_id += 1

                        node_type = "final" if depth == rounds else "normal"

                        scenario = Scenario(
                            scenario_id=scenario_id,
                            depth=depth,
                            scenario_type=node_type
                        )

                        if node_type == "final":
                            z_count += 1
                            scenario.label = f"Z{z_count}"
                        else:
                            x_count += 1
                            scenario.label = f"X{x_count}"

                        parent.children.append(scenario)
                        scenarios.append(scenario)
                        next_level.append(scenario)

                next_level.sort(key=lambda s: s.scenario_id)
                level = next_level

            return scenarios

        except Exception as error:
            self.logger.log_error(f"[TreeBuilder] Error inesperado: {error}")
            raise TreeBuilderError(
                technical_message=f"Error técnico al crear los escenarios: {error}",
                user_message="Error al momento de crear los escenarios."
            )

    def create_actions(self, scenarios: List[Scenario]) -> List[Action]:
        try:
            if not scenarios:
                return []

            self.adjacency.clear()
            actions: List[Action] = []

            root = scenarios[0]
            root_children = sorted(root.children, key=lambda s: s.scenario_id)

            def add_edge(origin: Scenario, dest: Scenario, label: str) -> Action:
                action_id = len(actions) + 1

                action = Action(
                    action_id=action_id,
                    probability=0.0,
                    destination_scenario=dest,
                    origin_scenario=origin,
                    label=label
                )

                actions.append(action)
                self.adjacency.setdefault(origin.scenario_id, []).append(action)
                origin.outgoing_actions.append(action)

                return action

            for subtree_index, child in enumerate(root_children):
                letter = self._get_subtree_letter(subtree_index)
                counter = 1

                add_edge(root, child, f"{letter}{counter}")
                counter += 1

                counter = self._build_subtree_actions(
                    node=child,
                    letter=letter,
                    counter=counter,
                    add_edge_fn=add_edge
                )

            return actions
        
        except Exception as error:
            self.logger.log_error(f"[TreeBuilder] Error inesperado: {error}")
            raise TreeBuilderError(
                technical_message=f"Error técnico creando las acciones: {error}",
                user_message="Error al momento de crear las acciones."
            )

    def _build_subtree_actions(
        self, 
        node: Scenario, 
        letter: str, 
        counter: int, 
        add_edge_fn
    ) -> int:
        try:
            if not node.children:
                return counter

            children_sorted = sorted(node.children, key=lambda s: s.scenario_id)

            for child in children_sorted:
                add_edge_fn(node, child, f"{letter}{counter}")
                counter += 1
                counter = self._build_subtree_actions(
                    child, letter, counter, add_edge_fn
                )

            return counter
        
        except Exception as error:
            self.logger.log_error(f"[TreeBuilder] Error inesperado: {error}")
            raise TreeBuilderError(
                technical_message=f"Error técnico creando subárboles de acciones: {error}",
                user_message="Error al crear subárboles de acciones."
            )

    def _get_subtree_letter(self, index: int) -> str:
        try:
            lowercase = [chr(c) for c in range(ord("a"), ord("z") + 1)]
            uppercase = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
            letters = lowercase + uppercase  # 52 subárboles

            if index >= len(letters):
                raise ValidationError(
                    technical_message=f"TreeBuilder: subárbol {index + 1} excede el límite de {len(letters)} letras.",
                    user_message="Demasiados subárboles en el juego. Reduzca el número de estrategias."
                )

            return letters[index]
        except (ValidationError) as error:
            self.logger.log_warning(f"[TreeBuilder] Error asignando las etiquetas a los subárboles: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[TreeBuilder] Error inesperado al asignar etiquetas a los subárboles: {error}")
            raise TreeBuilderError(
                technical_message=f"Error técnico al asignar etiquetas a los subárboles: {error}",
                user_message="Error cuando se asignaban las etiquetas a los subárboles."
            )

    def build_tree(self, players: int, rounds: int, strategies: int) -> Game:
        try:
            self.logger.log_info("Iniciando construcción del árbol...")
            self.scenarios = []
            self.actions = []
            self.adjacency = {}

            self.domain_validator.validate_game_complexity(rounds, strategies)
            
            self.max_depth = rounds
            self.strategies_per_player = strategies

            self.game = Game(game_id=1)
            self.game.state = GameState.CREATED

            for player_id in range(1, players + 1):
                self.game.add_player(Player(player_id=player_id))

            for round_num in range(rounds):
                self.game.add_round(
                    Round(round_id=round_num + 1, round_number=round_num + 1, active_player=None)
                )

            self.scenarios = self.create_scenarios(rounds, strategies)
            self.actions = self.create_actions(self.scenarios)

            self.game.scenarios = self.scenarios
            self.game.actions = self.actions
            self.game.root = self.scenarios[0]
            self.game.adjacency = self.adjacency

            self.game.total_scenarios = len(self.scenarios)
            self.game.total_actions = len(self.actions)
            self.game.total_histories = self.calculate_total_histories(rounds, strategies)
            self.game.max_depth = rounds
            self.game.strategies_per_player = strategies
            self.game.num_rounds = rounds
            self.game.num_strategies = strategies

            self.logger.log_info(
                f"Árbol construido: escenarios={len(self.scenarios)}, acciones={len(self.actions)}"
            )

            return self.game

        except Exception as error:
            self.logger.log_error(f"[TreeBuilder] Error inesperado al construir todo el árbol: {error}")
            raise TreeBuilderError(
                technical_message=f"Error técnico al construir todo el árbol: {error}",
                user_message="Error durante la construcción del árbol."
            )

    def get_tree(self) -> Game:
        return self.game