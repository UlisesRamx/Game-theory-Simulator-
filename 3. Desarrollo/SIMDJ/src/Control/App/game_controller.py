from __future__ import annotations
from typing import Any, List, Optional, Dict, Sequence
from datetime import datetime


from Control.App.session_manager import SessionManager

from Infrastructure.Common.logger import Logger

from Infrastructure.Common.technical_validator import TechnicalValidator

from Domain.Core.game import Game, GameState
from Domain.Core.player import Player
from Domain.Core.history import History
from Domain.Core.scenario import Scenario
from Domain.Core.action import Action
from Domain.Core.strategy import Strategy
from Domain.Core.payoff import Payoff
from Domain.Common.domain_validator import DomainValidator
from Domain.Common.exceptions import (
    NoActiveGameError,OperationError,GameException, 
    TreeExporterNotConfiguredError, GameCreationError, MissingValueError
)

from Domain.Simulation.tree_builder import TreeBuilder
from Domain.Simulation.probability_assigner import ProbabilityAssigner
from Domain.Simulation.history_generator import HistoryGenerator
from Domain.Simulation.utility_calculator import UtilityCalculator
from Domain.Simulation.equilibrium_finder import EquilibriumFinder

from Infrastructure.Export.excel_exporter import ExcelExporter
from Infrastructure.Export.tree_exporter import TreeExporter




