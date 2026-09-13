#!/usr/bin/env bash
# Verificação básica de segurança na VPS.
# Define flags para encerrar o script em caso de erro, variável indefinida ou falha em pipes
set -euo pipefail

# Exibe cabeçalho informativo sobre a verificação do firewall UFW
echo "[security] Verificando UFW"
# Executa o comando de status detalhado do firewall UFW com privilégios administrativos
sudo ufw status verbose

# Exibe cabeçalho informativo sobre a verificação do serviço Fail2ban
echo "[security] Verificando fail2ban"
# Checa o status de execução do daemon fail2ban sem quebrar a paginação do terminal
sudo systemctl status fail2ban --no-pager

# Exibe cabeçalho informativo sobre a verificação das portas de rede abertas
echo "[security] Verificando portas abertas"
# Lista todos os sockets TCP e UDP em estado de escuta (listening) com os números de portas e processos associados
sudo ss -tulnp

# Exibe cabeçalho informativo sobre a verificação de permissões do arquivo de variáveis de ambiente
echo "[security] Verificando permissões do .env"
# Exibe a listagem detalhada de permissões de leitura/escrita e proprietário do arquivo .env
ls -l .env

# Exibe cabeçalho informativo sobre a auditoria de usuários em containers Docker ativos
echo "[security] Verificando containers rodando como root"
# Itera sobre todos os containers em execução para inspecionar o usuário configurado
docker ps --format '{{.Names}}' | while read -r c; do
  # Inspeciona a propriedade User de cada container
  user=$(docker inspect --format '{{.Config.User}}' "$c")
  # Imprime o nome do container e o usuário associado (ou root caso esteja vazio)
  echo "$c -> user: ${user:-root}"
done
