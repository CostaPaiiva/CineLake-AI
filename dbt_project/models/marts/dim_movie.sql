-- ==============================================================================
-- marts/dim_movie.sql
-- Tabela de Dimensão de Filmes (Camada Marts / Analytics)
-- ==============================================================================

-- CTE que consome o modelo intermediário limpo da camada staging
with stg_movies as (
    select * from {{ ref('stg_movies') }}
)

-- Seleção dos atributos descritivos do filme para o modelo dimensional
select
    movie_id,      -- Chave de negócio / identificador do filme
    title,         -- Título do filme
    genres,        -- Lista de gêneros associados ao filme
    release_year   -- Ano de lançamento extraído na camada staging
from stg_movies