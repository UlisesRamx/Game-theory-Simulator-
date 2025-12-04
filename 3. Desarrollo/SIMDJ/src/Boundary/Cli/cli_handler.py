from __future__ import annotations
from typing import Any, List, Optional, Dict
from datetime import datetime

from .cli_formatter import CLIFormatter
from .command_parser import CommandParser

from Control.App.command_dispatcher import CommandDispatcher
from Infrastructure.Common.logger import Logger

from Domain.Common.exceptions import (
    GameException, NoActiveGameError, InvalidInputError,
    TechnicalValidationError, ExportError
)

from Infrastructure.Common.logger import Logger
from Infrastructure.Common.technical_validator import TechnicalValidator
from Domain.Common.domain_validator import DomainValidator


class CLIHandler:

    def __init__(
        self,
        formatter: CLIFormatter,
        parser: CommandParser,
        dispatcher: CommandDispatcher,
        technical_validator: TechnicalValidator,
        domain_validator: DomainValidator,
        logger: Logger
    ):
        self.formatter = formatter
        self.parser = parser
        self.dispatcher = dispatcher
        self.technical_validator = technical_validator
        self.domain_validator = domain_validator
        self.logger = logger
        


    # ===========================================================
    # MÉTODO PRINCIPAL - EJECUCIÓN DEL SISTEMA
    # ===========================================================
    def run(self) -> None:
        self.logger.log_info("Sistema SIM-DJ iniciado")
        
        while True:
            try:
                date_str = datetime.now().strftime("%d/%m/%Y")
                self.formatter.show_main_menu(date_str)
                raw_input = self.parser.read_input("> ")
                option = self.parser.parse_menu_option(raw_input)

                if option == 1:
                    self._handle_create_game("creación")
                elif option == 2:
                    self._handle_configure_game()
                elif option == 3:
                    self._handle_simulation_menu()
                elif option == 4:
                    self._handle_exit()
                    break
                else:
                    self._show_message(
                        "Notification", 
                        "Opción incorrecta", 
                        "Seleccione una opción válida del menú."
                    )
                    
            except KeyboardInterrupt:
                self._handle_keyboard_interrupt()
                break
            except Exception as error:
                self._handle_unexpected_error(error)


    # ===========================================================
    # MANEJO DE MENÚ DE SIMULACIÓN
    # ===========================================================
    def _handle_simulation_menu(self) -> None:
        try:
            game_summary = self.dispatcher.execute("get_game_summary")
            if not game_summary["has_active_game"]:
                raise NoActiveGameError()

            while True:
                try:
                    self.formatter.show_simulation_menu()
                    raw_input = self.parser.read_input("> ")
                    option = self.parser.parse_menu_option(raw_input)

                    if option == 1:
                        self._handle_assign_probabilities()
                    elif option == 2:
                        self._handle_generate_histories()
                    elif option == 3:
                        self._handle_calculate_utilities()
                    elif option == 4:
                        self._handle_export_results()
                    elif option == 5:
                        return  # Menú principal
                    else:
                        self._show_message(
                            "Notification",
                            "Opción incorrecta",
                            "Seleccione una opción válida del submenú de configuración."
                        )
                        
                except KeyboardInterrupt:
                    self._handle_operation_cancelled()
                    return
                except Exception as error:
                    self._handle_unexpected_error(error)

        except NoActiveGameError as error:
            self._show_message("Notification", "No hay Juego Activo", error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)


    # ===========================================================
    # CU-01 — CREAR JUEGO
    # ===========================================================
    def _handle_create_game(self, context: str) -> None:
        try:
            edition_mode = (context == "edición")
            parameters = self._get_game_parameters(context, edition_mode)
            
            if parameters is None:
                return
            
            num_players, num_rounds, num_strategies = parameters
            
            ok = self.dispatcher.execute("create_game", num_players, num_rounds, num_strategies)
            
            if ok:
                self._handle_post_creation(context)
                
        except GameException as error:
            self._show_message("Error", error.technical_message, error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _get_game_parameters(self, context: str, edition_mode: bool) -> Optional[tuple]:
        while True:
            parameters = self._read_game_parameters(context)
            if parameters is None:
                return None

            num_players, num_rounds, num_strategies = parameters
                        
            if not self._confirm_parameters(context, num_players, num_rounds, num_strategies):
                return  None
            else:
                edition_mode = False


            if not edition_mode and self._ask_yes_no_question(
            "¿Desea editar los parámetros del JUEGO antes de continuar? (S/N)"):
                edition_mode = True
                continue

            return num_players, num_rounds, num_strategies

    def _read_game_parameters(self, context: str) -> Optional[tuple]:
        parameters = {}
        param_configs = [
            ('players', self.formatter.show_cli_input_players),
            ('rounds', self.formatter.show_cli_input_rounds),
            ('strategies', self.formatter.show_cli_input_strategies)
        ]
        
        for param_name, prompt_method in param_configs:
            value = self._read_parameter(prompt_method, context)
            if value is None:
                return None
            parameters[param_name] = value
        
        return parameters['players'], parameters['rounds'], parameters['strategies']

    def _read_parameter(self, prompt_method: callable, context: str) -> Optional[int]:
        while True:
            prompt_method()
            raw_input = self.parser.read_input("> ").strip()
            
            if self.parser.is_cancel(raw_input):
                if self._ask_yes_no_question(f"¿Desea cancelar {context}? (S/N)"):
                    return None
                else:
                    continue
            
            if not raw_input.isdigit() or int(raw_input) <= 0:
                self._show_message(
                    "Notification",
                    "Entrada inválida",
                    "Ingrese solo números enteros positivos."
                )
                continue
            
            return int(raw_input)

    def _confirm_parameters(self, context: str, players: int, rounds: int, strategies: int) -> bool:
        complexity_info = self.domain_validator.validate_game_complexity(rounds, strategies)
        while True:
            self.formatter.show_cli_summary_game_creation(
                players, rounds, strategies,
                complexity_info["scenarios"], 
                complexity_info["strategies"], 
                context
            )

            answer = self.parser.read_input("\n> ").strip().lower()
        
            if answer in ("n", "no"):
                self._show_message(
                    "Notification",
                    "Operación Cancelada", 
                    f"Se ha cancelado la {context} del Juego."
                )
                return False
            elif answer in ("s", "si"):
                return True
            else:
                self._show_message(
                    "Notification",
                    "Respuesta incorrecta",
                    "Solo responda 'S' o 'N'."
                )

    def _handle_post_creation(self, context: str) -> None:
        game_summary = self.dispatcher.execute("get_game_summary")   
        self._handle_configure_order(context)
        result = self._capture_payoffs(game_summary["total_histories"])
        self._show_final_summary(game_summary, result)

    def _capture_payoffs(self, total_histories: int) -> None:
        try:
            game_summary = self.dispatcher.execute("get_game_summary")
            num_players = game_summary["config"]["players"]
            pay_matrix = []

            for history_index in range(1, total_histories + 1):
                values = []
                for player_index in range(1, num_players + 1):
                    value = self._read_payoff_value(player_index, history_index)
                    if value is None:
                        return
                    values.append(value)

                pay_matrix.append(values)

            result = self.dispatcher.execute("register_payoffs", pay_matrix)

            if result["success"]:
                return result
            
        except GameException as error:
            self._show_message("Error", error.technical_message, error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _read_payoff_value(self, player_index: int, history_index: int) -> Optional[float]:
        while True:
            try:
                self.formatter.show_cli_payments_prompt(history_index)
                raw_input = self.parser.read_input(f"    Jugador {player_index}: ").strip()

                if self.parser.is_cancel(raw_input):
                    self._show_message(
                        "Notification",
                        "Operación Cancelada", 
                        "Se canceló la captura de PAGOS."
                    )
                    return None

                return float(raw_input)
            
            except ValueError:
                self._show_message(
                    "Notification",
                    "Entrada inválida", 
                    "Ingrese solo valores numéricos."
                )
            continue

    def _show_final_summary(self, game_summary: Dict[str, Any], result: Dict[str, Any]) -> None:
        config = game_summary["config"]
        players, rounds, strategies = config["players"], config["rounds"], config["strategies"]
        
        order_preview = self.dispatcher.execute("get_player_order_preview", players, rounds)
        order_str = " -> ".join(order_preview)

        self.formatter.show_cli_summary_game_created(
            players, rounds, strategies, 
            order_str, game_summary["total_histories"], result["preview"]
        )
        self.parser.read_input("\n> ")


    # ===========================================================
    # CU-02 — CONFIGURAR JUEGO
    # ===========================================================
    def _handle_configure_game(self) -> None:
        try:
            game_summary = self.dispatcher.execute("get_game_summary")
            if not game_summary["has_active_game"]:
                raise NoActiveGameError()

            while True:
                try:
                    self.formatter.show_configuration_menu()
                    raw_input = self.parser.read_input("> ")
                    option = self.parser.parse_menu_option(raw_input)

                    if option == 1:
                        self._handle_create_game("edición")
                    elif option == 2:
                        self._handle_configure_order()
                    elif option == 3:
                        self._handle_show_tree()
                    elif option == 4:
                        self._handle_delete_game()
                    elif option == 5:
                        return  # Menú principal
                    else:
                        self._show_message(
                            "Notification",
                            "Opción incorrecta",
                            "Seleccione una opción válida del submenú de configuración."
                        )
                        
                except KeyboardInterrupt:
                    self._handle_operation_cancelled()
                    return
                except Exception as error:
                    self._handle_unexpected_error(error)

        except NoActiveGameError as error:
            self._show_message("Notification", "No hay Juego Activo", error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _handle_configure_order(self, context: str=None) -> None:
        try:
            game_summary = self.dispatcher.execute("get_game_summary")
            if not self._ask_to_configure_order(game_summary["player_order"], context):
                return
            
            players_data = self.dispatcher.execute("get_players_for_order")
            
            new_order = self._capture_new_order_from_user(game_summary, players_data)
            if new_order is None:
                return

            ok = self.dispatcher.execute("configure_order", new_order)
            if ok:
                game_summary = self.dispatcher.execute("get_game_summary")
                new_order_display = [f"J{player_id}" for player_id in game_summary["player_order"]]
                new_order_str = " -> ".join(new_order_display)
                
                self.formatter.show_cli_player_order_saved(new_order_str)
                self.parser.read_input("\n> ")

        except GameException as error:
            self._show_message("Error", error.technical_message, error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _capture_new_order_from_user(
        self, 
        game_summary: Dict[str, Any], 
        players_data: Dict[str, Any]
    ) -> Optional[List[int]]:
        current_order = [f"J{player_id}" for player_id in game_summary["player_order"]]
        order_str = " -> ".join(current_order)
        players_list = players_data["players_list"]
        num_rounds = game_summary["config"]["rounds"]

        while True:
            self.formatter.show_cli_manual_order_player(players_list, order_str, num_rounds)
            raw_input = self.parser.read_input("\n> ").strip()

            if self.parser.is_cancel(raw_input):
                self._show_message(
                    "Notification",
                    "Operación Cancelada",
                    "Se canceló la configuración del orden."
                )
                return None

            try:
                self.technical_validator.validate_string_not_empty(raw_input, "entrada de IDs")

                player_ids_str = [pid.strip() for pid in raw_input.split(",")]
                player_ids = []

                for pid_str in player_ids_str:
                    if not pid_str.isdigit():
                        raise TechnicalValidationError(
                            technical_message=f"ID '{pid_str}' no es numérico",
                            user_message="Todos los IDs deben ser números enteros."
                        )
                    pid = int(pid_str)
                    self.technical_validator.validate_positive_integer(pid, "ID de jugador")
                    player_ids.append(pid)

                if len(player_ids) != len(current_order):
                    raise TechnicalValidationError(
                        technical_message=f"Se ingresaron {len(player_ids)} IDs, se esperaban {len(current_order)}",
                        user_message=f"Debe ingresar exactamente {len(current_order)} IDs separados por coma."
                    )

                return player_ids

            except (TechnicalValidationError, InvalidInputError) as error:
                self._show_message("Error", type(error).__name__, error.user_message)
                continue

    def _handle_delete_game(self) -> None:
        try:
            confirm_delete = self._ask_yes_no_question(
                "¿Está seguro de que desea eliminar el juego actual? (S/N)"
            )
            
            if not confirm_delete:
                self._show_message(
                    "Notification",
                    "Operación Cancelada",
                    "Se ha cancelado la Eliminación del Juego."
                )
                return

            ok = self.dispatcher.execute("delete_game")

            if ok:
                self._show_message(
                    "Notification",
                    "Eliminación Completa",
                    "El JUEGO ha sido eliminado correctamente."
                )

        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)


    # ===========================================================
    # CU-03 — VISUALIZAR ÁRBOL
    # ===========================================================
    def _handle_show_tree(self,context: str=None) -> None:
        try:
            if not self._ask_to_show_tree(context):
                return

            self._show_message(
                "Notification",
                "Preparando datos del ÁRBOL DE DECISIONES...",
                "Por favor espere mientras se procesan los escenarios y estrategias."
            )

            file_path = self.dispatcher.execute("show_tree")
            if file_path:
                self.formatter.show_cli_tree_generated_path(file_path)
                self.parser.read_input("\n> ")

        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)


    # ===========================================================
    # CU-04 — Asignar probabilidades
    # ===========================================================    
    def _handle_assign_probabilities(self) -> None:
        try:
            scenarios_data = self._get_scenarios_for_assignment()
            if not scenarios_data:
                return
            
            if not self._confirm_probability_assignment_start():
                return
            
            if not self._process_all_scenarios(scenarios_data["scenarios"]):
                return
            
            self._finalize_probability_assignment()
            
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _get_scenarios_for_assignment(self) -> Optional[Dict[str, Any]]:
        scenarios_data = self.dispatcher.execute("get_scenarios_for_probability_assignment")
        
        if not scenarios_data["has_scenarios"]:
            self._show_message(
                "Notification",
                "No hay escenarios disponibles",
                "No se puede asignar probabilidades sin escenarios."
            )
            return None
        
        return scenarios_data

    def _confirm_probability_assignment_start(self) -> bool:
        while True:
            self.formatter.show_cli_probability_assignment_intro()
            start_raw = self.parser.read_input("\n> ")

            if self.parser.is_cancel(start_raw):
                self._show_message(
                    "Notification",
                    "Cancelando operación",
                    "Se canceló la asignación de probabilidades."
                )
                return False
            if start_raw in (""):
                return True
            else:
                self._show_message(
                    "Notification",
                    "Respuesta incorrecta",
                    "Solo presione [Enter] o ingrese 'C'."
                )

    def _process_all_scenarios(self, scenarios: List[List[str]]) -> bool:
        for idx, actions in enumerate(scenarios, start=1):
            if not self._process_single_scenario(idx, actions):
                return False
        return True

    def _process_single_scenario(self, scenario_index: int, actions: List[str]) -> bool:
        while True:
            probabilities = self._read_scenario_probabilities(scenario_index, actions)
            if probabilities is None:
                self._show_message(
                    "Notification",
                    "Valores incorrectos",
                    "Ingrese SOLO valores númericos."
                )
                continue 
            else:
                if self._probabilities_in_range(probabilities):
                    if self.technical_validator.is_numeric_in_range(sum(probabilities),1,1):
                        if self._assign_scenario_probabilities(scenario_index, actions, probabilities):
                            self._show_probabilities_registered(scenario_index, actions, probabilities)
                            return True
                        else:
                            continue
                    else:
                        normalize = self._ask_yes_no_question(
                            f"Las PROBABILIDADES del ESCENARIO {scenario_index} no suman 1.\n"
                            "¿Desea normalizarlas automáticamente? (S/N)"
                        )
                        if normalize:
                            return self._assign_normalized_probabilities(scenario_index, actions, probabilities)
                        else:
                            continue
                else:
                    continue

    def _probabilities_in_range(self, probabilities: List[float]) -> bool:
        for probability_value in probabilities:
            if not self.technical_validator.is_numeric_in_range(probability_value,0,1):
                self._show_message(
                "Notification",
                "Valores fuera de rango",
                "Ingrese SOLO valores númericos entre el 1 y el 0."
                )
                return False
        return True
    
    def _read_scenario_probabilities(self, scenario_index: int, actions: List[str]) -> Optional[List[float]]:
        self.formatter.show_cli_scenario_to_assign_probabilities(scenario_index, actions)
        raw_probs = self.parser.read_input("\n> ")
        
        if self.parser.is_cancel(raw_probs):
            self._show_message(
                "Notification",
                "Cancelando operación",
                "Se canceló la asignación de probabilidades."
            )
            return None
        
        return self.parser.parse_probabilities_csv(raw_probs)

    def _assign_normalized_probabilities(self, scenario_index: int, actions: List[str], 
                                        probabilities: List[float]) -> bool:
        try:
            normalized_probs = self.dispatcher.execute(
                "normalize_prob",
                actions,
                probabilities
            )
            
            self.formatter.show_cli_normalization_done(scenario_index, actions, normalized_probs)
            self.parser.read_input("\n> ")

            ok = self._assign_scenario_probabilities(scenario_index, actions, normalized_probs)
            if ok:
                self._show_probabilities_registered(scenario_index, actions, normalized_probs)
                return True

        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
            return False            
        except Exception as error:
            self._handle_unexpected_error(error)

    def _assign_scenario_probabilities(self, scenario_index: int, actions: List[str], 
                                    probabilities: List[float]) -> bool:
        try:
            ok = self.dispatcher.execute(
                "assign_prob",
                scenario_index,
                actions,
                probabilities
            )
            
            if ok:
                return True

        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
            return False            
        except Exception as error:
            self._handle_unexpected_error(error)        

    def _show_probabilities_registered(self, scenario_index: int, actions: List[str], 
                                    probabilities: List[float]) -> None:
        self.formatter.show_cli_probabilities_registered(scenario_index, actions, probabilities)
        self.parser.read_input("\n> ")

    def _finalize_probability_assignment(self) -> None:
        try:
            ok = self.dispatcher.execute("finalize_probability_assignment")
            
            if ok:
                self._show_message(
                    "Notification",
                    "Operación Completada",
                    "Probabilidades asignadas correctamente."
                )
            
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)


    # ===========================================================
    # CU-05 — Generar Historias
    # ===========================================================   
    def _handle_generate_histories(self) -> None:
        try:
            if not self._confirm_history_generation_start():
                return
            
            result = self._process_history_generation()
            if not result:
                return
            
            self._show_history_generation_results()
            
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _confirm_history_generation_start(self) -> bool:
        while True:
            self.formatter.show_cli_history_generation_intro()
            start_raw = self.parser.read_input("\n> ")

            if self.parser.is_cancel(start_raw):
                self._show_message(
                    "Notification",
                    "Cancelando operación",
                    "Se canceló la generación de historias."
                )
                return False
            if start_raw in (""):
                return True
            else:
                self._show_message(
                    "Notification",
                    "Respuesta incorrecta",
                    "Solo presione [Enter] o ingrese 'C'."
                )

    def _process_history_generation(self) -> Optional[Dict[str, Any]]:
        try:
            self.formatter.show_cli_history_processing()
            
            histories_result = self.dispatcher.execute("generate_histories")
            
            if not histories_result:
                self._show_message(
                    "Error",
                    "Error en la generación de Historias",
                    f"{histories_result.get('error', 'Error desconocido')}"
                )
                return None
            
            return histories_result
            
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _show_history_generation_results(self) -> None:
        histories_samples_data = self.dispatcher.execute("get_histories_samples")
        histories_samples = histories_samples_data["samples"]
        total_histories = histories_samples_data["total"]

        self.formatter.show_cli_history_results(total_histories, histories_samples)
        self.parser.read_input("\n> ")

        self.formatter.show_cli_history_summary(total_histories)
        self.parser.read_input("\n> ")


    # ===========================================================
    # CU-06 — Generar Utilidades y equilibrios
    # ===========================================================  
    def _handle_calculate_utilities(self) -> None:
        try:
            if not self._confirm_utilities_calculation_start():
                return
            
            utility_result = self._process_utilities_calculation()
            if not utility_result:
                return
            
            if self._ask_for_equilibria_calculation():
                equilibria_result = self._process_equilibria_calculation()
            else:
                equilibria_result = None
            
            self._show_utilities_results(utility_result, equilibria_result)
            
            self._finalize_utilities_calculation()
            
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _confirm_utilities_calculation_start(self) -> bool:
        while True:
            self.formatter.show_cli_utility_intro()
            start_raw = self.parser.read_input("\n> ")

            if self.parser.is_cancel(start_raw):
                self._show_message(
                    "Notification",
                    "Cancelando operación",
                    "Se canceló el cálculo de utilidades."
                )
                return False
            if start_raw in (""):
                return True
            else:
                self._show_message(
                    "Notification",
                    "Respuesta incorrecta",
                    "Solo presione [Enter] o ingrese 'C'."
                )

    def _process_utilities_calculation(self) -> Optional[Dict[str, Any]]:
        try:
            self.formatter.show_cli_utility_processing()
            
            utility_result = self.dispatcher.execute("calculate_utilities")
            
            if not utility_result:
                self._show_message(
                    "Error",
                    "Error en cálculo de utilidades",
                    f"Verifique que todos los pasos anteriores se completaron correctamente."
                )
                return None
            
            return utility_result
            
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _process_equilibria_calculation(self) -> Optional[Dict[str, Any]]:
        try:
            equilibria_result = self.dispatcher.execute("identify_equilibria")
            
            if not equilibria_result:
                self._show_message(
                    "Error",
                    "Error en búsqueda de equilibrios",
                    "Error durante la generación de los equilibrios"
                )
                return None
            
            return equilibria_result
            
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)



    def _show_utilities_results(self, utility_result: Dict[str, Any], 
                            equilibria_result: Optional[Dict[str, Any]]) -> None:
        utility_lines = utility_result.get("utility_lines", [])
        if utility_lines:
            self.formatter.show_cli_utility_summary(utility_lines)
            self.parser.read_input("\n> ")
        else:
            self._show_message(
                "Error",
                "No hay utilidades para mostrar",
                "No se generaron líneas de utilidad para mostrar."
            )
        
        if equilibria_result:
            eq_pages = equilibria_result.get("equilibria_pages", [])
            total_eq = equilibria_result.get("total_equilibria", 0)
            
            if eq_pages and total_eq > 0:
                current_index = 0
                
                while True:
                    current_page = eq_pages[current_index]
                    
                    if total_eq == 1:
                        self.formatter.show_cli_equilibria_single(current_page)
                        
                        self.parser.read_input("\n> ")
                        break
                    else:
                        self.formatter.show_cli_equilibria_with_navigation(
                            current_page, 
                            current_index + 1, 
                            total_eq
                        )
                        
                        key = self.parser.read_input("\n> ").strip().lower()
                        
                        if key == '':  # Enter
                            return
                        elif key == 'd' and current_index < total_eq - 1:
                            current_index += 1
                        elif key == 'a' and current_index > 0:
                            current_index -= 1
                        else:
                            self._show_message(
                                "Notification",
                                "Opción no válida",
                                "Use 'a' (anterior), 'd' (siguiente) o Enter (salir)."
                            )
                            continue
            else:
                self._show_message(
                    "Notification",
                    "No se encontraron equilibrios",
                    "No se identificaron equilibrios de Nash en este juego."
                )



    def _finalize_utilities_calculation(self) -> None:
        try:
            result = self.dispatcher.execute("finalize_utilities_calculation")
            
            if not result:
                self.logger.log_warning(f"No se pudo finalizar cálculo de utilidades: {result.get('error')}")
                self._show_message(
                    "Notification",
                    "Cálculo Completado",
                    "Las utilidades han sido calculadas correctamente pero se pudieron guardar"
                )
                return
            
            self._show_message(
                "Notification",
                "Cálculo Completado",
                result.get("message", "Las utilidades han sido calculadas correctamente.")
            )
            
        except Exception as error:
            self._show_message(
                "Error",
                "Error interno",
                "La utilidades y equilibrios no se pudieron guardar.\nInténtelo nuevamente."
            )


    # ===========================================================
    # CU-07 — Exportar Resultados
    # ===========================================================  

    def _handle_export_results(self) -> None:
        try:
            game_summary = self.dispatcher.execute("get_game_summary")
            if not game_summary["has_active_game"]:
                raise NoActiveGameError()

            while True:
                try:
                    self.formatter.show_export_menu()
                    raw_input = self.parser.read_input("> ")
                    option = self.parser.parse_menu_option(raw_input)

                    if option == 1:
                        self._handle_export_excel()
                    elif option == 2:
                        self._handle_show_tree("exportación")
                    elif option == 3:
                        self._handle_export_both()
                    elif option == 4:
                        return
                    else:
                        self._show_message(
                            "Notification",
                            "Opción incorrecta",
                            "Seleccione una opción válida del submenú de exportación."
                        )
                        
                except KeyboardInterrupt:
                    self._handle_operation_cancelled()
                    return
                except Exception as error:
                    self._handle_unexpected_error(error)

        except NoActiveGameError as error:
            self._show_message("Notification", "No hay Juego Activo", error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _handle_export_excel(self) -> None:
        try:
            confirm = self._ask_yes_no_question("¿Desea exportar todos los resultados del juego a un archivo Excel? (S/N)")
            if not confirm:
                self._show_message(
                    "Notification",
                    "Exportación Cancelada",
                    "Se canceló la operación de exportación."
                )
                return

            self._show_message(
                "Notification",
                "Exportando resultados...",
                "Por favor espere mientras se generan los archivos."
            )

            result = self.dispatcher.execute("export_complete_results")
            
            if result.get("success"):
                self.formatter.show_cli_export_preview_simple(result.get("file_path", ""))
                self.parser.read_input("\n> ")
            else:
                error_msg = result.get("error", "Error desconocido")
                self._show_message(
                    "Error",
                    "Error en exportación",
                    f"No se pudieron exportar los resultados: {error_msg}"
                )
                
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)

    def _handle_export_both(self) -> None:
        try:
            confirm = self._ask_yes_no_question(
                "¿Desea exportar TODOS los resultados (Excel + Árbol SVG)?"
            )
            
            if not confirm:
                self._show_message(
                    "Notification",
                    "Exportación Cancelada",
                    "Se canceló la operación de exportación."
                )
                return

            self._show_message(
                "Notification",
                "Exportando resultados combinados...",
                "Generando archivo Excel y diagrama del árbol."
            )

            excel_result = self.dispatcher.execute("export_complete_results")
            
            if not excel_result.get("success"):
                raise ExportError("No se pudo exportar el archivo Excel")

            tree_path = None
            try:
                tree_path = self.dispatcher.execute("show_tree")
            except Exception as tree_error:
                self.logger.log_warning(f"No se pudo exportar el árbol: {tree_error}")

            excel_file = excel_result.get("file_path", "")
            excel_name = excel_file.split("/")[-1] if "/" in excel_file else excel_file
            
            if tree_path:
                tree_name = tree_path.split("/")[-1] if "/" in tree_path else tree_path
                self.formatter.show_cli_combined_export_success(excel_name, tree_name)
            else:
                self.formatter.show_cli_export_preview_simple(excel_file)
            
            self.parser.read_input("\n> ")
            
        except GameException as error:
            self._show_message("Error", error.technical_message,error.user_message)
        except Exception as error:
            self._handle_unexpected_error(error)


    # ===========================================================
    # MÉTODOS AUXILIARES
    # ===========================================================
    def _ask_to_show_tree(self,context: str = None) -> bool:
        show_tree = self._ask_yes_no_question(
            "¿Desea generar el SVG del ÁRBOL DE DECISIONES? (S/N)"
        )
        if show_tree:
            return True
        else:
            if context not in ("creación","edición", "exportación"):
                self._show_message(
                    "Notification",
                    "Cancelando operación",
                    "Se canceló la generación del SVG del ÁRBOL DE DECISIONES."
                )
            return False

    def _ask_to_configure_order(self, player_order: List[int], context: str = None) -> bool:
        current_order = [f"J{player_id}" for player_id in player_order]
        order_str = " -> ".join(current_order)
        
        configure_order = self._ask_yes_no_question(
            f"Orden automático asignado (cíclico):\n{order_str}\n"
            "¿Desea definir el orden manualmente? (S/N)"
        )
        if configure_order:
            return True
        else:
            if context not in ("creación","edición"):
                self._show_message(
                    "Notification",
                    "Cancelando operación", 
                    "Se canceló la configuración del orden de los jugadores."
                )
            return False

    def _ask_for_equilibria_calculation(self) -> bool:
        ans_eq = self._ask_yes_no_question(
            "Cálculo de UTILIDAD(es) completado exitosamente.\n¿Desea identificar los EQUILIBRIO(s) del JUEGO? (S/N)"
        )
        if ans_eq:
            return True
        else:
            return False

    def _ask_yes_no_question(self, question: str) -> bool:
        while True:
            self.formatter.display_message("Question", "", question)
            answer = self.parser.read_input("\n> ").strip().lower()
            if answer in ("n", "no"):
                return False
            elif answer in ("s", "si"):
                return True
            else:
                self._show_message(
                    "Notification",
                    "Respuesta incorrecta",
                    "Solo responda 'S' o 'N'."
                )
    
    def _show_message(self, message_type: str, title: str, message: str) -> None:
        self.formatter.display_message(message_type, title, message)
        self.parser.read_input("\n> ")

    def _handle_operation_cancelled(self) -> None:
        self._show_message(
            "Notification",
            "Operación Cancelada",
            "La operación fue cancelada por el usuario."
        )
    
    def _handle_keyboard_interrupt(self) -> None:
        self.logger.log_info("Sistema cerrado por el usuario")
        self._show_message(
            "Notification",
            "Sistema Cerrado",
            "El sistema SIM-DJ ha sido cerrado."
        )

    def _handle_unexpected_error(self, error: Exception) -> None:
        self._show_message(
            "Error",
            "Error inesperado",
            error
        )

    def _handle_exit(self) -> None:
        self.logger.log_info("Sistema SIM-DJ finalizado normalmente")
        self._show_message(
            "Notification",
            "Sistema Cerrado",
            "El sistema SIM-DJ ha sido cerrado correctamente."
        )



__all__ = ["CLIHandler"]