# Módulo responsável pela integração e invocação local de ferramentas MCP do CineLake.
"""Cliente MCP local para invocar ferramentas do CineLake."""

# Importa o módulo importlib para importação dinâmica de módulos Python.
import importlib
# Importa o módulo nativo de logging para registro de mensagens e diagnósticos.
import logging
# Importa o tipo Any do módulo typing para anotações de tipos genéricos.
from typing import Any

# Define o logger específico para este módulo.
logger = logging.getLogger(__name__)


# Define a função para invocar uma ferramenta MCP localmente recebendo o nome da função e seus argumentos.
def invocar_ferramenta_mcp(nome_ferramenta: str, argumentos: dict[str, Any] | None = None) -> Any:
    # Docstring explicativa das responsabilidades da função e seus parâmetros.
    """
    Invoca uma ferramenta MCP localmente.

    Como o MCP Server V1 é nosso, importamos diretamente as funções.
    Em uma arquitetura distribuída, isso seria substituído por chamadas HTTP/SSE.

    Args:
        nome_ferramenta: Nome da ferramenta (ex.: get_platform_health).
        argumentos: Dicionário com argumentos da ferramenta.

    Returns:
        Resultado retornado pela ferramenta.
    """
    # Garante que o parâmetro argumentos seja um dicionário (se for None, inicializa como dicionário vazio).
    argumentos = argumentos or {}
    # Bloco try para capturar e tratar possíveis exceções durante a execução da ferramenta.
    try:
        # Comentário explicativo sobre o mapeamento dinâmico.
        # Mapeia nomes para funções do módulo mcp_server
        # Importa dinamicamente o módulo onde as ferramentas do servidor MCP estão definidas.
        modulo = importlib.import_module("cinelake.mcp_server.tools")
        # Obtém a função desejada a partir do nome informado como atributo do módulo importado.
        funcao = getattr(modulo, nome_ferramenta)
        # Registra no log a tentativa de invocação da ferramenta MCP especificada.
        logger.info("Invocando ferramenta MCP: %s", nome_ferramenta)
        # Executa a função passando os argumentos desempacotados em chave-valor (se existirem) ou sem argumentos.
        resultado = funcao(**argumentos) if argumentos else funcao()
        # Retorna o resultado gerado pela execução da ferramenta.
        return resultado
    # Captura a exceção caso a função/ferramenta solicitada não exista no módulo.
    except AttributeError:
        # Registra no log o erro informando que a ferramenta MCP não foi encontrada.
        logger.error("Ferramenta MCP não encontrada: %s", nome_ferramenta)
        # Relança a exceção AttributeError capturada.
        raise
    # Captura qualquer outra exceção genérica ocorrida durante a execução da ferramenta.
    except Exception as exc:
        # Registra no log o erro informando a falha durante a invocação da ferramenta MCP.
        logger.error("Erro ao invocar ferramenta MCP: %s", exc)
        # Relança a exceção capturada para tratamento nos níveis superiores.
        raise
