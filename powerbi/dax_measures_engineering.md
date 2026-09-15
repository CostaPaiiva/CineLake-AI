# Medidas DAX — CineLake AI

Medidas para um modelo semântico em estrela, com `fact_rating` como fato central e `dim_movie`, `dim_user` e `dim_date` como dimensões. Evite arrastar colunas numéricas diretamente para os visuais quando existir uma medida semântica equivalente.

## KPIs do catálogo

```dax
Total Filmes =
DISTINCTCOUNT('dim_movie'[movie_id])

Total Usuarios =
DISTINCTCOUNT('fact_rating'[user_id])

Total Avaliacoes =
COUNTROWS('fact_rating')

Nota Media =
AVERAGE('fact_rating'[rating])

Avaliacoes por Filme =
DIVIDE([Total Avaliacoes], [Total Filmes])

Filmes Avaliados =
DISTINCTCOUNT('fact_rating'[movie_id])

Cobertura do Catalogo % =
DIVIDE([Filmes Avaliados], [Total Filmes])
```

> No gráfico de notas por filme, use `Nota Media` (média), nunca `SUM(dim_movie[Nota_Media])`. A soma de médias produz um indicador sem significado analítico.

## Performance dos modelos de recomendação

Use estas medidas sobre `mart_powerbi_recommendation_analytics`:

```dax
Precision Media % =
AVERAGE('mart_powerbi_recommendation_analytics'[precision_medio])

Recall Medio % =
AVERAGE('mart_powerbi_recommendation_analytics'[recall_medio])

Hit Rate % =
AVERAGE('mart_powerbi_recommendation_analytics'[hit_rate])

Modelo Top Hit Rate =
VAR MelhorModelo =
    TOPN(
        1,
        ALL('mart_powerbi_recommendation_analytics'[model_name]),
        [Hit Rate %], DESC
    )
RETURN
    CONCATENATEX(MelhorModelo, 'mart_powerbi_recommendation_analytics'[model_name], ", ")
```

## Monitoramento de engenharia de dados

Use estas medidas sobre `mart_powerbi_data_engineering_monitoring` e crie uma página separada chamada **Data Engineering**:

```dax
Pipelines =
DISTINCTCOUNT('mart_powerbi_data_engineering_monitoring'[source])

Pipelines com Falha =
CALCULATE(
    DISTINCTCOUNT('mart_powerbi_data_engineering_monitoring'[source]),
    'mart_powerbi_data_engineering_monitoring'[status] = "failed"
)

Linhas Processadas =
SUM('mart_powerbi_data_engineering_monitoring'[rows_processed])

Linhas Inseridas =
SUM('mart_powerbi_data_engineering_monitoring'[rows_inserted])

Linhas Atualizadas =
SUM('mart_powerbi_data_engineering_monitoring'[rows_updated])

Freshness Media Horas =
AVERAGE('mart_powerbi_data_engineering_monitoring'[freshness_horas])

Duracao Media =
AVERAGE('mart_powerbi_data_engineering_monitoring'[duracao])
```

### Formatação recomendada

- Percentuais: formato `0.0%` para precisão, recall, hit rate, CTR e cobertura.
- Volume: separador de milhar, sem abreviação automática nos KPIs operacionais.
- Duração: `hh:mm:ss`.
- Freshness: `0.0 "h"` e semáforo com verde até 24h, amarelo até 48h e vermelho acima disso.

## Tema oficial

No Power BI Desktop: **Exibir → Temas → Procurar temas** e selecione:

`I:\Meus_Projetos\Github\CineLake-AI\powerbi\cinelake_theme.json`

Depois de atualizar as medidas, valide os visuais com **Exibir → Mostrar como tabela** e confirme que os totais respondem aos filtros de `dim_date` e `dim_movie`.
