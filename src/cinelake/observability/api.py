"""API FastAPI para expor endpoints REST de observabilidade e métricas de saúde da plataforma."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException

from cinelake.observability.health import coletar_status_geral

logger = logging.getLogger(__name__)

# Instância principal do aplicativo FastAPI de observabilidade
app = FastAPI(title="CineLake AI - Observabilidade", version="0.1.0")


@app.get("/health", summary="Verifica saúde geral da plataforma")
def health() -> dict[str, Any]:
    """Retorna o status completo de saúde da plataforma (conectividade, contagem de tabelas e freshness)."""
    try:
        status = coletar_status_geral()
        return status
    except Exception as exc:
        logger.exception("Erro ao coletar status de saúde")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metrics", summary="Resumo de métricas principais")
def metrics() -> dict[str, Any]:
    """Retorna um resumo contendo as contagens de linhas das tabelas e a atualidade (freshness) das fontes."""
    try:
        status = coletar_status_geral()
        return {
            "contagens": status.get("contagens", {}),
            "fontes": status.get("fontes", {}),
        }
    except Exception as exc:
        logger.exception("Erro ao coletar métricas")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/freshness", summary="Freshness das fontes de dados")
def freshness() -> dict[str, Any]:
    """Retorna apenas os indicadores de atualidade/frescor das fontes de dados em minutos."""
    try:
        status = coletar_status_geral()
        fontes = status.get("fontes", {})
        return dict(fontes) if isinstance(fontes, dict) else {}
    except Exception as exc:
        logger.exception("Erro ao coletar freshness")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