class GameController:
    def __init__(
        self,
        logger: Logger,
        technical_validator: TechnicalValidator,
        excel_exporter: ExcelExporter,
        tree_exporter: TreeExporter,
        domain_validator: DomainValidator,
        tree_builder: TreeBuilder,
        probability_assigner: ProbabilityAssigner,
        history_generator: HistoryGenerator,
        utility_calculator: UtilityCalculator,
        equilibrium_finder: EquilibriumFinder,
        session: SessionManager,
    ):
        self.logger = logger
        self.technical_validator = technical_validator
        self.excel_exporter = excel_exporter
        self.tree_exporter = tree_exporter
        self.domain_validator = domain_validator
        self.tree_builder = tree_builder
        self.probability_assigner = probability_assigner
        self.history_generator = history_generator
        self.utility_calculator = utility_calculator
        self.equilibrium_finder = equilibrium_finder
        self.session = session

        self._last_equilibria: List[Strategy] = []
        
        self._matrix_state: Dict[int, Dict[str, int]] = {}
        self._matrix_rows_per_page: int = 10
        self._matrix_cols_per_page: int = 6

        if not self.session.has_active_game():
            self.session.initialize_session()

    #Listo  - Auxiliar
    def get_game_summary(self) -> Dict[str, Any]:
        if not self.session.has_active_game():
            return {"has_active_game": False}
        
        session_summary = self.session.get_summary()
        player_order_ids = []

        for player in self.session.player_order:
            if hasattr(player, 'player_id'):
                player_order_ids.append(player.player_id)
            elif isinstance(player, (int, str)):
                player_order_ids.append(int(player))
            else:
                player_order_ids.append(len(player_order_ids) + 1)
        
        return {
            "has_active_game": True,
            "config": {
                "players": self.session.num_players,
                "rounds": self.session.num_rounds,
                "strategies": self.session.num_strategies
            },
            "player_order": player_order_ids,
            "total_histories": self.session.total_histories,
            "game_state": session_summary["active_game_state"],
            "created_at": self.session.created_at,
            "total_payoffs": len(self.session.payoffs),
            "has_payoffs": len(self.session.payoffs) > 0,
            "has_utilities": len(self.session.utility_matrix) > 0,
            "utility_shape": session_summary.get("utility_shape", (0, 0)),
            "total_utilities": len(self.session.utility_matrix),
            "total_histories_generated": len(self.session.history_list),
            "has_histories": len(self.session.history_list) > 0
        }

    def create_game(self, num_players: int, num_rounds: int, num_strategies: int) -> bool:
        try:
            self.technical_validator.validate_positive_integer(num_players, "número de jugadores")
            self.technical_validator.validate_positive_integer(num_rounds, "número de rondas")
            self.technical_validator.validate_positive_integer(num_strategies, "número de estrategias")
            
            self.domain_validator.validate_game_complexity(num_rounds, num_strategies)
            
            game = self.tree_builder.build_tree(num_players, num_rounds, num_strategies)
            
            if not game:
                raise GameCreationError(
                    technical_message="Fallo en la construcción del árbol del juego",
                    user_message="Error al crear la estructura del juego. Intente con parámetros diferentes."
                )
            
            self.session.update_config(num_players, num_rounds, num_strategies)
            
            players = game.players
            cyclic_order = self._generate_cyclic_player_order(players, num_rounds)
            self.session.set_player_order(cyclic_order)
            self.session.set_active_game(game)
            
            self.session.total_histories = self.tree_builder.calculate_total_histories(
                num_rounds, num_strategies
            )
            
            game.state = GameState.CREATED
            
            self.logger.log_info(
                f"[CU-01] Juego creado exitosamente: "
                f"{num_players} jugadores, {num_rounds} rondas, {num_strategies} estrategias"
            )
            
            return True
        
        except GameException as error:
            self.logger.log_warning(f"[CU-01] Validación falló: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-01] Error inesperado: {error}")
            raise OperationError(
                technical_message=f"Error técnico durante la creación del juego: {error}",
                user_message="Error durante la creación del JUEGO. Intente nuevamente."
            )

    def register_payoffs(self, payoffs_matrix: List[List[float]]) -> Dict[str, Any]:
        try:
            game = self._validate_active_game()
                
            players = game.players
            payoffs_objects = []
            payoff_id = 1

            temp_histories = []
            for history_idx in range(len(payoffs_matrix)):
                temp_history = History(
                    history_id=history_idx + 1,
                    actions=[],
                    total_probability=0.0,
                    description=f"Historia temporal {history_idx + 1} para payoff"
                )
                temp_histories.append(temp_history)

            for history_idx, payoff_vector in enumerate(payoffs_matrix):
                for player_idx, payoff_value in enumerate(payoff_vector):
                    if player_idx < len(players):
                        payoff = Payoff(
                            payoff_id=payoff_id,
                            player=players[player_idx],
                            history=temp_histories[history_idx],
                            value=payoff_value
                        )
                        payoffs_objects.append(payoff)
                        payoff_id += 1


            self.session.save_payoffs(payoffs_objects)
            self.session.save_temp_histories(temp_histories)
            game.payoffs = list(payoffs_objects)
            
            for history in temp_histories:
                if history not in game.histories:
                    game.histories.append(history)
            
            preview = self._generate_payoffs_preview(payoffs_matrix)
            
            self.logger.log_info(f"[CU-01] {len(payoffs_objects)} payoffs registrados exitosamente")
            
            return {
                "success": True, 
                "preview": preview,
                "total_payoffs": len(payoffs_objects)
            }
        except GameException as error:
            self.logger.log_warning(f"[CU-01] Validación falló: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-01] Error inesperado: {error}")
            raise OperationError(
                technical_message=f"Error registrando payoffs: {error}",
                user_message="No se pudieron registrar correctamente los pagos."
            )

    #Listo  - Auxiliar
    def _generate_payoffs_preview(self, payoffs_matrix: List[List[float]]) -> str:
        preview_lines = []
        for idx, payoff_vector in enumerate(payoffs_matrix, start=1):
            payoffs_str = ', '.join([
                f'|J{j+1}-[ {value}]|' for j, value in enumerate(payoff_vector)
            ])
            preview_lines.append(f"Historia {idx}: {payoffs_str}")
        return "\n".join(preview_lines)
    
    #Listo  - Auxiliar
    def _generate_cyclic_player_order(self, players: List[Player], rounds: int) -> List[Player]:
        return [players[round_num % len(players)] for round_num in range(rounds)]

    #Listo  - Auxiliar
    def get_player_order_preview(self, players: int, rounds: int) -> List[str]:
        order = []
        for round_num in range(rounds):
            player_id = (round_num % players) + 1
            order.append(f"J{player_id}")
        return order

    def configure_order(self, player_ids: List[int]) -> bool:  
        try:
            game = self._validate_active_game()

            self.technical_validator.validate_list_not_empty(player_ids, "lista de jugadores")
            
            for pid in player_ids:
                self.technical_validator.validate_positive_integer(pid, "ID de jugador")
            
            self.domain_validator.validate_game_state_for_configuration(game)
            self.domain_validator.validate_player_order_configuration(player_ids, game.players)
            
            player_id_map = {player.player_id: player for player in game.players}
            player_objects = [player_id_map[pid] for pid in player_ids]
            
            self.session.set_player_order(player_objects)
            
            rounds = game.rounds
            for round_index, game_round in enumerate(rounds):
                if round_index < len(player_objects):
                    game_round.active_player = player_objects[round_index]
                else:
                    player_index = round_index % len(player_objects)
                    game_round.active_player = player_objects[player_index]
            
            game.state = GameState.CREATED
            self.logger.log_info(f"[CU-02] Orden configurado: {player_ids}")
            return True
            
        except GameException as error:
            self.logger.log_warning(f"[CU-02] Error durante la configuración del orden de jugadores: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-02] Error inesperado: {error}")
            raise OperationError(
                technical_message=f"Error durante la configuración del orden: {error}",
                user_message="Error durante la actualización del orden de los Jugadores."
            )
        
    #Listo  - Auxiliar
    def get_players_for_order(self) -> Dict[str, Any]:
        game = self.session.get_active_game()

        if not game:
            return {"players_list": []}
        
        players = game.players
        players_list = [f"J{player.player_id}" for player in players]

        return {
            "players_list": players_list,
            "total_players": len(players)
        }

    #Listo - Auxiliar
    def _validate_active_game(self) -> Game:
        game = self.session.get_active_game()
        if not game:
            raise NoActiveGameError ()
        return game

    #Listo - Checar, solo limpia la sesión pero tal cual no elimina los juegos ni nada de los datos generados, regresando a la
    #estado base todo limpio puej.
    def delete_game(self) -> bool:
        try:
            self._validate_active_game()
            self.session.clear_session()
            self.logger.log_info("[CU-02] Juego eliminado correctamente")
            return True

        except GameException as error:
            self.logger.log_warning(f"[CU-02] Error durante la eliminación del juego: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-02] Error inesperado durante la eliminación del juego: {error}")
            raise OperationError(
                technical_message=f"Error durante la eliminación del juego: {error}",
                user_message="Error durante la eliminación del JUEGO."
            )

    def show_tree(self) -> str:
        try:
            game = self._validate_active_game()

            if not self.tree_exporter:
                raise TreeExporterNotConfiguredError()

            tree_path = self.tree_exporter.export_tree(game)
            self.logger.log_info("[CU-03] SVG de Árbol generado correctamente")
            return tree_path
        
        except GameException as error:
            self.logger.log_warning(f"[CU-03] Error durante la exportación del SVG de Árbol: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-03] Error inesperado durante la exportación del SVG de Árbol: {error}")
            raise OperationError(
                technical_message=f"Error durante la exportación del SVG de Árbol: {error}",
                user_message="Error durante la la exportación del SVG de Árbol."
            )        

    def assign_probabilities(self, scenario_index: int, action_labels: List[str], 
                            values: List[float]) -> bool:
        try:
            game = self._validate_active_game()
            
            scenario = self._get_scenario_by_index(game, scenario_index)
            actions = self._get_actions_by_labels(game, action_labels)

            if len(actions) != len(values):
                raise ValueError("Número de acciones y valores no coinciden")

            self.probability_assigner.assign_probabilities(actions, values)
            
            if not self.probability_assigner.validate_probabilities(scenario):
                raise ValueError("Probabilidades inválidas para el escenario")
            
            self.logger.log_info(f"[CU-04] Probabilidades asignadas: asignadasal escenario {scenario_index}: {values}")
            return True
            
        except GameException as error:
            self.logger.log_warning(f"[CU-04] Error asignando probabilidades: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-04] Error inesperado durante la asignación de probabilidades: {error}")
            raise OperationError(
                technical_message=f"Error asignando probabilidades: {error}",
                user_message="Error durante la asignación de probabilidades."
            )   

    def normalize_probabilities(self, action_labels: List[str], values: List[float]) -> List[float]:
        try:
            game = self._validate_active_game()
            
            actions = self._get_actions_by_labels(game, action_labels)
            
            if len(actions) != len(values):
                raise ValueError("Número de acciones y valores no coinciden")
                    
            self.probability_assigner.assign_probabilities(actions, values)
            self.probability_assigner.normalize_probabilities(actions)
            
            normalized_probabilities = [
                self.probability_assigner.get_probability(action) 
                for action in actions
            ]
            
            self.logger.log_info(f"[CU-04] Probabilidades normalizadas: {normalized_probabilities}")
            return normalized_probabilities
    
        except GameException as error:
            self.logger.log_warning(f"[CU-04] Error normalizando probabilidades: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-04] Error inesperado durante la normalización de probabilidades: {error}")
            raise OperationError(
                technical_message=f"Error anormalizando probabilidades: {error}",
                user_message="Error durante la normalización de probabilidades."
            )   

    def get_scenarios_for_probability_assignment(self) -> Dict[str, Any]:
        try:
            game = self._validate_active_game()
            
            scenarios_data = []
            for scenario in game.scenarios:
                if scenario.outgoing_actions:
                    action_labels = [action.label for action in scenario.outgoing_actions]
                    scenarios_data.append(action_labels)
            
            return {
                "has_scenarios": len(scenarios_data) > 0,
                "scenarios": scenarios_data,
                "total_scenarios": len(scenarios_data)
            }
        
        except GameException as error:
            self.logger.log_warning(f"[CU-04] Error obteniendo escenarios: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-04] Error inesperado durante la obtención de escenarios: {error}")
            raise OperationError(
                technical_message=f"Error anormalizando probabilidades: {error}",
                user_message="Error durante la obtención de escenarios."
            )  

    def save_probabilities_summary(self) -> bool:
        try:
            game = self._validate_active_game()
            
            summary = self.probability_assigner.get_probabilities_summary(game)
            self.session.save_probabilities(summary)
            
            self.logger.log_info("[CU-04] Resumen de probabilidades guardado")
            return True

        except GameException as error:
            self.logger.log_warning(f"[CU-04] Error guardando resumen de probabilidades: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-04] Error inesperado durante el guardado del resumen de probabilidades: {error}")
            raise OperationError(
                technical_message=f"Error anormalizando probabilidades: {error}",
                user_message="Error durante el guardado del resumen de probabilidades."
            )  

    def _get_actions_by_labels(self, game: Game, action_labels: List[str]) -> List[Action]:
        action_map = {action.label: action for action in game.actions}
        
        actions = []
        for label in action_labels:
            if label not in action_map:
                raise MissingValueError(f"Acción '{label}' no encontrada en el juego")
            actions.append(action_map[label])
        
        return actions

    def _get_scenario_by_index(self, game: Game, scenario_index: int) -> Scenario:
        scenarios_with_actions = [
            scenario for scenario in game.scenarios 
            if scenario.outgoing_actions
        ]
        
        if not (1 <= scenario_index <= len(scenarios_with_actions)):
            raise ValueError(f"Índice de escenario inválido: {scenario_index}")
        
        return scenarios_with_actions[scenario_index - 1]

    def update_game_state(self, state_str: str) -> bool:
        try:
            game_state = GameState[state_str.upper()]
            self.session.update_game_state(game_state)
            self.logger.log_info(f"Estado del juego actualizado a: {game_state.value}")
            return True
        
        except KeyError:
            valid_states = [state.value for state in GameState]
            self.logger.log_error(f"Estado de juego inválido: {state_str}. Válidos: {valid_states}")
            return False
        
        except OperationError:
            return False

    def finalize_probability_assignment(self) -> Dict[str, Any]:
        try:
            save_ok = self.save_probabilities_summary()
            if not save_ok:
                raise GameException("No se pudieron guardar las probabilidades.")
            
            # 2. Actualizar estado del juego a RUNNING
            update_ok = self.update_game_state("RUNNING")
            if not update_ok:
                raise GameException("No se pudo actualizar el estado del juego.")

            return True
                    
        except GameException as error:
            self.logger.log_warning(f"[CU-04] Error guardando resumen de probabilidades: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-04] Error inesperado durante el guardado del resumen de probabilidades: {error}")
            raise OperationError(
                technical_message=f"Error anormalizando probabilidades: {error}",
                user_message="Error durante el guardado del resumen de probabilidades."
            )  

    # ==========================================================
    # CU-05 — GENERAR HISTORIAS
    # ==========================================================
    #Listo
    def generate_histories(self) -> Dict[str, Any]:
        try:
            game = self._validate_active_game()
            
            self._validate_game_state_for_histories(game)
            
            histories = self.history_generator.generate_histories(game)

            self.session.save_histories(histories)
            game.histories = list(histories)
            
            self._assign_histories_to_payoffs()

            self.logger.log_info(f"[CU-05] {len(histories)} historias generadas correctamente")
            return {
                "success": True, 
                "total_histories": len(histories),
                "histories": histories
            }

        except GameException as error:
            self.logger.log_warning(f"[CU-05] Error generando historias: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-05] Error inesperado durante la generación de historias: {error}")
            raise OperationError(
                technical_message=f"Error generando historias: {error}",
                user_message="Error durante el generar las historias."
            )         

    #Listo
    def get_histories_samples(self) -> Dict[str, Any]:
        try:
            histories = self.session.history_list
            if not histories:
                raise MissingValueError(
                    technical_message="La lista de Historias esta vacia",
                    user_message="No se han encontrado historias en la sesión actual."
                )
                
            formatted_samples = self._format_histories_for_cli(histories)
            
            return {
                "total": len(histories),
                "samples": formatted_samples
            }
            
        except GameException as error:
            self.logger.log_warning(f"[CU-05] Error al generar una muestra de las historias generadas: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-05] Error inesperado durante la generación de la muestra de historias generadas: {error}")
            raise OperationError(
                technical_message=f"Error al generar una muestra de las historias: {error}",
                user_message="Error durante la generación de la muestra de historias generadas."
            ) 

    #Listo - Ojo, recuerda checar lo de las validaciones
    def _validate_game_state_for_histories(self, game: Game) -> None:
        if game.state != GameState.RUNNING:
            raise ValueError("El juego no está en estado RUNNING")

    #Listo
    def _assign_histories_to_payoffs(self) -> bool:
        try:
            histories = self.session.history_list
            payoffs = self.session.payoffs
            
            if not histories:
                self.logger.log_info("No hay Historias para asignar payoff")
                raise MissingValueError("No hay Historias para asignar payoff")            
            if not payoffs:
                self.logger.log_info("No hay payoffs para asignar historias")
                raise MissingValueError("No hay payoffs para asignar historias")
                    
            players = self.session.player_order
            players_count = len(players)
            
            expected_payoffs = len(histories) * players_count
            if len(payoffs) != expected_payoffs:
                self.logger.log_warning(
                    f"Número de payoffs ({len(payoffs)}) no coincide con "
                    f"historias×jugadores ({len(histories)}×{players_count} = {expected_payoffs})"
                )
                raise ValueError(
                    f"Número de payoffs ({len(payoffs)}) no coincide con "
                    f"historias×jugadores ({len(histories)}×{players_count} = {expected_payoffs})")
            
            for payoff_index, payoff in enumerate(payoffs):
                history_index = payoff_index // players_count
                player_index = payoff_index % players_count
                
                if history_index < len(histories):
                    payoff.history = histories[history_index]
                    
                    if player_index < len(players):
                        payoff.player = players[player_index]
                        
                    if hasattr(payoff.history, 'total_probability'):
                        payoff.calculate_expected_utility(payoff.history.total_probability)
            
            game = self._validate_active_game()
            game.payoffs = list(payoffs)

            self.logger.log_info(
                f"[CU-05] {len(payoffs)} payoffs asignados a {len(histories)} historias"
            )
            return True
            
        except Exception as error:
            raise OperationError(
                technical_message=f"Error asignando historias a payoffs: {error}",
                user_message="Error durante la asiganación de hsitorias al payoff"
            )

    #Listo
    def _format_histories_for_cli(self, histories_samples: List[History]) -> str:
        formatted_lines = []
        for index, history in enumerate(histories_samples, start=1):
            action_descriptions = [
                f"{action.label}-{{{action.probability:.1f}}}" 
                for action in history.actions
            ]
            formatted_lines.append(
                f"HISTORIA {index} -> [{', '.join(action_descriptions)}] -> "
                f"P = {history.total_probability:.3f}"
            )
        return "\n".join(formatted_lines)

    # ==========================================================
    # CU-06 — CALCULAR UTILIDADES Y EQUILIBRIOS
    # ==========================================================
    #Listo
    def calculate_utilities(self) -> Dict[str, Any]:
        try:
            game = self._validate_active_game()
            
            self._validate_utilities_prerequisites(game)
            
            self._assign_histories_to_payoffs()
            
            utilities = self.utility_calculator.calculate_utilities(game.histories, game.payoffs)
            
            self._validate_utilities_result(game, utilities)
            
            self.session.save_utility_matrix(utilities)
            
            utility_lines = self._format_utilities_for_cli(game.histories, utilities)
            
            self.logger.log_info(f"[CU-06] Utilidades calculadas para {len(utilities)} historias")

            update_ok = self.update_game_state("RUNNING")
            if not update_ok:
                raise GameException("No se pudo actualizar el estado del juego.")
            return {
                "success": True, 
                "utilities": utilities,
                "utility_lines": utility_lines
            }
        
        except GameException as error:
            self.logger.log_warning(f"[CU-06] Error durante el calcúlo de utilidades: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-06] Error inesperado durante el calcúlo de utilidades: {error}")
            raise OperationError(
                technical_message=f"Error durante el calcúlo de utilidades: {error}",
                user_message="Error durante el calcúlo de utilidades."
            ) 

    #Listo
    def _validate_utilities_prerequisites(self, game: Game) -> None:
        if not game.histories or len(game.histories) == 0:
            raise MissingValueError(
                technical_message="No hay historias generadas",
                user_message="Debe generar historias primero."
            )
        
        if not game.payoffs or len(game.payoffs) == 0:
            raise MissingValueError(
                technical_message="No hay payoffs registrados",
                user_message="Debe registrar los payoffs primero."
            )
        #Checar esto
        if game.state != GameState.RUNNING:
            raise ValueError("El juego no está en estado RUNNING")

    #Listo
    def _validate_utilities_result(self, game: Game, utilities: List[List[float]]) -> None:
        if not utilities or len(utilities) == 0:
            raise ValueError("El cálculo de utilidades no produjo resultados")
        
        if len(utilities) != len(game.histories):
            raise ValueError(
                f"Número de utilidades ({len(utilities)}) no coincide con "
                f"número de historias ({len(game.histories)})"
            )
        
        # Validar que cada historia tenga utilidades para todos los jugadores
        num_players = len(game.players)
        for i, history_utilities in enumerate(utilities):
            if len(history_utilities) != num_players:
                raise ValueError(
                    f"Historia {i+1}: número de utilidades ({len(history_utilities)}) "
                    f"no coincide con número de jugadores ({num_players})"
                )

    #Listo
    def _format_utilities_for_cli(
        self, 
        histories: List[History], 
        utilities: List[List[float]]
    ) -> List[str]:
        lines = []
        
        for history_index, history in enumerate(histories):
            if history_index < len(utilities):
                utility_values = utilities[history_index]
                
                action_labels = " -> ".join([
                    action.label for action in history.actions[:3]
                ])
                if len(history.actions) > 3:
                    action_labels += " -> ..."
                    
                player_utilities = " | ".join([
                    f"J{player_index + 1}={utility:.3f}" 
                    for player_index, utility in enumerate(utility_values)
                ])
                probability_info = f"P={history.total_probability:.4f}"
                
                lines.append(
                    f"Historia {history_index + 1}: {action_labels} | "
                    f"{probability_info} | {player_utilities}"
                )
            else:
                lines.append(f"Historia {history_index + 1}: [SIN UTILIDADES CALCULADAS]")
        
        return lines



    #Listo
    def identify_equilibria(self) -> Dict[str, Any]:
        try:
            game = self._validate_active_game()
            
            self._validate_equilibria_prerequisites(game)
            
            equilibria = self.equilibrium_finder.find_spe_profiles(
                game, game.histories, game.payoffs, game.players
            )
            
            equilibrium_profiles = self.equilibrium_finder.get_equilibrium_profiles()
            
            self.session.save_equilibrium_profiles(equilibrium_profiles)
            
            equilibria_pages = []
            
            for i, profile in enumerate(equilibrium_profiles, 1):
                profile_lines = self.equilibrium_finder.format_equilibrium_profile(
                    profile, i, len(equilibrium_profiles)
                )
                equilibria_pages.append(profile_lines)
            
            self.session.save_equilibria(equilibria)
            
            self.logger.log_info(f"[CU-06] {len(equilibrium_profiles)} equilibrios identificados")
            return {
                "success": True,
                "equilibria": equilibria,
                "equilibria_profiles": equilibrium_profiles,
                "equilibria_pages": equilibria_pages,
                "total_equilibria": len(equilibrium_profiles)
            }
        except GameException as error:
            self.logger.log_warning(f"[CU-06] Error identificando equilibrios: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-06] Error inesperado durante la identificación de equilibrios: {error}")
            raise OperationError(
                technical_message=f"Error identificando equilibrios: {error}",
                user_message="Error durante la identificación de equilibrios."
            )

    def _validate_equilibria_prerequisites(self, game: Game) -> None:
        if not game.histories or len(game.histories) == 0:
            raise MissingValueError(
                technical_message="No hay historias generadas",
                user_message="Debe generar historias primero."
            )
        
        if not game.payoffs or len(game.payoffs) == 0:
            raise MissingValueError(
                technical_message="No hay payoffs registrados",
                user_message="Debe registrar los payoffs primero."
            )
        
        if not self.session.utility_matrix or len(self.session.utility_matrix) == 0:
            raise MissingValueError(
                technical_message="No hay utilidades calculadas",
                user_message="Debe calcular las utilidades primero."
            )


    #Listo
    def finalize_utilities_calculation(self) -> Dict[str, Any]:
        try:
            self._validate_active_game()
            
            if not self.session.utility_matrix or len(self.session.utility_matrix) == 0:
                raise MissingValueError(
                    technical_message="No hay utilidades calculadas para finalizar",
                    user_message="No se han calculado utilidades para finalizar la operación."
                )
            
            update_ok = self.update_game_state("RUNNING")
            if not update_ok:
                raise GameException("No se pudo actualizar el estado del juego.")

            
            self.logger.log_info("[CU-06] Juego marcado como COMPLETED después del cálculo de utilidades")
            return {
                "success": True,
                "message": "Las utilidades han sido calculadas correctamente.\nEl juego ha sido marcado como COMPLETED."
            }
        except GameException as error:
            self.logger.log_warning(f"[CU-06] Error guardando utilidades: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-06] Error inesperado durante el guardado de utilidades: {error}")
            raise OperationError(
                technical_message=f"Error guardando utilidades: {error}",
                user_message="Error durante el guardado de las utilidades en la sesión."
            ) 

