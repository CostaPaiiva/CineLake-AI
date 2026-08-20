# ADR-002: RAG + MCP como Camada de IA

| Status   | Aceito     |
|----------|------------|
| Data     | 19-08-2026 |
| Área     | IA / Operações de Dados |

## Contexto

O CineLake AI precisa de uma camada inteligente que ajude engenheiros e analistas de dados a responder a perguntas sobre a plataforma, tais como:

- Qual pipeline falhou?
- Por que falhou?
- Qual é o esquema da tabela X?
- Qual é a linhagem da coluna Y?
- Qual modelo possui o melhor NDCG@10?

Esta camada deve ser segura, auditável e pronta para produção.

## Problema

Como fornecer acesso em linguagem natural à plataforma de dados sem permitir acesso arbitrário e não controlado aos sistemas subjacentes?

## Decisão

Construir um **assistente baseado em RAG** combinado com um **servidor MCP (Model Context Protocol)**.

- **RAG (Geração Aumentada de Recuperação)** indexa documentação, ADRs, runbooks, contratos de dados, documentação do dbt e outros conhecimentos semiestruturados. Ele recupera o contexto relevante para gerar respostas precisas.
- **MCP (Model Context Protocol)** expõe **ferramentas de apenas leitura** que consultam dados operacionais em tempo real (status de pipelines, atualização de dados, qualidade de dados, métricas do MLflow, etc.) através de uma interface controlada.

A API do assistente (`/ask`) poderá:

1. Recuperar documentos relevantes via RAG.
2. Chamar ferramentas MCP para obter dados em tempo real quando necessário.
3. Combinar ambos os contextos para produzir uma resposta confiável.

## Alternativas Consideradas

### Agente de IA puro com ferramentas diretas

- Exigiria um gerenciamento complexo de uso de ferramentas e permissões.
- Maior risco de acesso não autorizado ou ações prejudiciais.
- Mais difícil de avaliar e auditar.

### RAG puro sem acesso a dados em tempo real

- Não conseguiria responder a perguntas sobre o estado atual dos pipelines.
- Utilidade limitada para operações de dados.

### MCP independente sem RAG

- Não conseguiria aproveitar documentações e runbooks.
- Menos contexto para responder a perguntas complexas.

## Prós e Contras (Compensações)

- Requer a manutenção de dois subsistemas (índice RAG + servidor MCP).
- Complexidade adicional em avaliação e observabilidade.
- Potencial para conflitos de contexto entre os documentos recuperados e os dados em tempo real.

## Consequências

### Positivas

- Separação clara entre conhecimento estático (RAG) e estado dinâmico (MCP).
- Apenas leitura por padrão, reduzindo riscos de segurança.
- Mais fácil de auditar as chamadas de ferramentas e fontes de recuperação.
- Alta utilidade para operações de dados.

### Negativas

- Necessidade de sincronizar os documentos indexados com as mudanças na plataforma.
- Deve-se projetar a avaliação cuidadosamente para cobrir tanto a recuperação quanto o uso de ferramentas.

## Considerações Futuras

Se o assistente amadurecer, poderemos adicionar **ferramentas de escrita controladas** ao MCP com fluxos de aprovação humana.
