"""Cliente Python para a API do TMDb com retry, timeout e rate limit."""

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class TMDBClient:
    """Cliente HTTP robusto para interagir com a API REST do The Movie Database (TMDb)."""

    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(
        self,
        api_key: str,
        requests_per_second: float = 4.0,
        timeout: int = 10,
    ) -> None:
        """Inicializa o cliente do TMDb com configurações de throttling e resiliência.

        Args:
            api_key: Chave de API de autenticação do TMDb.
            requests_per_second: Limite máximo de requisições disparadas por segundo.
            timeout: Tempo limite máximo de espera para cada requisição (em segundos).
        """
        self.api_key = api_key
        self.timeout = timeout
        # Intervalo mínimo obrigatório entre requisições consecutivas
        self._min_interval = 1.0 / requests_per_second
        self._last_request_time = 0.0

    def _respeitar_rate_limit(self) -> None:
        """Pausa a execução pelo tempo necessário para respeitar o limite de taxa (rate limit)."""
        agora = time.monotonic()
        # Calcula quanto tempo falta para cumprir o intervalo mínimo
        diferenca = self._min_interval - (agora - self._last_request_time)
        if diferenca > 0:
            logger.debug("Aguardando %.2fs para respeitar rate limit", diferenca)
            time.sleep(diferenca)
        # Atualiza o timestamp da última requisição realizada
        self._last_request_time = time.monotonic()

    def _fazer_requisicao(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executa uma requisição GET com tentativas automáticas (retry) e backoff exponencial.

        Args:
            endpoint: Caminho relativo da API (ex.: /movie/550).
            params: Parâmetros opcionais da query string.

        Returns:
            Dicionário com o payload JSON decodificado. Retorna {} se status for 404 (Not Found).
        """
        params = params or {}
        # Injeta a chave de API nos parâmetros da requisição
        params["api_key"] = self.api_key

        url = f"{self.BASE_URL}{endpoint}"

        tentativas = 0
        max_tentativas = 5
        backoff = 1.0

        # Loop de retentativas para garantir resiliência contra oscilações de rede
        while tentativas < max_tentativas:
            # Garante que a requisição não estoure o rate limit da API
            self._respeitar_rate_limit()
            tentativas += 1

            try:
                logger.info("Requisição para %s (tentativa %d)", endpoint, tentativas)
                resposta = requests.get(url, params=params, timeout=self.timeout)
                # Levanta exceção se o status HTTP for de erro (4xx, 5xx)
                resposta.raise_for_status()
                return resposta.json()  # type: ignore[no-any-return]

            except requests.exceptions.Timeout:
                logger.warning(
                    "Timeout na requisição %s. Tentativa %d/%d",
                    endpoint,
                    tentativas,
                    max_tentativas,
                )
            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code if exc.response else None
                logger.warning(
                    "Erro HTTP %s em %s. Tentativa %d/%d",
                    status_code,
                    endpoint,
                    tentativas,
                    max_tentativas,
                )
                if status_code == 404:
                    # Se o filme não existe no catálogo do TMDb, não adianta tentar novamente
                    logger.info("Recurso não encontrado no TMDB: %s", endpoint)
                    return {}
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "Erro de requisição em %s: %s. Tentativa %d/%d",
                    endpoint,
                    exc,
                    tentativas,
                    max_tentativas,
                )

            # Se ainda houver tentativas restantes, aguarda com backoff exponencial
            if tentativas < max_tentativas:
                logger.info("Aguardando %.1fs antes da próxima tentativa...", backoff)
                time.sleep(backoff)
                backoff *= 2  # Dobra o tempo de espera a cada nova falha (1s, 2s, 4s, 8s)
            else:
                logger.error("Máximo de tentativas atingido para %s", endpoint)
                raise RuntimeError(f"Falha ao acessar {endpoint} após {max_tentativas} tentativas")

        # Código defensivo caso saia do loop inesperadamente
        raise RuntimeError(f"Falha inesperada ao acessar {endpoint}")

    def get_movie_details(self, movie_id: int) -> dict[str, Any]:
        """Consulta os dados detalhados de um filme (sinopse, orçamento, receita, status, etc.)."""
        return self._fazer_requisicao(f"/movie/{movie_id}")

    def get_movie_credits(self, movie_id: int) -> dict[str, Any]:
        """Consulta os créditos completos do filme (elenco de atores e equipe técnica/direção)."""
        return self._fazer_requisicao(f"/movie/{movie_id}/credits")

    def get_movie_keywords(self, movie_id: int) -> dict[str, Any]:
        """Consulta as palavras-chave e temas associados ao filme."""
        return self._fazer_requisicao(f"/movie/{movie_id}/keywords")
