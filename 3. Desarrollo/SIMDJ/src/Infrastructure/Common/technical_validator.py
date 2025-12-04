# src/infrastructure/common/technical_validator.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Sequence

from Domain.Common.exceptions import TechnicalValidationError, InvalidInputError


@dataclass
class TechnicalValidator:
    """
    Validaciones técnicas genéricas que lanzan excepciones al fallar.
    """

    def validate_numeric_range(
        self, 
        value: float, 
        min_val: float, 
        max_val: float, 
        field_name: str = "valor"
    ) -> None:
        try:
            numeric_value = float(value)
            if not (min_val <= numeric_value <= max_val):
                raise TechnicalValidationError(
                    technical_message=f"Valor {value} fuera de rango [{min_val}, {max_val}]",
                    user_message=f"El {field_name} debe estar entre {min_val} y {max_val}"
                )
            else:
                return True
        except (TypeError, ValueError):
            raise InvalidInputError(
                technical_message=f"Valor {value} no es numérico válido",
                user_message=f"El {field_name} debe ser un número válido"
            )
            

    def validate_probability_range(self, value: float, field_name: str = "probabilidad") -> None:
        self.validate_numeric_range(value, 0.0, 1.0, field_name)

    def validate_positive_integer(self, value: int, field_name: str = "valor") -> None:
        try:
            int_value = int(value)
            if int_value <= 0:
                raise TechnicalValidationError(
                    technical_message=f"Valor {value} no es positivo",
                    user_message=f"El {field_name} debe ser un número entero positivo"
                )
        except (TypeError, ValueError):
            raise InvalidInputError(
                technical_message=f"Valor {value} no es entero válido",
                user_message=f"El {field_name} debe ser un número entero válido"
            )

    def validate_list_not_empty(self, data: Sequence[Any], field_name: str = "lista") -> None:
        if data is None or len(data) == 0:
            raise TechnicalValidationError(
                technical_message=f"La {field_name} está vacía o es nula",
                user_message=f"La {field_name} no puede estar vacía"
            )

    def validate_string_not_empty(self, value: str, field_name: str = "texto") -> None:
        if value is None or len(value.strip()) == 0:
            raise TechnicalValidationError(
                technical_message=f"El {field_name} está vacío o es nulo",
                user_message=f"El {field_name} no puede estar vacío"
            )

    def is_numeric_in_range(self, value: float, min_val: float, max_val: float) -> bool:
        try:
            numeric_value = float(value)
            return min_val <= numeric_value <= max_val
        except (TypeError, ValueError):
            return False