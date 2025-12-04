from __future__ import annotations
import pydot
from pathlib import Path
from typing import Any

from Infrastructure.Export.naming_service import NamingService
from Infrastructure.Common.logger import Logger
from Infrastructure.Common.technical_validator import TechnicalValidator


class TreeExporter:
    def __init__(
        self, 
        logger: Logger, 
        naming_service: NamingService, 
        technical_validator: TechnicalValidator
    ):
        self.logger = logger
        self.naming_service = naming_service
        self.technical_validator = technical_validator
        self.base_export_dir = self._get_base_export_directory()
        self.ensure_export_directory()

    #Listo
    def _get_base_export_directory(self) -> Path:
        current_file = Path(__file__).resolve()
        base_dir = current_file.parent.parent.parent.parent / "Tests" / "Exports" / "Trees"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def export_tree(self, game: Any, format: str = "SVG") -> str:
        if format.upper() != "SVG":
            raise ValueError("Formato no soportado. Solo SVG.")

        players = len(getattr(game, "players", []))
        rounds = len(getattr(game, "rounds", []))
        strategies = getattr(game, "strategies_per_player", None)

        file_name = self._build_file_name(players, rounds, strategies)
        full_path = self.base_export_dir / file_name
        full_path = Path(self.naming_service.resolve_file_conflict(str(full_path)))

        try:
            return self.generate_svg(game, str(full_path))
        except Exception as ex:
            raise

    def generate_svg(self, game: Any, out_file: str) -> str:
        graph = self._build_pydot_from_game(game)
        self._style_pydot_graph(graph)
        graph.write_svg(out_file)
        self.log_export_event(f"Árbol exportado en: {out_file}")
        return out_file

    #Casi-Listo Corregir el formato de los árboles
    def _build_pydot_from_game(self, game: Any) -> pydot.Dot:
        graph = pydot.Dot(graph_type="digraph", rankdir="TB", bgcolor="white")

        for scenario in getattr(game, "scenarios", []):
            label = getattr(scenario, "label", f"X{getattr(scenario, 'scenario_id', '?')}")
            is_terminal = getattr(scenario, "is_terminal", False)
            if callable(is_terminal):
                is_terminal = is_terminal()
            shape = "doublecircle" if is_terminal else "circle"
            graph.add_node(pydot.Node(label, shape=shape))

        for action in getattr(game, "actions", []):
            origin = getattr(action, "origin_scenario", None)
            destination = getattr(action, "destination_scenario", None)
            if not origin or not destination:
                continue

            origin_label = getattr(origin, "label", f"X{getattr(origin, 'scenario_id', '?')}")
            destination_label = getattr(destination, "label", f"X{getattr(destination, 'scenario_id', '?')}")
            action_label = getattr(action, "label", f"a{getattr(action, 'action_id', '?')}")
            probability = getattr(action, "probability", 0.0)

            edge_label = f"{action_label}\n({probability:.3f})" if probability > 0 else action_label
            edge = pydot.Edge(origin_label, destination_label, label=edge_label)
            graph.add_edge(edge)

        return graph

    #Casi-Listo Corregir el formato de los árboles
    def _style_pydot_graph(self, graph: pydot.Dot) -> None:
        graph.set_rankdir("TB")
        graph.set_bgcolor("white")
        graph.set("nodesep", "0.5")
        graph.set("ranksep", "1.0")

    def ensure_export_directory(self) -> None:
        try:
            self.base_export_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.log_error(f"Error creando directorio de exportación: {e}")
            raise

    def _build_file_name(
        self, 
        players: int, 
        rounds: int, 
        strategies: int, 
        prefix: str = "ArbolDecisiones"
    ) -> str:
        prefix_f = self.naming_service.format_prefix(prefix)
        timestamp = self.naming_service.get_timestamp()
        return f"{prefix_f}_J{players}_R{rounds}_E{strategies}_{timestamp}.svg"

    def log_export_event(self, message: str) -> None:
        if self.logger:
            self.logger.log_info(message)

    def _handle_error(self, message: str) -> None:
        if self.logger:
            self.logger.log_error(message)