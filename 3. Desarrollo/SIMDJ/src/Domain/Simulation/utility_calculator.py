from __future__ import annotations
from typing import List, Dict

from Domain.Core.history import History
from Domain.Core.payoff import Payoff
from Domain.Core.player import Player

from Domain.Common.domain_validator import DomainValidator
from Domain.Common.exceptions import (
    UtilityCalculationError, ValidationError
)

from Infrastructure.Common.logger import Logger


class UtilityCalculator:
    def __init__(
        self,
        logger: Logger,
        domain_validator: DomainValidator
    ):
        self.utility_matrix: List[List[float]] = []
        self.histories: List[History] = []
        self.payoffs: List[Payoff] = []

        self.logger = logger
        self.domain_validator = domain_validator

    def validate_data_consistency(self) -> None:
        try:
            self.domain_validator.validate_utility_calculation_data(
                self.histories, self.payoffs
            )

            history_ids = {history.history_id for history in self.histories}
            
            for i, payoff in enumerate(self.payoffs):
                if payoff.history.history_id not in history_ids:
                    raise UtilityCalculationError(
                        technical_message=f"Payoff {i+1} referencia historia {payoff.history.history_id} que no existe",
                        user_message="Hay pagos asociados a historias que no existen."
                    )

                if not hasattr(payoff.history, 'total_probability'):
                    raise UtilityCalculationError(
                        technical_message=f"Historia {payoff.history.history_id} no tiene probabilidad calculada",
                        user_message="Todas las historias deben tener probabilidades calculadas."
                    )

                if payoff.history.total_probability is None:
                    raise UtilityCalculationError(
                        technical_message=f"Historia {payoff.history.history_id} tiene probabilidad total nula",
                        user_message="La probabilidad de las historias no puede ser nula."
                    )

        except (UtilityCalculationError, ValidationError) as error:
            raise
        except Exception as error:
            raise UtilityCalculationError(
                technical_message=f"Error validando datos para cálculo de utilidades: {error}",
                user_message="Error al validar los datos para cálculo de utilidades."
            )

    def calculate_utilities(
        self,
        histories: List[History],
        payoffs: List[Payoff]
    ) -> List[List[float]]:
        try:
            self.histories = histories
            self.payoffs = payoffs

            self.validate_data_consistency()

            players_by_id: Dict[int, Player] = {}
            for payoff in payoffs:
                players_by_id[payoff.player.player_id] = payoff.player

            players: List[Player] = sorted(
                players_by_id.values(), 
                key=lambda player: player.player_id
            )

            num_players = len(players)
            num_histories = len(histories)

            self.utility_matrix = [
                [0.0 for _ in range(num_players)]
                for _ in range(num_histories)
            ]

            payoff_map = {}
            for payoff in payoffs:
                payoff_map[
                    (payoff.player.player_id, payoff.history.history_id)
                ] = payoff.value

            for history_index, history in enumerate(histories):
                probability = history.total_probability or 0.0

                for player_index, player in enumerate(players):
                    payoff_value = payoff_map.get(
                        (player.player_id, history.history_id),
                        0.0
                    )

                    utility_value = payoff_value * probability
                    self.utility_matrix[history_index][player_index] = utility_value

            for payoff in payoffs:
                probability = payoff.history.total_probability or 0.0
                payoff.expected_utility = payoff.value * probability

            self.logger.log_info(
                f"[UtilityCalculator] Matriz de utilidades generada: "
                f"{num_histories} historias × {num_players} jugadores."
            )
            return self.utility_matrix
            
        except (UtilityCalculationError, ValidationError) as error:
            self.logger.log_warning(f"[UtilityCalculator] Error calculando utilidades: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[UtilityCalculator] Error inesperado: {error}")
            raise UtilityCalculationError(
                technical_message=f"Error técnico calculando utilidades: {error}",
                user_message="Error al calcular las utilidades del juego."
            )

    def calculate_expected_utility(self, player: Player) -> float:
        try:
            if not self.utility_matrix:
                raise UtilityCalculationError(
                    technical_message="Matriz de utilidades no calculada",
                    user_message="Debe calcular las utilidades primero."
                )

            total = 0.0
            for payoff in self.payoffs:
                if payoff.player.player_id == player.player_id:
                    probability = payoff.history.total_probability or 0.0
                    total += payoff.value * probability

            return total
            
        except UtilityCalculationError:
            raise
        except Exception as error:
            raise UtilityCalculationError(
                technical_message=f"Error calculando utilidad esperada para jugador {player.player_id}: {error}",
                user_message=f"Error al calcular la utilidad esperada del jugador {player.player_id}."
            )

    def get_utility_matrix(self) -> List[List[float]]:
        return self.utility_matrix

    def print_utility_summary(self) -> None:
        self.logger.log_info("===== UTILITY MATRIX =====")
        if not self.utility_matrix:
            self.logger.log_info("Matriz vacía")
        else:
            for i, row in enumerate(self.utility_matrix):
                self.logger.log_info(f"Historia {i+1}: {row}")
        self.logger.log_info("==========================")

    def clear_utilities(self) -> None:
        self.utility_matrix = []
        self.histories = []
        self.payoffs = []
