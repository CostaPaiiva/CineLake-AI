-- ==============================================================================
-- marts/dim_date.sql
-- Tabela de Dimensão de Datas / Calendário (Camada Marts / Analytics)
-- ==============================================================================

-- CTE que gera uma série temporal contínua cobrindo todo o histórico do MovieLens até o futuro
with datas as (
    select
        -- Função do PostgreSQL que cria um intervalo diário de 1995 até 2026
        generate_series(
            date '1995-01-01',
            date '2026-12-31',
            interval '1 day'
        )::date as data
)

-- Projeção e decomposição das partes da data para facilitar análises e filtros temporais
select
    data as date_id,                         -- Chave primária da dimensão de data
    extract(year from data)::int as ano,     -- Ano numérico (ex: 2026)
    extract(month from data)::int as mes,    -- Mês numérico (1 a 12)
    extract(day from data)::int as dia,      -- Dia do mês numérico (1 a 31)
    to_char(data, 'YYYY-MM-DD') as data_iso, -- Data formatada no padrão ISO 8601
    to_char(data, 'Day') as dia_semana       -- Nome do dia da semana (ex: 'Friday')
from datas