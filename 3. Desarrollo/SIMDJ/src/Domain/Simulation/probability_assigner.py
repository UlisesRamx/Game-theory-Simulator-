from __future__ import annotations
from typing import Dict, List

from Domain.Core.action import Action
from Domain.Core.scenario import Scenario
from Domain.Core.game import Game

from Domain.Common.domain_validator import DomainValidator
from Domain.Common.exceptions import (ProbabilityAssignmentError)

from Infrastructure.Common.logger import Logger


class ProbabilityAssigner:
    def __init__(
        self,
        logger: Logger,
        domain_validator: DomainValidator
    ):
        self.probabilities: Dict[int, float] = {}

        self.logger = logger
        self.domain_validator = domain_validator

        self.tolerance: float = 0.001

    def assign_probabilities(
        self, 
        actions: List[Action], 
        values: List[float]
    ) -> None:
        try:
            self.domain_validator.validate_probability_assignments(actions, values)
            
            for action, value in zip(actions, values):
                if value < 0 or value > 1:
                    raise ProbabilityAssignmentError(
                        technical_message=f"Probabilidad inválida en acción {action.label}: {value}",
                        user_message="Los valores de probabilidad deben estar entre 0 y 1."
                    )
                
                probability = float(value)
                self.probabilities[action.action_id] = probability
                action.probability = probability

            self.logger.log_info(
                f"[ProbabilityAssigner] Probabilidades asignadas a {len(actions)} acciones."
            )
            
        except (ProbabilityAssignmentError) as error:
            self.logger.log_warning(f"[ProbabilityAssigner] Error asignando probabilidades: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[ProbabilityAssigner] Error inesperado al asignar probabilidades: {error}")
            raise ProbabilityAssignmentError(
                technical_message=f"Error técnico asignando probabilidades: {error}",
                user_message="Error al asignar probabilidades a las acciones."
            )

    def validate_probabilities(self, scenario: Scenario) -> bool:
        try:
            outgoing = getattr(scenario, "outgoing_actions", [])
            if not outgoing:
                return True

            total = sum(
                self.probabilities.get(action.action_id, action.probability)
                for action in outgoing
            )

            diff = abs(1.0 - total)
            is_valid = diff <= self.tolerance

            if not is_valid:
                raise ProbabilityAssignmentError(
                    technical_message=f"Escenario {scenario.label}: probabilidades suman {total:.6f} (diferencia: {diff:.6f})",
                    user_message=f"Las probabilidades del escenario {scenario.label} no suman 1."
                )

            self.logger.log_info(
                f"[ProbabilityAssigner] Validación escenario {scenario.label}: suma={total:.6f}, ok"
            )
            return True
            
        except ProbabilityAssignmentError:
            raise
        except Exception as error:
            self.logger.log_error(f"[ProbabilityAssigner] Error validando probabilidades: {error}")
            raise ProbabilityAssignmentError(
                technical_message=f"Error validando probabilidades del escenario {scenario.label}: {error}",
                user_message="Error al validar las probabilidades del escenario."
            )

    def normalize_probabilities(self, actions: List[Action]) -> None:
        try:
            total = sum(
                self.probabilities.get(action.action_id, action.probability)
                for action in actions
            )

            if total <= 0:
                raise ProbabilityAssignmentError(
                    technical_message=f"No se puede normalizar un conjunto cuyo total es <= 0: {total}",
                    user_message="No se pueden normalizar probabilidades con suma total cero o negativa."
                )

            for action in actions:
                new_probability = (
                    self.probabilities.get(action.action_id, action.probability) / total
                )
                self.probabilities[action.action_id] = new_probability
                action.probability = new_probability

            self.logger.log_info(
                f"[ProbabilityAssigner] Normalización aplicada a {len(actions)} acciones "
                f"(total previo={total:.6f})."
            )
            
        except ProbabilityAssignmentError:
            raise
        except Exception as error:
            self.logger.log_error(f"[ProbabilityAssigner] Error normalizando probabilidades: {error}")
            raise ProbabilityAssignmentError(
                technical_message=f"Error técnico normalizando probabilidades: {error}",
                user_message="Error al normalizar las probabilidades de las acciones."
            )

    def get_probability(self, action: Action) -> float:
        return self.probabilities.get(action.action_id, action.probability)

    def get_probabilities_for_scenario(
        self, 
        scenario: Scenario
    ) -> Dict[str, float]:
        return {
            action.label: self.probabilities.get(action.action_id, action.probability)
            for action in getattr(scenario, "outgoing_actions", [])
        }

    def clear_probabilities(self) -> None:
        self.probabilities.clear()
        self.logger.log_info("[ProbabilityAssigner] Probabilidades reseteadas.")

    def get_probabilities_summary(
        self, 
        game: Game
    ) -> Dict[str, Dict[str, float]]:
        try:
            summary: Dict[str, Dict[str, float]] = {}

            for scenario in getattr(game, "scenarios", []):
                outgoing = getattr(scenario, "outgoing_actions", [])
                if not outgoing:
                    continue

                summary[scenario.label] = {
                    action.label: self.probabilities.get(action.action_id, action.probability)
                    for action in outgoing
                }

            self.logger.log_info("[ProbabilityAssigner] Resumen generado.")
            return summary
            
        except Exception as error:
            self.logger.log_error(f"[ProbabilityAssigner] Error generando resumen: {error}")
            raise ProbabilityAssignmentError(
                technical_message=f"Error generando resumen de probabilidades: {error}",
                user_message="Error al generar el resumen de probabilidades del juego."
            )