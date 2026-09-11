#!/usr/bin/env bash
# Script Bash de rollback automatizado para o projeto CineLake AI.

# Configura o comportamento estrito do script em caso de erros:
# -e: Aborta a execução imediatamente se qualquer comando falhar (retornar código diferente de 0)
# -u: Trata variáveis não declaradas/nulas como um erro grave
# -o pipefail: Garante que erros em pipelines de comandos (ex: cmd1 | cmd2) não sejam ignorados
set -euo pipefail

# Exibe no terminal a mensagem indicando o início do procedimento de rollback
echo "[rollback] Iniciando rollback"

# Navega até o diretório raiz do repositório (um nível acima da pasta scripts/)
cd "$(dirname "$0")/.."

# Verifica se o arquivo .last_good_tag existe no diretório raiz do projeto
if [ ! -f .last_good_tag ]; then
  # Se o arquivo não for encontrado, exibe mensagem informando que não há versão anterior salva
  echo "[rollback] Nenhuma tag anterior registrada"
  # Encerra o script com código de falha (1) para notificar o sistema de CI/CD
  exit 1
# Fim da verificação condicional do arquivo
fi

# Lê o conteúdo armazenado no arquivo .last_good_tag e salva a tag da imagem anterior na variável TAG
TAG=$(cat .last_good_tag)

# Exibe no log a tag de versão estável para a qual a aplicação será revertida
echo "[rollback] Revertendo para tag $TAG"

# Derruba todos os contêineres e serviços atuais do Docker Compose
docker compose down

# Inicia os contêineres do Docker Compose em segundo plano (-d) utilizando a imagem com a tag da versão estável salvada
CINELAKE_IMAGE_TAG="$TAG" docker compose up -d

# Exibe no terminal a mensagem de sucesso indicando a finalização do processo de rollback
echo "[rollback] Rollback concluído"
