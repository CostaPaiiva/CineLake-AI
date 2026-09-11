#!/usr/bin/env bash
# Script Bash de deploy automatizado com salvamento da última tag estável para o CineLake AI.

# Configura o comportamento estrito do script em caso de erros:
# -e: Aborta a execução imediatamente se qualquer comando falhar
# -u: Trata variáveis não declaradas como erro
# -o pipefail: Garante que falhas em pipelines de comandos não sejam ignoradas
set -euo pipefail

# Exibe mensagem inicial do processo de deploy
echo "[deploy] Iniciando deploy do CineLake AI"

# Navega até o diretório raiz do repositório
cd "$(dirname "$0")/.."

# Obtém a tag/hash reduzida (7 caracteres) do commit Git atual antes da atualização
TAG_ATUAL=$(git rev-parse --short HEAD)

# Exibe a tag atual do repositório no terminal
echo "[deploy] Tag atual: $TAG_ATUAL"

# Atualiza o repositório local trazendo as novidades da branch main do GitHub (apenas fast-forward)
echo "[deploy] Atualizando repositório"
git pull --ff-only origin main

# Baixa as imagens Docker atualizadas do container registry (GHCR)
echo "[deploy] Baixando imagens atualizadas"
docker compose pull

# Sobe os contêineres e serviços em segundo plano, removendo contêineres órfãos
echo "[deploy] Subindo serviços"
docker compose up -d --remove-orphans

# Executa as migrações de esquema do banco de dados PostgreSQL via Alembic dentro do contêiner da API
echo "[deploy] Aplicando migrações Alembic"
docker compose exec -T api alembic upgrade head

# Executa as transformações SQL e compilação de modelos dbt dentro do contêiner da API
echo "[deploy] Rodando dbt"
docker compose exec -T api bash -c "cd dbt_project && dbt run --profiles-dir ."

# Inicia a verificação da saúde da API através de loop com 12 tentativas
echo "[deploy] Aguardando API"
SAUDAVEL=false
for i in {1..12}; do
  # Testa se o endpoint HTTP /health da API responde com status 200 OK
  if curl -sf http://127.0.0.1:8002/health > /dev/null; then
    # Marca a API como saudável e encerra o loop de tentativas
    echo "[deploy] API saudável"
    SAUDAVEL=true
    break
  fi
  # Exibe mensagem de espera a cada tentativa com intervalo de 5 segundos
  echo "[deploy] Tentativa $i: API ainda não respondeu"
  sleep 5
done

# Caso a API não responda dentro do limite de 12 tentativas (60s), falha o deploy
if [ "$SAUDAVEL" != "true" ]; then
  echo "[deploy] Healthcheck falhou"
  exit 1
fi

# Salva a tag da versão bem-sucedida no arquivo .last_good_tag para possibilitar rollback futuro
echo "$TAG_ATUAL" > .last_good_tag

# Exibe mensagem final de sucesso do deploy
echo "[deploy] Deploy concluído com sucesso"
