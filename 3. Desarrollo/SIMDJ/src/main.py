from __future__ import annotations
import os
import sys

#Pribando la rama Prueba 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = BASE_DIR

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# ---- Boundary Layer
from Boundary.Cli.cli_formatter import CLIFormatter
from Boundary.Cli.command_parser import CommandParser
from Boundary.Cli.cli_handler import CLIHandler

# ---- Control Layer
from Control.App.session_manager import SessionManager
from Control.App.game_controller import GameController
from Control.App.command_dispatcher import CommandDispatcher

# ---- Domain Layer (Common)
from Domain.Common.domain_validator import DomainValidator

# ---- Domain Layer (Simulation Services)
from Domain.Simulation.tree_builder import TreeBuilder
from Domain.Simulation.probability_assigner import ProbabilityAssigner
from Domain.Simulation.history_generator import HistoryGenerator
from Domain.Simulation.utility_calculator import UtilityCalculator
from Domain.Simulation.equilibrium_finder import EquilibriumFinder

# ---- Infrastructure Layer: Export
from Infrastructure.Export.excel_exporter import ExcelExporter
from Infrastructure.Export.tree_exporter import TreeExporter
from Infrastructure.Export.naming_service import NamingService

# ---- Infrastructure Common
from Infrastructure.Common.logger import Logger
from Infrastructure.Common.technical_validator import TechnicalValidator


def main() -> None:
    print("Iniciando SIM-DJ - Sistema de Simulación de Teoría de Juegos...")
    try:
        # ===========================================================
        # 1. INFRAESTRUCTURA - Common
        # ===========================================================
        logger = Logger()
        technical_validator = TechnicalValidator()

        # ===========================================================
        # 2. INFRAESTRUCTURA - Export
        # ===========================================================
        naming_service = NamingService()        

        excel_exporter = ExcelExporter(
            logger=logger, 
            naming_service=naming_service,
            technical_validator=technical_validator
        )

        tree_exporter = TreeExporter(
            logger=logger, 
            naming_service=naming_service,
            technical_validator=technical_validator

        )

        # ===========================================================
        # 3. DOMAIN - Common
        # ===========================================================
        domain_validator = DomainValidator()

        # ===========================================================
        # 4. DOMAIN - Simulation
        # ===========================================================
        tree_builder = TreeBuilder(
            logger=logger,
            domain_validator=domain_validator
        )
        
        probability_assigner = ProbabilityAssigner(
            logger=logger,
            domain_validator=domain_validator
        )
        
        history_generator = HistoryGenerator(
            logger=logger,
            domain_validator=domain_validator
        )
        
        utility_calculator = UtilityCalculator(
            logger=logger,
            domain_validator=domain_validator
        )
        
        equilibrium_finder = EquilibriumFinder(
            logger=logger,
            domain_validator=domain_validator
        )

        # ===========================================================
        # 6. CONTROL - App
        # ===========================================================
        session_manager = SessionManager(
            logger=logger,
            technical_validator=technical_validator           
            )

        game_controller = GameController(
            logger=logger,
            technical_validator=technical_validator,
            excel_exporter=excel_exporter,
            tree_exporter=tree_exporter,
            domain_validator=domain_validator,            
            tree_builder=tree_builder,
            probability_assigner=probability_assigner,
            history_generator=history_generator,
            utility_calculator=utility_calculator,
            equilibrium_finder=equilibrium_finder,
            session=session_manager
        )

        command_dispatcher = CommandDispatcher(
            logger=logger,
            technical_validator=technical_validator,
            game_controller=game_controller
        )

        # ===========================================================
        # 8. Boundary - Cli
        # ===========================================================
        command_parser = CommandParser()

        cli_formatter = CLIFormatter()

        cli_handler = CLIHandler(
            formatter=cli_formatter,
            parser=command_parser,
            dispatcher=command_dispatcher,
            technical_validator=technical_validator,
            domain_validator=domain_validator,
            logger=logger
        )

        # ===========================================================
        # 10. EJECUCIÓN
        # ===========================================================
        print("Sistema configurado correctamente")
        print("Usa la opción [4] para salir del sistema\n")
        
        cli_handler.run()

    except Exception as error:
        print(f"Error crítico durante la inicialización: {error}")
        import traceback
        traceback.print_exc()
        sys.exit()


if __name__ == "__main__":
    main()