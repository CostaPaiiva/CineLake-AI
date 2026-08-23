# ADR-004: Pipeline de Ingestão de Dados com Idempotência

| Status   | Aceito     |
|----------|------------|
| Data     | 23-08-2026 |
| Área     | Ingestão de Dados / Banco de Dados |

## Contexto

O CineLake AI precisa processar dados do MovieLens de forma confiável, garantindo que as ingestões sejam idempotentes e permitam auditoria completa do processo. O sistema deve lidar com dados duplicados de forma segura e fornecer feedback sobre o resultado de cada execução.

## Problema

Como implementar um pipeline de ingestão que:
- Processa arquivos CSV grandes de forma eficiente
- Garante idempotência para evitar duplicatas
- Fornece status e métricas de cada execução
- Permite auditoria e diagnóstico de falhas
- Oferece uma interface de linha de comando para execução

## Decisão

Implementar um pipeline de ingestão com PostgreSQL utilizando estratégias de idempotência diferentes por tipo de dado e uma tabela de controle de batches para auditoria.

---

## Explicação Detalhada

### Tabela `ingestion_batch`

Armazena cada execução do pipeline com status, timestamps e contadores. Isso permite auditoria e diagnóstico de falhas.

### `_ingest_arquivo`

- Lê o CSV inteiro (para dataset pequeno; depois otimizaremos).
- Converte tipos básicos.
- Usa `insert(...).on_conflict_do_nothing()` para ratings e tags (ignora duplicatas).
- Usa `insert(...).on_conflict_do_update()` para movies e links (atualiza se já existir).
- Calcula quantos registros foram inseridos pela diferença de contagem antes/depois.

### Idempotência

- `movies` e `links` usam `ON CONFLICT DO UPDATE`, garantindo que os dados fiquem atualizados sem duplicar a chave.
- `ratings` e `tags` usam `ON CONFLICT DO NOTHING`, evitando duplicatas de chaves compostas.

### CLI

Adicionamos subcomandos ao `__main__.py` para facilitar a execução: `check-db` e `ingest-movielens`.

---

## Execução

### Na VPS (via SSH)

Ative o ambiente virtual e instale dependências (caso ainda não tenha feito):

```bash
cd ~/cinelake-ai
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

### Verificar conexão com o banco

```bash
python -m src check-db
```

### Executar a ingestão

```bash
python -m src ingest-movielens
```

### Verificar logs

```bash
docker logs cinelake-ai-postgres-1
```

---

## Alternativas Consideradas

### Processamento em lote com chunks

- **Vantagem**: Melhor para arquivos muito grandes
- **Desvantagem**: Complexidade adicional na gestão de estados parciais
- **Decisão**: Adiar para otimização futura, já que o dataset atual é pequeno

### Uso de ferramentas ETL externas

- **Vantagem**: Maiura robustez e escalabilidade
- **Desvantagem**: Complexidade de configuração e custo adicional
- **Decisão**: Manter implementação nativa para controle total no início

### Armazenamento de estado em arquivos

- **Vantagem**: Simplicidade inicial
- **Desvantagem**: Dificuldade de auditoria e concorrência
- **Decisão**: Usar banco de dados para controle de estado desde o início

## Prós e Contras (Compensações)

- **Idempotência robusta** evita problemas de dados duplicados
- **Auditoria completa** através da tabela `ingestion_batch`
- **Interface CLI simplificada** para operações comuns
- **Uso eficiente de recursos** com estratégias diferentes por tipo de dado
- **Complexidade adicional** na lógica de conflitos do banco
- **Necessidade de manter múltiplas estratégias** de inserção

## Consequências

### Positivas

- Dados consistentes e sem duplicatas
- Capacidade de reexecutar ingestões com segurança
- Visibilidade completa sobre o processo de ingestão
- Facilidade de diagnóstico de falhas
- Interface operacional simplificada

### Negativas

- Complexidade na manutenção das diferentes estratégias de idempotência
- Sobrecarga adicional de escrita na tabela de controle
- Necessidade de testes mais complexos para cobrir todos os cenários

## Considerações Futuras

- Implementar processamento em chunks para datasets maiores
- Adicionar suporte a compressão de arquivos
- Implementar retry lógico para falhas transitórias
- Adicionar monitoramento de métricas de ingestão
- Suportar múltiplos fontes de dados além do MovieLens