from __future__ import annotations
from pathlib import Path
from typing import List, Dict
import pandas as pd

from Infrastructure.Common.logger import Logger
from Infrastructure.Common.technical_validator import TechnicalValidator
from Infrastructure.Export.naming_service import NamingService
from Domain.Core.game import Game
from Control.App.session_manager import SessionManager
from Domain.Core.scenario import Scenario
from Domain.Core.strategy import Strategy



class ExcelExporter:

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

    def _get_base_export_directory(self) -> Path:
        current_file = Path(__file__).resolve()
        base_dir = current_file.parent.parent.parent.parent / "Tests" / "Exports" / "Excel"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def resolve_file_conflict(self, full_path: str) -> str:
        if not full_path:
            raise ValueError("Ruta vacía para resolver conflicto")

        return self.naming_service.resolve_file_conflict(full_path)

    def ensure_export_directory(self) -> None:
        try:
            self.base_export_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.log_error(f"Error creando directorio de exportación: {e}")
            raise

    def export_complete_game(self, game: Game, session: SessionManager) -> str:
        try:
            base_name = self.naming_service.generate_file_name(
                len(game.players), len(game.rounds), game.num_strategies, "Game"
            )
            filename = f"{base_name}_completo.xlsx"
            file_path = self.base_export_dir / filename
            file_path = Path(self.resolve_file_conflict(str(file_path)))

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                self._export_game_configuration(game, writer)
                self._export_probabilities(game, writer)
                self._export_histories(game, session, writer)
                self._export_utilities(game, session, writer)
                self._export_equilibria(game, session, writer)
                self._export_summary(game, session, writer)

            self.logger.log_info(f"Excel exportado: {file_path}")
            return str(file_path)

        except Exception as e:
            self.logger.log_error(f"Error exportando a Excel: {e}")
            raise

    def _export_game_configuration(self, game: Game, writer: pd.ExcelWriter) -> None:
        escenarios_normales = self._count_normal_scenarios(game.scenarios)
        
        config_data = {
            'Parámetro': [
                'Jugadores',
                'Rondas',
                'Estrategias por Jugador',
                'Escenarios Totales',
                'Acciones Totales',
                'Estrategias Totales',
                'Historias Totales',
                'Fecha de Creación'
            ],
            'Valor': [
                len(game.players),
                len(game.rounds),
                game.num_strategies,
                escenarios_normales,
                len(game.actions),
                len(game.actions), 
                len(game.histories),
                game.created_at
            ]
        }
        
        df = pd.DataFrame(config_data)
        df.to_excel(writer, sheet_name='Configuración', index=False)
        
        worksheet = writer.sheets['Configuración']
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 20

    def _export_probabilities(self, game: Game, writer: pd.ExcelWriter) -> None:
        data = []
        estrategia_counter = 1
        
        for scenario in game.scenarios:
            if scenario.scenario_type == "normal" and scenario.outgoing_actions:
                for action in scenario.outgoing_actions:
                    data.append([
                        estrategia_counter,
                        scenario.scenario_id,
                        scenario.label if hasattr(scenario, 'label') else f"Escenario {scenario.scenario_id}",
                        action.action_id,
                        action.label if hasattr(action, 'label') else f"Acción {action.action_id}",
                        getattr(action, 'probability', 0.0)
                    ])
                    estrategia_counter += 1
        
        if data:
            df = pd.DataFrame(data, columns=[
                'Estrategia de Juego', 
                'ID Escenario', 
                'Escenario', 
                'ID Acción', 
                'Acción', 
                'Probabilidad'
            ])
            df.to_excel(writer, sheet_name='Probabilidades', index=False)
            
            worksheet = writer.sheets['Probabilidades']
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                worksheet.column_dimensions[col].width = 18

    def _export_histories(self, game: Game, session: SessionManager, writer: pd.ExcelWriter) -> None:
        data = []
        histories = session.history_list or game.histories
        
        for history in histories:
            action_labels = []
            action_probabilities = []
            
            for action in history.actions:
                action_labels.append(action.label if hasattr(action, 'label') else f"A{action.action_id}")
                action_probabilities.append(getattr(action, 'probability', 0.0))
            
            action_sequence = " → ".join(action_labels)
            
            prob_strs = [f"({prob:.2f})" for prob in action_probabilities]
            valor_secuencia = "*".join(prob_strs)
            
            data.append([
                history.history_id,
                action_sequence,
                valor_secuencia,
                history.total_probability,
                len(history.actions)
            ])
        
        if data:
            df = pd.DataFrame(data, columns=[
                'ID Historia', 
                'Secuencia de Acciones', 
                'Valor secuencia',
                'Probabilidad Total',
                'Número de Acciones'
            ])
            df.to_excel(writer, sheet_name='Historias', index=False)
            
            worksheet = writer.sheets['Historias']
            worksheet.column_dimensions['A'].width = 12
            worksheet.column_dimensions['B'].width = 30 
            worksheet.column_dimensions['C'].width = 25
            worksheet.column_dimensions['D'].width = 20
            worksheet.column_dimensions['E'].width = 18

    def _export_utilities(self, game: Game, session: SessionManager, writer: pd.ExcelWriter) -> None:
        data = []
        payoffs = session.payoffs or game.payoffs
        
        for payoff in payoffs:
            history_id = payoff.history.history_id if payoff.history else 'N/A'
            player_id = payoff.player.player_id if payoff.player else 'N/A'
            
            history_prob = 0.0
            if payoff.history and hasattr(payoff.history, 'total_probability'):
                history_prob = payoff.history.total_probability
            
            data.append([
                payoff.payoff_id,
                history_id,
                history_prob,
                player_id,
                f"Jugador {player_id}",
                payoff.value,
                payoff.expected_utility,
                getattr(payoff, 'description', f'Pago {payoff.payoff_id}')
            ])
        
        if data:
            df = pd.DataFrame(data, columns=[
                'ID Payoff',
                'ID Historia',
                'Probabilidad Historia',
                'ID Jugador',
                'Jugador',
                'Valor Payoff',
                'Utilidad Esperada',
                'Descripción'
            ])
            df.to_excel(writer, sheet_name='Utilidades', index=False)
            
            # Ajustar ancho de columnas
            worksheet = writer.sheets['Utilidades']
            worksheet.column_dimensions['A'].width = 12
            worksheet.column_dimensions['B'].width = 12
            worksheet.column_dimensions['C'].width = 20
            worksheet.column_dimensions['D'].width = 12
            worksheet.column_dimensions['E'].width = 15
            worksheet.column_dimensions['F'].width = 15
            worksheet.column_dimensions['G'].width = 20
            worksheet.column_dimensions['H'].width = 20

    def _export_equilibria(self, game: Game, session: SessionManager, writer: pd.ExcelWriter) -> None:
        try:
            equilibria = session.equilibria or []
            
            if not equilibria:
                empty_df = pd.DataFrame([['No se encontraron equilibrios']], 
                                    columns=['Información'])
                empty_df.to_excel(writer, sheet_name='Equilibrios', index=False)
                return
            
            equilibrium_profiles = []
            if hasattr(session, 'equilibrium_profiles') and session.equilibrium_profiles:
                equilibrium_profiles = session.equilibrium_profiles
            else:
                equilibrium_profiles = self._reconstruct_equilibrium_profiles(equilibria, game)
            
            data = []
            
            for i, profile in enumerate(equilibrium_profiles, 1):
                data.append([f"Análisis de Equilibrios completado: {i}/{len(equilibrium_profiles)} SPE"])
                data.append(["-" * 70])
                
                data.append(["Ronda", "Jugador", "Escenario", "Acción", "Destino", "Pago"])
                data.append(["-" * 70])
                
                for step in profile.steps:
                    payoff_str = ", ".join([f"{player}:{value:.1f}" for player, value in step.payoffs.items()])
                    
                    data.append([
                        step.round_num,
                        step.player,
                        step.scenario,
                        step.action,
                        step.destination,
                        payoff_str
                    ])
                
                data.append([])
                
                data.append(["Historia completa:", profile.full_history])
                
                final_payments_str = ", ".join([f"{player}={value:.1f}" for player, value in profile.final_payments.items()])
                data.append(["Pagos finales:", final_payments_str])
                
                data.append(["-" * 70])
                data.append([])
            
            df = pd.DataFrame(data)
            
            df.to_excel(writer, sheet_name='Equilibrios', index=False, header=False)
            
            worksheet = writer.sheets['Equilibrios']
            
            column_widths = {
                'A': 15,  # Ronda
                'B': 12,  # Jugador
                'C': 15,  # Escenario
                'D': 12,  # Acción
                'E': 15,  # Destino
                'F': 30   # Pago
            }
            
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            for row in [1, 3, 4]: 
                for col in range(1, 7):
                    cell = worksheet.cell(row=row, column=col)
                    cell.font = cell.font.copy(bold=True)
            
            self.logger.log_info(f"Exportados {len(equilibrium_profiles)} equilibrios en formato tabular")
            
        except Exception as e:
            self.logger.log_error(f"Error exportando equilibrios: {e}")
            self._export_equilibria_simple(game, session, writer)

    def _reconstruct_equilibrium_profiles(self, equilibria: List[Strategy], game: Game) -> List[Dict]:
        profiles = []
        
        strategies_by_profile = {}
        
        for strategy in equilibria:
            profile_id = getattr(strategy, 'profile_id', 1)
            
            if profile_id not in strategies_by_profile:
                strategies_by_profile[profile_id] = []
            strategies_by_profile[profile_id].append(strategy)
        
        for profile_id, strategies in strategies_by_profile.items():
            strategies_sorted = sorted(strategies, key=lambda s: s.from_scenario.depth)
            
            steps = []
            full_history_parts = []
            final_payments = {}
            
            for strategy in strategies_sorted:
                active_player = self._get_active_player_for_strategy(strategy, game)
                player_label = f"J{active_player.player_id}" if active_player else "J?"
                
                destination = "Terminal"
                if strategy.action.destination_scenario:
                    destination = strategy.action.destination_scenario.label
                
                payoffs = self._get_payoffs_for_strategy(strategy, game)
                
                step = {
                    'round_num': strategy.from_scenario.depth + 1,
                    'player': player_label,
                    'scenario': strategy.from_scenario.label,
                    'action': strategy.action.label,
                    'destination': destination,
                    'payoffs': payoffs
                }
                steps.append(step)
                
                full_history_parts.append(strategy.from_scenario.label)
                full_history_parts.append(strategy.action.label)
                
                if strategy.action.destination_scenario and strategy.action.destination_scenario.is_terminal():
                    final_payments = payoffs
            
            profile = {
                'profile_id': profile_id,
                'strategies': strategies,
                'steps': steps,
                'full_history': " → ".join(full_history_parts),
                'final_payments': final_payments
            }
            
            profiles.append(profile)
        
        return profiles

    def _get_active_player_for_strategy(self, strategy: Strategy, game: Game):
        try:
            for round_obj in game.rounds:
                if round_obj.round_number == strategy.from_scenario.depth + 1:
                    return round_obj.active_player
        except:
            pass
        
        return game.players[0] if game.players else None

    def _get_payoffs_for_strategy(self, strategy: Strategy, game: Game) -> Dict[str, float]:
        payoffs = {}
        
        for payoff in game.payoffs:
            if payoff.history and strategy.action in payoff.history.actions:
                player_label = f"J{payoff.player.player_id}"
                payoffs[player_label] = payoff.value
        
        return payoffs

    def _export_equilibria_simple(self, game: Game, session: SessionManager, writer: pd.ExcelWriter) -> None:
        try:
            data = []
            equilibria = session.equilibria or []
            
            for i, equilibrium in enumerate(equilibria, 1):
                data.append([
                    i,
                    equilibrium.from_scenario.label if hasattr(equilibrium.from_scenario, 'label') else f"Escenario {equilibrium.from_scenario.scenario_id}",
                    equilibrium.action.label if hasattr(equilibrium.action, 'label') else f"Acción {equilibrium.action.action_id}",
                    getattr(equilibrium, 'utility', 0.0),
                    getattr(equilibrium, 'description', '')
                ])
            
            if data:
                df = pd.DataFrame(data, columns=[
                    'ID Equilibrio', 
                    'Escenario', 
                    'Acción', 
                    'Utilidad', 
                    'Descripción'
                ])
                df.to_excel(writer, sheet_name='Equilibrios', index=False)
                
                worksheet = writer.sheets['Equilibrios']
                worksheet.column_dimensions['A'].width = 15
                worksheet.column_dimensions['B'].width = 20
                worksheet.column_dimensions['C'].width = 15
                worksheet.column_dimensions['D'].width = 15
                worksheet.column_dimensions['E'].width = 25
        except Exception as e:
            self.logger.log_error(f"Error en exportación simple de equilibrios: {e}")




    def _export_summary(self, game: Game, session: SessionManager, writer: pd.ExcelWriter) -> None:
        utilidad_esperada_total = sum(p.expected_utility for p in game.payoffs)

        escenarios_normales = self._count_normal_scenarios(game.scenarios)
        
        summary_data = {
            'Métrica': [
                'Total Jugadores',
                'Total Rondas',
                'Estrategias por Jugador',
                'Total Escenarios',
                'Total Acciones',
                'Estrategias de Juego',
                'Total Historias',
                'Total Payoffs',
                'Total Utilidades Calculadas',
                'Utilidad Esperada Total',
                'Total Equilibrios'
            ],
            'Valor': [
                len(game.players),
                len(game.rounds),
                game.num_strategies,
                escenarios_normales,
                len(game.actions),
                len(game.actions),
                len(game.histories),
                len(game.payoffs),
                len(session.utility_matrix) if session.utility_matrix else 0,
                utilidad_esperada_total,
                len(session.equilibria)
            ]
        }
        
        df = pd.DataFrame(summary_data)
        df.to_excel(writer, sheet_name='Resumen', index=False)
        
        worksheet = writer.sheets['Resumen']
        worksheet.column_dimensions['A'].width = 30
        worksheet.column_dimensions['B'].width = 15

    def _count_normal_scenarios(self, scenarios: List[Scenario]) -> int:
        count = 0
        for scenario in scenarios:
            if (hasattr(scenario, 'label') and scenario.label.startswith('X')) or \
               (hasattr(scenario, 'scenario_type') and scenario.scenario_type == 'normal'):
                count += 1
        return count