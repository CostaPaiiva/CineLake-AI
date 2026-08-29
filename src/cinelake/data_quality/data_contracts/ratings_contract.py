# ==============================================================================
# ratings_contract.py - Contrato de Dados para a Tabela / Dataset ratings
# ==============================================================================
"""Contrato de dados e validação de expectativas para a tabela ratings."""

from typing import Any

# Definição do schema e regras de integridade de dados esperadas
RATINGS_CONTRACT: dict[str, Any] = {
    "table_name": "ratings",
    "columns": {
        # Identificador do usuário (não nulo e >= 1)
        "user_id": {
            "type": "int64",
            "nullable": False,
            "min": 1,
        },
        # Identificador do filme (não nulo e >= 1)
        "movie_id": {
            "type": "int64",
            "nullable": False,
            "min": 1,
        },
        # Nota atribuída pelo usuário (escala de 0.5 a 5.0)
        "rating": {
            "type": "float64",
            "nullable": False,
            "min": 0.5,
            "max": 5.0,
        },
        # Timestamp Unix numérico em segundos
        "ts": {
            "type": "int64",
            "nullable": False,
        },
    },
    # Regras de expectativas baseadas no framework Great Expectations
    "constraints": [
        {"expectation": "expect_column_values_to_not_be_null", "column": "user_id"},
        {"expectation": "expect_column_values_to_not_be_null", "column": "movie_id"},
        {"expectation": "expect_column_values_to_not_be_null", "column": "rating"},
        {"expectation": "expect_column_values_to_not_be_null", "column": "ts"},
        {"expectation": "expect_column_min_to_be_between", "column": "rating", "min_value": 0.5},
        {"expectation": "expect_column_max_to_be_between", "column": "rating", "max_value": 5.0},
    ],
}