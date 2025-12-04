from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, TYPE_CHECKING

from .exceptions import (
    ConfigurationError, InvalidInputError, ValidationError,
    PlayerOrderError, GameStateError, ComplexityError,
    ProbabilityAssignmentError, HistoryGenerationError,
    UtilityCalculationError, EquilibriumFindingError
)
from ..Core.game import GameState


if TYPE_CHECKING:
    from ..Core.game import Game, GameState
    from ..Core.player import Player


@dataclass
class DomainValidator:
    def validate_player_order_configuration(
        self, 
        player_ids: List[int], 
        game_players: List[Player]
    ) -> None:
        if not player_ids:
            raise InvalidInputError(
                technical_message="La lista de IDs de jugadores está vacía",
                user_message="Debe ingresar al menos un ID de jugador."
            )
        
        if len(player_ids) != len(game_players):
            raise ConfigurationError(
                technical_message=f"Se esperaban {len(game_players)} jugadores, se recibieron {len(player_ids)}",
                user_message=f"Debe ingresar exactamente {len(game_players)} IDs de jugadores."
            )
        
        if len(set(player_ids)) != len(player_ids):
            raise InvalidInputError(
                technical_message="Hay IDs de jugadores duplicados",
                user_message="Los IDs de los jugadores no pueden repetirse."
            )
        
        player_id_map = {player.player_id: player for player in game_players}
        missing_ids = []
        
        for pid in player_ids:
            if pid not in player_id_map:
                missing_ids.append(str(pid))
        
        if missing_ids:
            raise PlayerOrderError(
                technical_message=f"Jugadores con IDs {', '.join(missing_ids)} no encontrados",
                user_message=f"Los jugadores con IDs {', '.join(missing_ids)} no existen en el juego."
            )
        
        if any(pid <= 0 for pid in player_ids):
            raise InvalidInputError(
                technical_message="IDs de jugadores no positivos",
                user_message="Todos los IDs de jugadores deben ser números positivos."
            )

    def validate_game_state_for_configuration(self, game: Game) -> None:
        if game.state != GameState.CREATED:
            raise GameStateError(
                technical_message=f"Juego en estado {game.state}, debe estar CREATED para configuración",
                user_message="Solo se puede configurar el orden en juegos recién creados."
            )

    def _calculate_game_metrics(self, rounds: int, strategies: int) -> Dict[str, Any]:
        try:
            S, E = strategies, rounds
            
            if S == 1:
                total_scenarios = 1
                total_strategies = 1
            else:
                total_scenarios = (S ** E - 1) // (S - 1)
                total_strategies = ((S ** E - S ** 2) // (S - 1)) + 2 * S
            
            # Determinar nivel de complejidad
            if total_scenarios < 100:
                complexity_level = "BAJA"
            elif total_scenarios < 1000:
                complexity_level = "MEDIA"
            elif total_scenarios < 10000:
                complexity_level = "ALTA"
            else:
                complexity_level = "EXTREMA"
            
            return {
                "scenarios": total_scenarios,
                "strategies": total_strategies,
                "complexity_level": complexity_level
            }
            
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            raise ValidationError(
                technical_message=f"Error en cálculo de complejidad: {e}",
                user_message="Error al calcular la complejidad del juego."
            )

    def validate_game_complexity(
        self, 
        rounds: int, 
        strategies: int, 
        max_scenarios: int = 30000, 
        max_strategies: int = 30000
    ) -> Dict[str, Any]:
        metrics = self._calculate_game_metrics(rounds, strategies)
        
        if (metrics["scenarios"] >= max_scenarios or 
            metrics["strategies"] > max_strategies):
            raise ComplexityError(
                scenarios=metrics["scenarios"], 
                strategies=metrics["strategies"]
            )
        
        return {
            "is_valid": True,
            **metrics
        }

    def get_game_complexity_level(self, rounds: int, strategies: int) -> str:
        metrics = self._calculate_game_metrics(rounds, strategies)
        return metrics["complexity_level"]

    def validate_probability_assignments(
        self,
        actions: List[Any],
        values: List[float]
    ) -> None:
        if not actions or not values:
            raise ProbabilityAssignmentError(
                technical_message="Lista de acciones o valores vacía",
                user_message="Debe proporcionar acciones y valores para asignar probabilidades."
            )
        
        if len(actions) != len(values):
            raise ProbabilityAssignmentError(
                technical_message=f"Cantidad de acciones ({len(actions)}) no coincide con valores ({len(values)})",
                user_message="La cantidad de acciones y valores de probabilidad debe coincidir."
            )
        
        for i, value in enumerate(values):
            if value < 0 or value > 1:
                raise ProbabilityAssignmentError(
                    technical_message=f"Valor de probabilidad inválido en posición {i}: {value}",
                    user_message="Los valores de probabilidad deben estar entre 0 y 1."
                )

    def validate_tree_structure(self, tree: Any) -> None:
        if not tree:
            raise HistoryGenerationError(
                technical_message="Árbol nulo",
                user_message="No hay estructura de juego para generar historias."
            )
        
        if not hasattr(tree, 'scenarios') or not tree.scenarios:
            raise HistoryGenerationError(
                technical_message="Árbol sin escenarios",
                user_message="El juego no tiene escenarios definidos."
            )
        
        if not hasattr(tree, 'root') or not tree.root:
            raise HistoryGenerationError(
                technical_message="Árbol sin nodo raíz",
                user_message="El juego no tiene un nodo inicial definido."
            )

    def validate_utility_calculation_data(
        self,
        histories: List[Any],
        payoffs: List[Any]
    ) -> None:
        if not histories:
            raise UtilityCalculationError(
                technical_message="Lista de historias vacía",
                user_message="No hay historias para calcular utilidades."
            )
        
        if not payoffs:
            raise UtilityCalculationError(
                technical_message="Lista de payoffs vacía",
                user_message="No hay pagos para calcular utilidades."
            )
        
        for i, history in enumerate(histories):
            if not hasattr(history, 'total_probability'):
                raise UtilityCalculationError(
                    technical_message=f"Historia {i+1} sin probabilidad total",
                    user_message="Las historias deben tener probabilidades calculadas."
                )
        
        for i, payoff in enumerate(payoffs):
            if not hasattr(payoff, 'history') or not payoff.history:
                raise UtilityCalculationError(
                    technical_message=f"Payoff {i+1} sin historia asociada",
                    user_message="Cada pago debe estar asociado a una historia."
                )
            
            if not hasattr(payoff, 'player') or not payoff.player:
                raise UtilityCalculationError(
                    technical_message=f"Payoff {i+1} sin jugador asociado",
                    user_message="Cada pago debe estar asociado a un jugador."
                )

    def validate_equilibrium_finding_data(
        self,
        game: Any,
        histories: List[Any],
        payoffs: List[Any],
        players: List[Any]
    ) -> None:
        if not game:
            raise EquilibriumFindingError(
                technical_message="Juego nulo",
                user_message="No hay juego para buscar equilibrios."
            )
        
        self.validate_utility_calculation_data(histories, payoffs)
        
        if not players:
            raise EquilibriumFindingError(
                technical_message="Lista de jugadores vacía",
                user_message="No hay jugadores definidos en el juego."
            )
        
        if not hasattr(game, 'scenarios') or not game.scenarios:
            raise EquilibriumFindingError(
                technical_message="Juego sin escenarios",
                user_message="El juego no tiene escenarios definidos."
            )
        
        if not hasattr(game, 'actions') or not game.actions:
            raise EquilibriumFindingError(
                technical_message="Juego sin acciones",
                user_message="El juego no tiene acciones definidas."
            )