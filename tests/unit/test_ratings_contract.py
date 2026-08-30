# ==============================================================================
# test_ratings_contract.py - Testes Unitários para o Contrato de Dados de Ratings
# ==============================================================================
"""Testes para o contrato de dados de ratings."""

from cinelake.data_quality.data_contracts.ratings_contract import RATINGS_CONTRACT


def test_contrato_possui_colunas_obrigatorias():
    """Valida se o contrato define todas as colunas obrigatórias da tabela ratings."""
    assert set(RATINGS_CONTRACT["columns"].keys()) == {"user_id", "movie_id", "rating", "ts"}


def test_contrato_define_rating_min_max():
    """Valida se os limites de nota mínima (0.5) e máxima (5.0) estão definidos no contrato."""
    colunas = RATINGS_CONTRACT["columns"]
    assert colunas["rating"]["min"] == 0.5
    assert colunas["rating"]["max"] == 5.0
