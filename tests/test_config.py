"""Testes para as configurações da aplicação."""

from cinelake.config import Settings


def test_settings_default_environment(monkeypatch) -> None:
    """Usa padrões de desenvolvimento quando variáveis de ambiente estão ausentes."""
    # Garante que as variáveis de ambiente não estejam definidas para o teste
    monkeypatch.delenv("CINELAKE_ENV", raising=False)
    monkeypatch.delenv("CINELAKE_LOG_LEVEL", raising=False)

    settings = Settings.from_env()

    # Verifica se os valores padrão foram aplicados corretamente
    assert settings.environment == "development"
    assert settings.log_level == "INFO"


def test_settings_override_environment(monkeypatch) -> None:
    """As configurações devem respeitar os valores definidos nas variáveis de ambiente."""
    # Define as variáveis de ambiente de teste
    monkeypatch.setenv("CINELAKE_ENV", "production")
    monkeypatch.setenv("CINELAKE_LOG_LEVEL", "DEBUG")

    settings = Settings.from_env()

    # Verifica se os valores foram sobrescritos corretamente pelas variáveis configuradas
    assert settings.environment == "production"
    assert settings.log_level == "DEBUG"
