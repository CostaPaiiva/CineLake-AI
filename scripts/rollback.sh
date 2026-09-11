#!/usr/bin/env bash
# Rollback simples: volta para a imagem anterior se disponível.
set -euo pipefail

echo "[rollback] Iniciando rollback"
cd "$(dirname "$0")/.."

if [ ! -f .last_good_tag ]; then
  echo "[rollback] Nenhuma tag anterior registrada"
  exit 1
fi

TAG=$(cat .last_good_tag)
echo "[rollback] Revertendo para tag $TAG"

docker compose down
CINELAKE_IMAGE_TAG="$TAG" docker compose up -d

echo "[rollback] Rollback concluído"
