from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

from Domain.Core.game import Game
from Domain.Core.player import Player
from Domain.Core.strategy import Strategy
from Domain.Core.scenario import Scenario
from Domain.Core.action import Action
from Domain.Core.history import History
from Domain.Core.payoff import Payoff

from Domain.Common.domain_validator import DomainValidator
from Domain.Common.exceptions import (
    EquilibriumFindingError, ValidationError
)

from Infrastructure.Common.logger import Logger


@dataclass
class EquilibriumStep:
    round_num: int
    player: str
    scenario: str
    action: str
    destination: str
    payoffs: Dict[str, float]


@dataclass
class EquilibriumProfile:
    profile_id: int
    strategies: List[Strategy]
    steps: List[EquilibriumStep]
    full_history: str
    final_payments: Dict[str, float]
    utility_vector: List[float]


class EquilibriumFinder:
    def __init__(
        self,
        logger: Logger,
        domain_validator: DomainValidator
    ):
        self.logger = logger
        self.domain_validator = domain_validator
        self.equilibrium_profiles: List[EquilibriumProfile] = []

    def find_spe_profiles(
        self,
        game: Game,
        histories: List[History],
        payoffs: List[Payoff],
        players: List[Player]
    ) -> List[List[Strategy]]:
        try:
            self.domain_validator.validate_equilibrium_finding_data(
                game, histories, payoffs, players
            )

            self.equilibrium_profiles.clear()

            adjacency: Dict[int, List[Action]] = self._build_adjacency(game)
            
            action_to_histories = self._map_actions_to_histories(histories)
            
            history_utilities = self._build_history_utilities(histories, payoffs, players)
            
            spe_profiles = self._find_all_spe_profiles(
                game, adjacency, action_to_histories, history_utilities, players
            )
            
            for i, profile_strategies in enumerate(spe_profiles, 1):
                eq_profile = self._build_equilibrium_profile(
                    i, profile_strategies, game, players, histories, payoffs
                )
                if eq_profile:
                    self.equilibrium_profiles.append(eq_profile)
            
            self.logger.log_info(
                f"[EquilibriumFinder] {len(self.equilibrium_profiles)} equilibrios encontrados."
            )
            
            return [profile.strategies for profile in self.equilibrium_profiles]
            
        except (EquilibriumFindingError, ValidationError) as error:
            self.logger.log_warning(f"[EquilibriumFinder] Error buscando equilibrios: {error.technical_message}")
            raise
        except Exception as error:
            self.logger.log_error(f"[EquilibriumFinder] Error inesperado al buscar equilibrios: {error}")
            raise EquilibriumFindingError(
                technical_message=f"Error técnico buscando equilibrios: {error}",
                user_message="Error al buscar los equilibrios del juego."
            )

    def _find_all_spe_profiles(
        self,
        game: Game,
        adjacency: Dict[int, List[Action]],
        action_to_histories: Dict[int, List[History]],
        history_utilities: Dict[int, Dict[int, float]],
        players: List[Player]
    ) -> List[List[Strategy]]:
        scenarios_by_depth = defaultdict(list)
        for scenario in game.scenarios:
            scenarios_by_depth[scenario.depth].append(scenario)
        
        max_depth = max(scenarios_by_depth.keys()) if scenarios_by_depth else 0
        
        best_continuations: Dict[int, List[Tuple[Action, float, List[Strategy]]]] = {}
        
        next_strategy_id = 1
        
        for depth in range(max_depth, -1, -1):
            for scenario in scenarios_by_depth[depth]:
                if scenario.is_terminal():
                    continue
                
                outgoing_actions = adjacency.get(scenario.scenario_id, [])
                if not outgoing_actions:
                    continue
                
                active_player = self._get_active_player_for_scenario(scenario, game, players)
                if active_player is None:
                    self.logger.log_warning(f"No se pudo determinar jugador activo para escenario {scenario.scenario_id}")
                    continue
                
                action_results = []
                for action in outgoing_actions:
                    continuation_utility = self._calculate_continuation_utility(
                        action, active_player, action_to_histories, history_utilities
                    )
                    
                    continuation_strategies = []
                    if action.destination_scenario:
                        dest_id = action.destination_scenario.scenario_id
                        if dest_id in best_continuations:
                            for (_, _, strategies) in best_continuations[dest_id]:
                                strategy = Strategy(
                                    strategy_id=next_strategy_id,
                                    from_scenario=scenario,
                                    action=action
                                )
                                next_strategy_id += 1
                                continuation_strategies.append([strategy] + strategies)
                        else:
                            strategy = Strategy(
                                strategy_id=next_strategy_id,
                                from_scenario=scenario,
                                action=action
                            )
                            next_strategy_id += 1
                            continuation_strategies.append([strategy])
                    
                    action_results.append((action, continuation_utility, continuation_strategies))
                
                if not action_results:
                    continue
                
                max_utility = max(util for _, util, _ in action_results)
                
                best_actions = []
                for action, utility, continuations in action_results:
                    if abs(utility - max_utility) < 1e-6:
                        best_actions.append((action, continuations))
                
                scenario_continuations = []
                for action, continuations in best_actions:
                    for continuation in continuations:
                        scenario_continuations.append((action, max_utility, continuation))
                
                best_continuations[scenario.scenario_id] = scenario_continuations
        
        root_scenarios = [s for s in game.scenarios if s.depth == 0]
        if not root_scenarios:
            return []
        
        root_scenario = root_scenarios[0]
        all_profiles = []
        
        if root_scenario.scenario_id in best_continuations:
            for (_, _, strategies) in best_continuations[root_scenario.scenario_id]:
                all_profiles.append(strategies)
        
        return all_profiles

    def _build_equilibrium_profile(
        self,
        profile_id: int,
        strategies: List[Strategy],
        game: Game,
        players: List[Player],
        histories: List[History],
        payoffs: List[Payoff]
    ) -> Optional[EquilibriumProfile]:
        try:
            for strategy in strategies:
                if strategy.strategy_id <= 0:
                    self.logger.log_error(f"Estrategia con ID inválido: {strategy.strategy_id}")
                    return None
            
            strategies_sorted = sorted(strategies, key=lambda s: s.from_scenario.depth)
            
            steps = []
            
            for strategy in strategies_sorted:
                active_player = self._get_active_player_for_scenario(
                    strategy.from_scenario, game, players
                )
                if not active_player:
                    self.logger.log_warning(f"No se pudo determinar jugador activo para escenario {strategy.from_scenario.scenario_id}")
                    continue
                    
                player_label = f"J{active_player.player_id}"
                
                destination = "Terminal"
                if strategy.action.destination_scenario:
                    destination = strategy.action.destination_scenario.label
                
                step_payoffs = self._get_payoffs_for_scenario_action(
                    strategy.from_scenario, strategy.action, histories, payoffs, players
                )
                
                step = EquilibriumStep(
                    round_num=strategy.from_scenario.depth + 1,
                    player=player_label,
                    scenario=strategy.from_scenario.label,
                    action=strategy.action.label,
                    destination=destination,
                    payoffs=step_payoffs
                )
                steps.append(step)
            
            if not steps:
                return None
            
            full_history = self._build_full_history(strategies_sorted)
            
            final_payments = steps[-1].payoffs if steps else {}
            
            utility_vector = self._calculate_utility_vector(steps, players)
            
            return EquilibriumProfile(
                profile_id=profile_id,
                strategies=strategies,
                steps=steps,
                full_history=full_history,
                final_payments=final_payments,
                utility_vector=utility_vector
            )
            
        except Exception as error:
            self.logger.log_warning(f"Error construyendo perfil {profile_id}: {error}")
            return None

    def _get_payoffs_for_scenario_action(
        self,
        scenario: Scenario,
        action: Action,
        histories: List[History],
        payoffs: List[Payoff],
        players: List[Player]
    ) -> Dict[str, float]:
        result = {f"J{p.player_id}": 0.0 for p in players}
        
        for history in histories:
            if action in history.actions:
                action_index = history.actions.index(action)
                if action_index > 0:
                    prev_action = history.actions[action_index - 1]
                    if (prev_action.destination_scenario and 
                        prev_action.destination_scenario.scenario_id == scenario.scenario_id):
                        for payoff in payoffs:
                            if payoff.history.history_id == history.history_id:
                                player_label = f"J{payoff.player.player_id}"
                                result[player_label] = payoff.value
                        break
        
        return result

    def _build_full_history(self, strategies: List[Strategy]) -> str:
        parts = []
        
        for strategy in sorted(strategies, key=lambda s: s.from_scenario.depth):
            parts.append(strategy.from_scenario.label)
            parts.append(strategy.action.label)
            
            if strategy.action.destination_scenario:
                if strategy.action.destination_scenario.is_terminal():
                    parts.append(strategy.action.destination_scenario.label)
        
        return " -> ".join(parts)

    def _calculate_utility_vector(
        self,
        steps: List[EquilibriumStep],
        players: List[Player]
    ) -> List[float]:
        if not steps:
            return [0.0] * len(players)
        
        last_step = steps[-1]
        return [last_step.payoffs.get(f"J{p.player_id}", 0.0) for p in players]

    def _build_adjacency(self, game: Game) -> Dict[int, List[Action]]:
        adjacency: Dict[int, List[Action]] = {}
        
        for action in game.actions:
            if action.origin_scenario:
                origin_id = action.origin_scenario.scenario_id
                adjacency.setdefault(origin_id, []).append(action)
        
        return adjacency

    def _map_actions_to_histories(self, histories: List[History]) -> Dict[int, List[History]]:
        action_to_histories: Dict[int, List[History]] = {}
        
        for history in histories:
            for action in history.actions:
                action_to_histories.setdefault(action.action_id, []).append(history)
        
        return action_to_histories

    def _build_history_utilities(
        self,
        histories: List[History],
        payoffs: List[Payoff],
        players: List[Player]
    ) -> Dict[int, Dict[int, float]]:
        history_utilities: Dict[int, Dict[int, float]] = {}
        
        for history in histories:
            history_utilities[history.history_id] = {
                p.player_id: 0.0 for p in players
            }
        
        for payoff in payoffs:
            history_id = payoff.history.history_id
            player_id = payoff.player.player_id
            history_utilities[history_id][player_id] = payoff.value
        
        return history_utilities

    def _calculate_continuation_utility(
        self,
        action: Action,
        player: Player,
        action_to_histories: Dict[int, List[History]],
        history_utilities: Dict[int, Dict[int, float]]
    ) -> float:
        """Calcula la utilidad de continuación para una acción."""
        total_utility = 0.0
        count = 0
        
        for history in action_to_histories.get(action.action_id, []):
            total_utility += history_utilities[history.history_id].get(player.player_id, 0.0)
            count += 1
        
        return total_utility / count if count > 0 else 0.0

    def _get_active_player_for_scenario(
        self,
        scenario: Scenario,
        game: Game,
        players: List[Player]
    ) -> Optional[Player]:
        try:
            for round_obj in game.rounds:
                if round_obj.round_number == scenario.depth + 1:
                    if round_obj.active_player:
                        return round_obj.active_player
            
            if players:
                return players[scenario.depth % len(players)]
            
            return None
            
        except Exception as error:
            self.logger.log_error(f"Error obteniendo jugador activo: {error}")
            return None

    def format_equilibrium_profile(
        self,
        profile: EquilibriumProfile,
        current_index: int,
        total_count: int
    ) -> List[str]:
        lines = []
        lines.append(f"Análisis de Equilibrios completado: {current_index}/{total_count} SPE")
        lines.append("-" * 70)
        lines.append("Ronda| Jugador| Escenario| Acción  | Destino  | Pago")
        lines.append("-" * 70)
        
        for step in profile.steps:
            payoff_str = ", ".join([
                f"{player}:{value:.1f}" for player, value in step.payoffs.items()
            ])
            
            line = (
                f"{step.round_num:^5} | "
                f"{step.player:^7} | "
                f"{step.scenario:^9} | "
                f"{step.action:^7} | "
                f"{step.destination:^9} | "
                f"{payoff_str}"
            )
            lines.append(line)
        
        lines.append("")
        
        lines.append(f"Historia completa: {profile.full_history}")
        
        final_str = ", ".join([
            f"{player}={value:.1f}" for player, value in profile.final_payments.items()
        ])
        lines.append(f"Pagos finales: {final_str}")
        
        lines.append("-" * 70)
        
        return lines

    def get_navigation_controls(
        self,
        current_index: int,
        total_count: int
    ) -> str:
        if total_count == 1:
            return "[ENTER] Continuar"
        
        if current_index == 1:
            return "[d] = Siguiente SPE"
        elif current_index == total_count:
            return "[a] = Anterior SPE  | [ENTER] Continuar"
        else:
            return "[a] = Anterior SPE  | [d] = Siguiente SPE"

    def get_equilibrium_profiles(self) -> List[EquilibriumProfile]:
        return list(self.equilibrium_profiles)

    def clear_equilibria(self) -> None:
        self.equilibrium_profiles.clear()