#LISTO    # ===============================================================================================================


# En GameController, agrega estos métodos para CU-07:
    # ==========================================================
    # CU-07 — EXPORTAR RESULTADOS COMPLETOS
    # ==========================================================
    def export_complete_results(self) -> Dict[str, Any]:
        try:
            game = self._validate_active_game()
            
            self._validate_export_prerequisites(game)
            
            excel_path = self.excel_exporter.export_complete_game(game, self.session)
            
            stats = self._get_export_statistics(game)
            
            self.logger.log_info(f"[CU-07] Resultados exportados a Excel: {excel_path}")
            return {
                "success": True,
                "file_path": excel_path,
                "statistics": stats,
                "message": f"Resultados exportados correctamente a: {excel_path}"
            }
            
        except GameException as error:
            self.logger.log_warning(f"[CU-07] Error Exportando resultados a excel: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[CU-07] Error inesperado durante la exportación de resultados al excel: {error}")
            raise OperationError(
                technical_message=f"Error Exportando resultados a excel: {error}",
                user_message="Error durante la exportación de resultados al excel."
            ) 

    def _validate_export_prerequisites(self, game: Game) -> None:
        if not game.histories or len(game.histories) == 0:
            raise MissingValueError(
                technical_message="No hay historias generadas para exportar",
                user_message="Debe generar historias primero."
            )
        
        if not game.payoffs or len(game.payoffs) == 0:
            raise MissingValueError(
                technical_message="No hay payoffs registrados para exportar",
                user_message="Debe registrar payoffs primero."
            )
        
        if game.state not in [GameState.COMPLETED, GameState.RUNNING]:
            raise ValueError(
                "El juego debe estar en estado COMPLETED o RUNNING para exportar"
            )

    def _get_export_statistics(self, game: Game) -> Dict[str, Any]:
        return {
            "game_id": game.game_id,
            "total_players": len(game.players),
            "total_rounds": len(game.rounds),
            "total_histories": len(game.histories),
            "total_payoffs": len(game.payoffs),
            "total_utilities": len(self.session.utility_matrix) if self.session.utility_matrix else 0,
            "total_equilibria": len(self.session.equilibria),
            "game_state": game.state.value,
            "export_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        """Método legacy en camelCase."""
        return self.get_scenarios_for_probability_assignment()