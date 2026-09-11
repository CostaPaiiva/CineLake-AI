-- ==============================================================================
-- marts/fact_rating.sql
-- Tabela Fato de Avaliações (Camada Marts / Analytics) - Star Schema
-- ==============================================================================

-- CTE para capturar os eventos limpos de avaliações da camada staging
with stg_ratings as (
    select * from {{ ref('stg_ratings') }}
)

-- Construção da tabela fato com chaves estrangeiras para as dimensões e métricas
select
    r.user_id,                          -- Chave estrangeira para dim_user
    r.movie_id,                         -- Chave estrangeira para dim_movie
    r.rating,                           -- Métrica/Fato: nota atribuída (0.5 a 5.0)
    r.rated_at,                         -- Timestamp exato da avaliação
    d.date_id                           -- Chave estrangeira para dim_date
from stg_ratings as r
-- Converte o timestamp para date e associa à dimensão de datas/calendário
left join {{ ref('dim_date') }} as d on d.date_id = r.rated_at::date
