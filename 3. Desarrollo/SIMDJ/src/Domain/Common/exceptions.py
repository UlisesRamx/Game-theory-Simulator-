# Domain/Common/exceptions.py
from __future__ import annotations
from typing import Any

class GameException(Exception):
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message)
        self.user_message = user_message or message
        self.technical_message = message

# ===========================================================
# Excepciones Especiales
# ===========================================================

class TechnicalValidationError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error en el formato de los datos ingresados."
        super().__init__(technical_message, user_msg)

class InvalidInputError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Entrada inválida. Verifique los datos ingresados."
        super().__init__(technical_message, user_msg)

class NoActiveGameError(GameException):
    def __init__(self, technical_message: str = "No hay juego activo", user_message: str = None):
        user_msg = user_message or "No hay Juego Activo. Cree un nuevo JUEGO desde el Menú Principal."
        super().__init__(technical_message, user_msg)  # ✅ Ahora acepta user_message

class PlayerOrderError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error en el orden de jugadores. Verifique los IDs ingresados."
        super().__init__(technical_message, user_msg)

class GameStateError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Estado del juego inválido para esta operación."
        super().__init__(technical_message, user_msg)

class ConfigurationError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error durante la configuración del orden. Intente nuevamente."
        super().__init__(technical_message, user_msg)

class ValidationError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error de validación. Verifique los datos ingresados."
        super().__init__(technical_message, user_msg)

class ComplexityError(GameException):
    def __init__(self, scenarios: int, strategies: int, user_message: str = None):
        technical_message = f"Complejidad excesiva: {scenarios} escenarios, {strategies} estrategias"
        user_msg = user_message or f"Complejidad Excesiva. Escenarios: {scenarios}, Acciones: {strategies}."
        super().__init__(technical_message, user_msg)

class OperationError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error durante la ejecución de la operación."
        super().__init__(technical_message, user_msg)

class TreeExporterNotConfiguredError(GameException):
    def __init__(self, technical_message: str = "TreeExporter no configurado", user_message: str = None):
        user_msg = user_message or "Error de configuración del sistema. Contacte al administrador."
        super().__init__(technical_message, user_msg)

class ExportError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error durante la exportación. Intente nuevamente."
        super().__init__(technical_message, user_msg)

class DeletionError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error durante la eliminación del juego. Intente nuevamente."
        super().__init__(technical_message, user_msg)

class GameCreationError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error durante la creación del juego. Intente nuevamente."
        super().__init__(technical_message, user_msg)

class PayoffRegistrationError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error durante el registro de pagos. Intente nuevamente."
        super().__init__(technical_message, user_msg)

class MissingValueError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error por la falta de valor en las variables."
        super().__init__(technical_message, user_msg)

class TreeBuilderError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error en la contrucción del árbol de decisiones. Verifique los datos ingresados."
        super().__init__(technical_message, user_msg)

class ProbabilityAssignmentError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error en la asignación de probabilidades. Verifique los datos ingresados."
        super().__init__(technical_message, user_msg)

class HistoryGenerationError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error en la generación de historias. Verifique la estructura del juego."
        super().__init__(technical_message, user_msg)

class UtilityCalculationError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error en el cálculo de utilidades. Verifique los pagos y probabilidades."
        super().__init__(technical_message, user_msg)

class EquilibriumFindingError(GameException):
    def __init__(self, technical_message: str, user_message: str = None):
        user_msg = user_message or "Error en la búsqueda de equilibrios. Verifique los datos del juego."
        super().__init__(technical_message, user_msg)