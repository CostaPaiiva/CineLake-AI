# Gerenciamento de Credenciais

## Boas práticas

- Nunca versionar `.env`.
- Usar senhas longas (>= 32 caracteres).
- Rotacionar credenciais periodicamente.
- Usar usuários distintos por serviço.
- Em produção, usar Docker secrets ou um cofre (Vault, AWS Secrets Manager).

## Geração de senhas

```bash
openssl rand -base64 32
```

## Variáveis sensíveis

- `POSTGRES_PASSWORD`
- `MINIO_SECRET_KEY`
- `GRAFANA_ADMIN_PASSWORD`
- `MCP_TOKEN`
- `TMDB_API_KEY`

## Rotação

1. Gere nova senha.
2. Atualize o `.env`.
3. Reinicie o serviço afetado.
4. Revogue a senha antiga no provedor.
