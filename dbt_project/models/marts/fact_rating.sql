-- ==============================================================================
-- marts/fact_rating.sql
-- Tabela Fato de Avaliações (Camada Marts / Analytics) - Star Schema
-- ==============================================================================

-- CTE para capturar os eventos limpos de avaliações da camada staging
with stg_ratings as (
    select * from {{ ref('stg_ratings') }}
),

-- CTE referenciando a dimensão de filmes
dim_movie as (
    select * from {{ ref('dim_movie') }}
),

-- CTE referenciando a dimensão de usuários
dim_user as (
    select * from {{ ref('dim_user') }}
)

-- Construção da tabela fato com chaves estrangeiras para as dimensões e métricas
select
    r.user_id,                          -- Chave estrangeira para dim_user
    r.movie_id,                         -- Chave estrangeira para dim_movie
    r.rating,                           -- Métrica/Fato: nota atribuída (0.5 a 5.0)
    r.rated_at,                         -- Timestamp exato da avaliação
    d.date_id                           -- Chave estrangeira para dim_date
from stg_ratings r
-- Junção para garantir integridade referencial com os filmes
left join dim_movie m on r.movie_id = m.movie_id
-- Junção para garantir integridade referencial com os usuários
left join dim_user u on r.user_id = u.user_id
-- Converte o timestamp para date e associa à dimensão de datas/calendário
left join {{ ref('dim_date') }} d on d.date_id = r.rated_at::date