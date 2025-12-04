from __future__ import annotations
from typing import List, Optional, Dict, Set, Tuple

from Domain.Core.game import Game
from Domain.Core.history import History
from Domain.Core.action import Action
from Domain.Core.scenario import Scenario

from Domain.Common.domain_validator import DomainValidator
from Domain.Common.exceptions import (
    HistoryGenerationError, ValidationError
)

from Infrastructure.Common.logger import Logger


class HistoryGenerator:
    def __init__(
        self,
        logger: Logger,
        domain_validator: DomainValidator
    ):
        self.histories: List[History] = []
        self.tree: Optional[Game] = None
        self.actions: List[Action] = []
        self.path_buffer: List[Action] = []
        self._cycle_guard: Set[Tuple[int, Tuple[int, ...]]] = set()

        self.logger = logger
        self.domain_validator = domain_validator

    def generate_histories(self, tree: Game) -> List[History]:
        try:
            self.clear_histories()
            self.tree = tree

            self.domain_validator.validate_tree_structure(tree)

            self.actions = getattr(tree, "actions", [])
            
            if not self.actions:
                raise HistoryGenerationError(
                    technical_message="Árbol sin acciones definidas",
                    user_message="El juego no tiene acciones para generar historias."
                )

            root: Optional[Scenario] = getattr(tree, "root", None)
            if root is None:
                scenarios = getattr(tree, "scenarios", [])
                root = next((s for s in scenarios if s.depth == 0), None) or \
                       next((s for s in scenarios if s.scenario_id == 0), None)

            if root is None:
                raise HistoryGenerationError(
                    technical_message="No se pudo encontrar el nodo raíz del árbol",
                    user_message="El juego no tiene un nodo inicial definido."
                )

            self.logger.log_info("[HistoryGenerator] Generando historias (DFS)...")

            adjacency: Dict[int, List[Action]] = getattr(tree, "adjacency", {})
            if not adjacency:
                adjacency = self._rebuild_adjacency_from_actions(self.actions)
                self.logger.log_warning(
                    "[HistoryGenerator] adjacency reconstruido desde acciones."
                )

            for scenario_id in adjacency:
                adjacency[scenario_id].sort(key=lambda a: a.action_id)

            self.path_buffer = []
            self._cycle_guard.clear()

            self._dfs(root, adjacency)

            self._calculate_all_probabilities()

            tree.histories = self.histories

            self.logger.log_info(
                f"[HistoryGenerator] {len(self.histories)} historias generadas exitosamente."
            )
            return self.histories
            
        except (HistoryGenerationError, ValidationError) as error:
            self.logger.log_warning(f"[HistoryGenerator] Error generando historias: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[HistoryGenerator] Error inesperado: {error}")
            raise HistoryGenerationError(
                technical_message=f"Error técnico generando historias: {error}",
                user_message="Error al generar las historias del juego."
            )

    def get_histories(self) -> List[History]:
        return list(self.histories)

    def clear_histories(self) -> None:
        self.histories.clear()
        self.path_buffer.clear()
        self._cycle_guard.clear()

    def _dfs(
        self, 
        current: Scenario, 
        adjacency: Dict[int, List[Action]]
    ) -> None:
        try:
            outgoing: List[Action] = adjacency.get(current.scenario_id, [])

            if not outgoing:
                # Nodo terminal, crear historia
                history_id = len(self.histories) + 1
                self.histories.append(
                    History(
                        history_id=history_id,
                        actions=list(self.path_buffer)
                    )
                )
                return

            for action in outgoing:
                if not hasattr(action, "action_id"):
                    self.logger.log_warning(
                        "[HistoryGenerator] Acción sin action_id ignorada."
                    )
                    continue

                destination = getattr(action, "destination_scenario", None)
                if not isinstance(destination, Scenario):
                    self.logger.log_warning(
                        f"[HistoryGenerator] Acción {getattr(action, 'label', action.action_id)} "
                        f"sin destino válido."
                    )
                    continue

                new_path_ids = tuple(
                    a.action_id for a in (self.path_buffer + [action])
                )
                guard_key = (destination.scenario_id, new_path_ids)

                if guard_key in self._cycle_guard:
                    self.logger.log_warning(
                        f"[HistoryGenerator] Ciclo detectado: "
                        f"Scenario {destination.scenario_id}, path={new_path_ids}"
                    )
                    continue

                self._cycle_guard.add(guard_key)
                self.path_buffer.append(action)
                self._dfs(destination, adjacency)
                self.path_buffer.pop()
        except (HistoryGenerationError) as error:
            self.logger.log_warning(
                f"[HistoryGenerator] Error generando historias al hacer una búsqueda de profundidad: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[HistoryGenerator] Error inesperado al hacer una búsqueda de profundidad: {error}")
            raise HistoryGenerationError(
                technical_message=f"Error técnico generando historias al hacer una búsqueda de profundidad: {error}",
                user_message="Error al generar las historias del juego al hacer una búsqueda de profundidad."
            )

    def _calculate_all_probabilities(self) -> None:
        for history in self.histories:
            try:
                history.calculate_probability()
            except Exception as error:
                self.logger.log_warning(
                    f"[HistoryGenerator] Error calculando probabilidad de historia {history.history_id}: {error}"
                )
                raise HistoryGenerationError(
                technical_message=f"Error técnico generando historias: {error}",
                user_message=f"Error calculando probabilidad de historia {history.history_id}"
                )

    def _rebuild_adjacency_from_actions(
        self, 
        actions: List[Action]
    ) -> Dict[int, List[Action]]:
        try:
            adjacency: Dict[int, List[Action]] = {}
            for action in actions:
                origin = getattr(action, "origin_scenario", None)
                if not isinstance(origin, Scenario):
                    continue
                adjacency.setdefault(origin.scenario_id, []).append(action)
            return adjacency
        except Exception as error:
                self.logger.log_warning(
                    f"[HistoryGenerator] Error al reconstruir el diccionario de adyacencia desde las acciones: {error}"
                )
                raise HistoryGenerationError(
                technical_message=f"Error técnico generando historias: {error}",
                user_message="Error al reconstruir el diccionario de adyacencia desde las acciones."
                )



