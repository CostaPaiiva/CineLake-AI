# Agent Evaluation — CineLake AI

Este diretório contém o dataset e os resultados da avaliação do assistente RAG + MCP.

## Métricas

- **Tool Selection Accuracy**: fração de perguntas em que a ferramenta MCP correta foi escolhida.
- **Document Hit Rate**: fração de perguntas em que ao menos um documento esperado foi recuperado.
- **Document Recall**: média da fração de documentos esperados recuperados.
- **Latência média**: tempo médio de resposta da API.

## Como executar

```bash
python -m cinelake evaluate-agent --dataset data/agent_evaluation/eval_dataset.json --top-k 5
```

Os resultados ficam em `docs/agent_evaluation/resultados.json` e são registrados no MLflow (experimento `agent_evaluation`).

## Como interpretar

- **Tool Selection Accuracy ideal**: > 0.8.
- **Document Hit Rate ideal**: > 0.6.
- **Document Recall ideal**: > 0.4.
- **Latência média ideal**: < 2000 ms.

## Como melhorar

1. Ajustar o mapeamento de intenção em `_detectar_ferramenta`.
2. Aumentar o `top_k` no endpoint.
3. Melhorar a indexação de documentos RAG.
4. Revisar o dataset (perguntas e ferramentas esperadas).
