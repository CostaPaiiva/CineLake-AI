#!/usr/bin/env bash
# Define o interpretador de comandos Bash usando o env para portabilidade em diferentes sistemas
# Cancela e interrompe a execução imediatamente se qualquer comando falhar (retornar código de erro diferente de 0)
set -e

# Exibe mensagem informativa indicando o início das verificações do pipeline de CI
echo "Executando verificações de CI..."

# Executa o linter Ruff para checagem estática de qualidade e formato de código em todo o repositório
ruff check .

# Executa o checador estático de tipos Mypy no diretório do código-fonte (src)
mypy src

# Executa os testes unitários via Pytest ignorando testes marcados como integração (not integration) em modo detalhado (-v)
pytest -m "not integration" -v

# Entra na pasta do projeto dbt e executa a compilação das queries e modelos analíticos
cd dbt_project && dbt compile --profiles-dir .
