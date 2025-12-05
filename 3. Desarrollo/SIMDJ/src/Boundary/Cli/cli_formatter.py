from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence, List


@dataclass(frozen=True)
class Screen:
    title: str
    body: str
    footer: str = ""
    prompt: str = "> "


class CLIFormatter:
    LINE = "----------------------------------------"

    def _clear(self) -> None:
        print("\n" * 80)

    def _display_screen(self, screen: Screen) -> None:
        self._clear()
        print(screen.title)
        print(self.LINE)
        print(screen.body)
        if screen.footer:
            print(self.LINE)
            print(screen.footer)

    def display_message(self, type: str, title: str, msg: str) -> None:
        self._clear()
        match type:
            case "Notification":
                print(f"{self.LINE}\n{title}\n{self.LINE}\n{msg}\n[ENTER] Continuar\n{self.LINE}")
            case "Question":
                print(f"{self.LINE}\n{msg}")
            case "Error":
                print(f"{self.LINE}\nError:\n{title}\n{self.LINE}\n{msg}\n[ENTER] Continuar\n{self.LINE}")

    def show_cli_order_intro(self, order_str: str) -> None:
        body = (
            f"{self.LINE}\n"
            "Orden actual:\n"
            f"{order_str}\n"
            "¿Desea modificar el orden manualmente? (S/N)"
        )
        self._display_screen(Screen("[2] Definir orden de jugadores", body))

    def show_cli_manual_order_player(self,players_list: str, players_order: str, num_rounds: int) -> None:
        body = (
            f"Número de Rondas: {num_rounds}\n"
            f"Estos son los jugadores: {players_list}\n"
            f"El orden actual es: {players_order}\n" 
            f"{self.LINE}\n"           
            "Ingrese el nuevo orden de jugadores separados por coma\n"
            "(ejemplo: 3,1,4,2)\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body))

    def show_cli_player_order_saved(self,players_order: str) -> None:
        body = (
            "Orden de jugadores actualizado correctamente.\n"
            "El nuevo orden es:\n"
            f"{players_order}\n"
            f"{self.LINE}\n"             
            "[ENTER] continuar\n"
            f"{self.LINE}" 
        )
        self._display_screen(Screen("", body))

    def show_main_menu(self, date_str: str) -> None:
        body = (
            "================================================================================\n"
            "                                  SIM-DJ v1.0\n"
            "           Simulador de Toma de Decisiones Basado en Teoría de Juegos\n"
            "================================================================================\n"
            f"Fecha actual: {date_str}\n"
            "================================================================================\n"
            "Seleccione una opción:\n"
            "[1] Crear Juego\n"
            "[2] Configuración de Juego\n"
            "[3] Simulación del Juego\n"
            "[4] Salir del Sistema\n"
            "================================================================================\n"
        )
        self._display_screen(Screen("Menú Principal", body))

    def show_configuration_menu(self)-> None:
        body = (
            "============================================\n"
            "        Submenú de Configuración\n"
            "============================================\n"
            "[1] Editar parámetros del Juego\n"
            "[2] Definir orden de jugadores\n"
            "[3] Visualizar Juego en forma de Árbol\n"
            "[4] Eliminar Juego\n"
            "[5] Volver al Menú Principal\n"
            "============================================\n"
        )
        self._display_screen(Screen("[2] Configuración de Juego", body))

    def show_simulation_menu(self) -> None:
        body = (
            "============================================\n"
            "        Submenú de Simulación\n"
            "============================================\n"
            "[1] Asignar Probabilidad a las Estrategias\n"
            "[2] Generar y Visualizar Historias \n"
            "[3] Calcular Utilidades y Equilibrios\n"
            "[4] Exportar Resultados de Simulación\n"
            "[5] Volver al Menú Principal\n"
            "============================================\n"
        )
        self._display_screen(Screen("[3] Simulación del Juego", body, prompt=""))

    def show_export_menu(self) -> None:
        body = (
            "=======================================================\n"
            "                Submenú de Exportación\n"
            "=======================================================\n"
            "Seleccione el tipo de exportación que desea realizar:\n"
            "[1] Exportar Matriz de Probabilidades, Historias y Utilidades (Excel)\n"
            "[2] Exportar Árbol de decisiones (SVG)\n"
            "[3] Exportar Ambos\n"
            "[4] Volver al Submenú de Simulación\n"
            "=======================================================\n"
        )
        self._display_screen(Screen("[5] Exportar Resultados de Simulación", body, prompt=""))

    def show_cli_input_players(self) -> None:
        body = (
            "Ingrese el número de JUGADORES:\n"
        )
        self._display_screen(Screen("", body))

    def show_cli_input_rounds(self) -> None:
        body = (
            "Número de JUGADORES registrado correctamente.\n"
            f"{self.LINE}\n"
            "Ingrese el número de RONDAS:\n"
        )
        self._display_screen(Screen("", body))

    def show_cli_input_strategies(self) -> None:
        body = (
            "Número de RONDAS registrado correctamente.\n"
            f"{self.LINE}\n"
            "Ingrese el número de ESTRATEGIAS por JUGADOR:\n"
        )
        self._display_screen(Screen("", body))

    def show_cli_summary_game_creation(self, num_players: int, num_rounds: int, num_strategies: int, scen: int, strat: int, context: str) -> None:
        body = (
            "Resumen del JUEGO:\n"
            f"Jugadores: {num_players}\n"
            f"Rondas: {num_rounds}\n"
            f"Estrategias por jugador: {num_strategies}\n"
            f"Complejidad estimada:\n"
            f"  Escenarios generados: {scen}\n"
            f"  Acciones totales: {strat}\n"
            f"{self.LINE}\n"
            f"¿Desea continuar con la {context} del JUEGO? (S/N)"
        )
        self._display_screen(Screen("", body))

    def show_cli_auto_order_player_preview(self, order_str: str) -> None:
        body = (
            f"Orden automático asignado (cíclico):\n"
            f"{order_str}\n"
            "¿Desea definir el orden manualmente? (S/N)"
        )
        self._display_screen(Screen("", body))

    def show_cli_payments_prompt(self, idx: int) -> None:
        body = (
            "Ingrese los PAGOS para cada JUGADOR en cada HISTORIA.\n"
            "(Escriba “C” en cualquier momento para detener)\n"
            f"{self.LINE}\n"
            f"Historia {idx}:"
        )
        self._display_screen(Screen("", body))

    def show_cli_summary_game_created(self, num_players: int, num_rounds: int, num_strategies: int, order_str: str, total_histories: int, payments_preview: str) -> None:
        body = (
            "Resumen del JUEGO:\n"
            f"Jugadores: {num_players}\n"
            f"Rondas: {num_rounds}\n"
            f"Estrategias: {num_strategies}\n"
            f"Orden de Jugadores: {order_str}\n"
            f"Historias generadas: {total_histories}\n"
            "Pagos por Historia:\n\n"
            f"{payments_preview}\n"
            f"{self.LINE}\n"
            "El JUEGO ha sido creado exitosamente.\n"
            "[ENTER] continuar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body))

    def show_cli_edit_params_intro(self, p, r, s) -> None:
        body = (
            "Configuración actual del JUEGO:\n"
            f"Jugadores: {p}\n"
            f"Rondas: {r}\n"
            f"Estrategias por jugador: {s}\n"
            f"{self.LINE}\n"
            "¿Desea modificar algún parámetro del JUEGO? (S/N)"
        )
        self._display_screen(Screen("[1] Editar parámetros del Juego", body))

    def show_cli_summary_game_edition(self, p, r, s, sc, st) -> None:
        body = (
            "Resumen de configuración modificada:\n"
            f"Jugadores: {p}\n"
            f"Rondas: {r}\n"
            f"Estrategias por jugador: {s}\n"
            f"Complejidad estimada: {sc} combinaciones posibles\n"
            f"{self.LINE}\n"
            "¿Desea guardar los cambios en la configuración del JUEGO? (S/N)"
        )
        self._display_screen(Screen("", body))

    def show_cli_delete_question(self) -> None:
        body = (
            "[4] Eliminar Juego\n"
            f"{self.LINE}\n"
            "¿Está seguro de que desea eliminar el JUEGO actual?\n"
            "Esta acción no se puede deshacer. (S/N)"
        )
        self._display_screen(Screen("", body))

    def show_cli_tree_generated_path(self, filepath: str) -> None:
        body = (
            "El ÁRBOL DE DECISIONES en formato SVG se generó correctamente.\n"
            "Ruta del archivo:\n\n"
            f"{filepath}\n\n"
            f"{self.LINE}\n"
            "[ENTER] continuar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body))

    def show_cli_probability_assignment_intro(self) -> None:
        body = (
            "Tendrá que asignar probabilidades a cada\n"
            "una de las acciones de las estrategias identificadas\n"
            "Ingrese las PROBABILIDADES (entre 0 y 1) \n"
            "para cada ESTRATEGIA del JUEGO activo.\n"
            f"{self.LINE}\n"
            "[ENTER] comenzar / [C] cancelar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("[1] Asignar Probabilidad a las Estrategias", body, prompt=""))

    def show_cli_scenario_to_assign_probabilities(self, scenario_idx: int, actions: Sequence[str]) -> None:
        actions_str = ", ".join(actions)
        body = (
            f"ESCENARIO {scenario_idx}\n"
            "Acciones disponibles:\n"
            f"{actions_str}\n"
            f"{self.LINE}\n"
            "Ingrese las PROBABILIDADES separadas por coma:\n"
            "Ejemplo -> 0.3,0.5,0.2\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body, prompt=""))

    def show_cli_normalization_done(self,scenario_idx: int, actions: Sequence[str], probs: Sequence[float]) -> None:
        pairs = "\n".join([f"{a} -> {p:.2f} |" for a, p in zip(actions, probs)])
        body = (
            "Normalización completada correctamente.\n"
            f"ESCENARIO {scenario_idx}\n"
            f"{self.LINE}\n"      
            "Probabilidades ajustadas:\n"
            f"{pairs}\n"
            "[ENTER] continuar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body, prompt=""))

    def show_cli_probabilities_registered(self, scenario_idx: int, actions: Sequence[str], probs: Sequence[float]) -> None:
        pairs = "\n".join([f"{a} -> {p:.2f} |" for a, p in zip(actions, probs)])        
        body = (
            f"ESCENARIO {scenario_idx}\n"
            f"{self.LINE}\n"            
            "Probabilidaes asignadas a las Acciones:\n"
            f"{pairs}\n"
            f"{self.LINE}\n"
            "Presione [ENTER] para continuar con el siguiente ESCENARIO.\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("Escenario registrado", body, prompt=""))

    def show_cli_history_generation_intro(self) -> None:
        body = (
            "Se generarán todas las HISTORIA(s) posibles\n"
            "del JUEGO activo.\n"
            f"{self.LINE}\n"
            "[ENTER] comenzar / [C] cancelar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("[2] Generar y Visualizar Historias", body, prompt=""))

    def show_cli_history_processing(self) -> None:
        body = (
            "Generando combinaciones de ACCIÓN(es)...\n"
            "Por favor espere mientras se calculan las HISTORIA(s).\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body, prompt=""))

    def show_cli_history_results(self, total: int, histories_samples: list) -> None:
        body = (
            "HISTORIAS generadas correctamente.\n"
            f"{self.LINE}\n"
            f"Total HISTORIAS: {total}\n"
            "Lista:\n\n"        
            f"{histories_samples}\n"    
            f"{self.LINE}\n"
            "[ENTER] continuar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body, prompt=""))

    def show_cli_history_summary(self, total: int) -> None:
        print("----------------------------------------")
        print("Resumen:")
        print(f"- HISTORIA(s) generadas: {total}")
        print("- Datos almacenados correctamente")
        print("----------------------------------------")
        body = (
            "Resumen de HISTORIAS.\n"
            f"{self.LINE}\n"
            f"Total de HISTORIAS generadas: {total}\n"
            "Datos almacenados correctamente.\n"
            f"{self.LINE}\n"
            "[ENTER] continuar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body, prompt=""))

    def show_cli_utility_intro(self) -> None:
        body = (
            "Se calcularán las UTILIDAD(es) esperadas\n"
            "para cada JUGADOR.\n"
            f"{self.LINE}\n"
            "[ENTER] comenzar / [C] cancelar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("[3] Calcular Utilidades y Equilibrios", body, prompt=""))

    def show_cli_utility_processing(self) -> None:
        body = (
            "Calculando UTILIDAD(es) esperadas...\n"
            "Por favor espere, procesando HISTORIA(s) y PAGO(s).\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body, prompt=""))

    def show_cli_utility_summary(self, utility_lines: list):
        utilities_text = "\n".join(utility_lines)
        body = (
            "Resumen de UTILIDAD(es) esperadas por HISTORIA:\n"
            f"{self.LINE}\n"
            f"{utilities_text}\n"
            f"{self.LINE}\n"
            "[ENTER] Continuar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("", body, prompt=""))
    
    def show_cli_equilibria_with_navigation(self, equilibrium_lines: List[str], 
                                        current: int, total: int) -> None:
        display_lines = equilibrium_lines.copy()
        
        if total == 1:
            nav_line = "[ENTER] Continuar"
        else:
            if current == 1:
                nav_line = "[d] = Siguiente SPE"
            elif current == total:
                nav_line = "[a] = Anterior SPE  | [ENTER] Continuar"
            else:
                nav_line = "[a] = Anterior SPE  | [d] = Siguiente SPE"
        
        display_lines.append("")
        display_lines.append(nav_line)
        
        body = "\n".join(display_lines)
        
        self._display_screen(Screen("Análisis de Equilibrios", body, prompt=""))

    def show_cli_equilibria_single(self, equilibrium_lines: List[str]) -> None:
        body = "\n".join(equilibrium_lines)
        self._display_screen(Screen("Análisis de Equilibrios", body, prompt=""))

    def show_cli_export_preview_simple(self, path: str) -> None:
        body = (
            "Exportación completada correctamente.\n"
            "----------------------------------------\n"
            f"Archivo exportado en:\n{path}\n"
            "----------------------------------------\n"
            "[ENTER] continuar"
        )
        self._display_screen(Screen("Exportación exitosa", body, prompt=""))

    def show_cli_combined_export_success(self, excel_file: str, tree_file: str) -> None:
        body = (
            "Exportación combinada completada exitosamente.\n"
            f"{self.LINE}\n"
            "Archivos generados:\n"
            f"1. Excel con resultados: {excel_file}\n\n"
            f"2. Diagrama del árbol: {tree_file}\n\n"
            f"{self.LINE}\n"
            "Los archivos se encuentran en la carpeta de exportaciones.\n"
            f"{self.LINE}\n"
            "[ENTER] continuar\n"
            f"{self.LINE}"
        )
        self._display_screen(Screen("Exportación Combinada Exitosa", body, prompt=""))


__all__ = ["CLIFormatter", "Screen"]
