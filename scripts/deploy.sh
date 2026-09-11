#!/usr/bin/env bash
# Script de deploy automatizado do CineLake AI na VPS.
set -euo pipefail

echo "[deploy] Iniciando deploy do CineLake AI"
cd "$(dirname "$0")/.."

echo "[deploy] Atualizando repositório"
git pull --ff-only origin main

echo "[deploy] Baixando imagens atualizadas"
docker compose pull

echo "[deploy] Subindo serviços"
docker compose up -d --remove-orphans

echo "[deploy] Aplicando migrações Alembic"
docker compose exec -T api alembic upgrade head

echo "[deploy] Rodando dbt"
docker compose exec -T api bash -c "cd dbt_project && dbt run --profiles-dir ."

echo "[deploy] Aguardando API"
for i in {1..10}; do
  if curl -sf http://127.0.0.1:8002/health > /dev/null; then
    echo "[deploy] API saudável"
    break
  fi
  echo "[deploy] Tentativa $i: API ainda não respondeu"
  sleep 5
done

echo "[deploy] Deploy concluído com sucesso"
