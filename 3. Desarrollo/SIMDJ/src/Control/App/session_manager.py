from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from Domain.Core.game import Game, GameState
from Domain.Core.player import Player
from Domain.Core.history import History
from Domain.Core.payoff import Payoff
from Domain.Core.strategy import Strategy
from Domain.Simulation.equilibrium_finder import EquilibriumProfile


from Domain.Common.exceptions import (OperationError)

from Infrastructure.Common.logger import Logger
from Infrastructure.Common.technical_validator import TechnicalValidator


@dataclass
class SessionManager:
    logger: Logger
    technical_validator: TechnicalValidator

    num_players: int = 0
    num_rounds: int = 0
    num_strategies: int = 0
    total_histories: int = 0

    player_order: List[Player] = field(default_factory=list)
    history_list: List[History] = field(default_factory=list)
    utility_matrix: List[List[float]] = field(default_factory=list)
    payoffs: List[Payoff] = field(default_factory=list)
    probabilities: Dict[str, Any] = field(default_factory=dict)
    probability_matrix: List[List[float]] = field(default_factory=list)
    equilibria: List[Strategy] = field(default_factory=list)
    equilibrium_profiles: List[EquilibriumProfile] = field(default_factory=list, repr=False)

    
    temp_histories: List[History] = field(default_factory=list)

    active_game: Optional[Game] = None
    created_at: str = field(default_factory=lambda: 
                           datetime.now().isoformat(timespec="seconds"))

    def initialize_session(self) -> None:
        try:
            self.num_players = 0
            self.num_rounds = 0
            self.num_strategies = 0
            self.total_histories = 0
            self.player_order.clear()
            self.history_list.clear()
            self.utility_matrix.clear()
            self.payoffs.clear()
            self.probabilities.clear()
            self.probability_matrix.clear()
            self.equilibria.clear()
            self.temp_histories.clear()
            self.active_game = None
            self.created_at = datetime.now().isoformat(timespec="seconds")
            
            self.logger.log_info("Sesión inicializada/reiniciada")

        except Exception as error:
            self.logger.log_error(f"Error inicializando sesión: {error}")
            raise OperationError(
                technical_message=f"Error inicializando sesión: {error}",
                user_message="Error al inicializar la sesión del juego."
            )

    def clear_session(self) -> None:
        try:
            self.player_order.clear()
            self.history_list.clear()
            self.utility_matrix.clear()
            self.payoffs.clear()
            self.probabilities.clear()
            self.probability_matrix.clear()
            self.equilibria.clear()
            self.temp_histories.clear()
            self.active_game = None
            
            self.logger.log_info("Sesión limpiada")
            
        except Exception as error:
            self.logger.log_error(f"Error limpiando sesión: {error}")
            raise OperationError(
                technical_message=f"Error limpiando sesión: {error}",
                user_message="Error al limpiar la sesión del juego."
            )

    def update_config(self, players: int, rounds: int, strategies: int) -> None:
        self.technical_validator.validate_positive_integer(players, "número de jugadores")
        self.technical_validator.validate_positive_integer(rounds, "número de rondas")
        self.technical_validator.validate_positive_integer(strategies, "número de estrategias")
        
        self.num_players = players
        self.num_rounds = rounds
        self.num_strategies = strategies
        
        self.logger.log_info(
            f"Configuración actualizada: {players} jugadores, "
            f"{rounds} rondas, {strategies} estrategias"
        )

    def set_player_order(self, order: List[Player]) -> None:
        self.technical_validator.validate_list_not_empty(order, "orden de jugadores")
        self.player_order = list(order)
        self.logger.log_info(f"Orden de jugadores establecido: {len(order)} jugadores")

    def set_active_game(self, game: Game) -> None:
        self.active_game = game
        self.logger.log_info(f"Juego activo establecido: {game.game_id}")

    def get_active_game(self) -> Optional[Game]:
        return self.active_game

    def has_active_game(self) -> bool:
        return self.active_game is not None

    def update_game_state(self, new_state: GameState) -> None:
        if not self.active_game:
            raise ValueError("No hay juego activo para actualizar estado")

        self.active_game.state = new_state
        self.logger.log_info(f"Estado del juego actualizado: {new_state.value}")

    def save_histories(self, histories: List[History]) -> None:
        self.technical_validator.validate_list_not_empty(histories, "historias")
        self.history_list = list(histories)
        self.logger.log_info(f"{len(histories)} historias guardadas en sesión")

    def save_temp_histories(self, temp_histories: List[History]) -> None:
        self.technical_validator.validate_list_not_empty(temp_histories, "historias temporales")
        self.temp_histories = list(temp_histories)
        self.logger.log_info(f"{len(temp_histories)} historias temporales guardadas")

    def save_utility_matrix(self, utilities: List[List[float]]) -> None:
        self.technical_validator.validate_list_not_empty(utilities, "matriz de utilidades")
        self.utility_matrix = [list(row) for row in utilities]
        self.logger.log_info("Matriz de utilidades guardada en sesión")

    def save_payoffs(self, payoffs: List[Payoff]) -> None:
        self.technical_validator.validate_list_not_empty(payoffs, "payoffs")
        self.payoffs = list(payoffs)
        self.logger.log_info(f"{len(payoffs)} payoffs guardados en sesión")

    def save_probabilities(self, probabilities: Dict[str, Any]) -> None:
        self.technical_validator.validate_list_not_empty(probabilities, "Probabilidades")
        self.probabilities = dict(probabilities)
        self.logger.log_info("Probabilidades guardadas en sesión")

    def save_equilibria(self, equilibria: List[Strategy]) -> None:
        self.technical_validator.validate_list_not_empty(equilibria, "Equilibrios")        
        self.equilibria = list(equilibria)
        self.logger.log_info(f"{len(equilibria)} equilibrios guardados en sesión")

    def save_equilibrium_profiles(self, profiles: List[EquilibriumProfile]) -> None:
        self.technical_validator.validate_list_not_empty(profiles, "perfiles de equilibrio")
        self.equilibrium_profiles = list(profiles)
        self.logger.log_info(f"{len(profiles)} perfiles de equilibrio guardados en sesión")

    def get_equilibrium_profiles(self) -> List[EquilibriumProfile]:
        return list(self.equilibrium_profiles)

    def get_summary(self) -> Dict[str, Any]:
        try:
            game_state = None
            if self.active_game:
                game_state = self.active_game.state.value

            player_summaries = []
            for player in self.player_order:
                if hasattr(player, 'get_summary'):
                    player_summaries.append(player.get_summary())
                else:
                    player_summaries.append({
                        "player_id": getattr(player, 'player_id', 'N/A'),
                        "name": getattr(player, 'name', 'N/A')
                    })

            utility_rows = len(self.utility_matrix)
            utility_cols = len(self.utility_matrix[0]) if self.utility_matrix and len(self.utility_matrix) > 0 else 0
            
            return {
                "created_at": self.created_at,
                "config": {
                    "players": self.num_players,
                    "rounds": self.num_rounds,
                    "strategies": self.num_strategies,
                },
                "has_active_game": self.has_active_game(),
                "active_game_state": game_state,
                "player_order": player_summaries,
                "total_histories_expected": self.total_histories,
                "total_histories_generated": len(self.history_list),
                "total_temp_histories": len(self.temp_histories),
                "total_payoffs": len(self.payoffs),
                "total_equilibria": len(self.equilibria),
                "has_probabilities": bool(self.probabilities or self.probability_matrix),
                "utility_shape": (utility_rows, utility_cols),
                "has_utilities": utility_rows > 0,
                "has_histories": len(self.history_list) > 0
            }
            
        except Exception as error:
            self.logger.log_error(f"Error generando resumen de sesión: {error}")
            raise OperationError(
                technical_message=f"Error generando resumen de sesión: {error}",
                user_message="Error al obtener el resumen de la sesión."
            )
