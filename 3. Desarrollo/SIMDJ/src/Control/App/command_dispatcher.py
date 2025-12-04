from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Callable, Any

from .game_controller import GameController
from Infrastructure.Common.logger import Logger
from Infrastructure.Common.technical_validator import TechnicalValidator


from Domain.Common.exceptions import GameException, OperationError


@dataclass
class CommandDispatcher:
    logger: Logger
    technical_validator: TechnicalValidator
    game_controller: GameController
    
    routes: Dict[str, Callable[..., Any]] = None

    def __post_init__(self) -> None:

        self.routes = {
            # ===========================================================
            # CU-01 — Crear Juego y Registrar Payoffs
            # ===========================================================
            "create_game": self.game_controller.create_game,
            "register_payoffs": self.game_controller.register_payoffs,
            "get_game_summary": self.game_controller.get_game_summary,
            "get_player_order_preview": self.game_controller.get_player_order_preview,

            # ===========================================================
            # CU-02 — Configurar Orden y Gestión del Juego
            # ===========================================================
            "configure_order": self.game_controller.configure_order,
            "delete_game": self.game_controller.delete_game,
            "get_players_for_order": self.game_controller.get_players_for_order,
            
            # ===========================================================
            # CU-03 — Visualizar Árbol
            # ===========================================================
            "show_tree": self.game_controller.show_tree,

            # ===========================================================
            # CU-04 — Asignar Probabilidades
            # ===========================================================
            "assign_prob": self.game_controller.assign_probabilities,
            "normalize_prob": self.game_controller.normalize_probabilities,
            "get_scenarios_for_probability_assignment": (
                self.game_controller.get_scenarios_for_probability_assignment
            ),
            "save_probabilities_summary": self.game_controller.save_probabilities_summary,
            "finalize_probability_assignment": self.game_controller.finalize_probability_assignment,
            "update_game_state": self.game_controller.update_game_state,

            # ===========================================================
            # CU-05 — Generar Historias
            # ===========================================================
            "generate_histories": self.game_controller.generate_histories,
            "get_histories_samples": self.game_controller.get_histories_samples,


            # ===========================================================
            # CU-06 — Calcular Utilidades y Equilibrios
            # ===========================================================
            "calculate_utilities": self.game_controller.calculate_utilities,
            "identify_equilibria": self.game_controller.identify_equilibria,
            "finalize_utilities_calculation": self.game_controller.finalize_utilities_calculation,

            # ===========================================================
            # CU-07 — Exportar Datos
            # ===========================================================
            "export_complete_results": self.game_controller.export_complete_results,


        }

    def execute(self, command: str, *args, **kwargs) -> Any:
        handler = self.routes.get(command)

        if handler is None:
            error_message = f"Comando desconocido: {command}"
            self.logger.log_error(error_message)
            raise ValueError(error_message)
        
        try:
            self.logger.log_info(f"Ejecutando comando: {command}")
            result = handler(*args, **kwargs)
            self.logger.log_info(f"Comando '{command}' ejecutado exitosamente")
            return result
            
        except GameException as error:
            self.logger.log_warning(f"Comando '{command}' falló: {error.user_message}")
            raise
        except Exception as error:
            error_message = f"Comando '{command}' falló: {error}"
            self.logger.log_error(error_message)
            raise OperationError(
                technical_message=error_message,
                user_message="Error inesperado durante la ejecución del comando."
            )