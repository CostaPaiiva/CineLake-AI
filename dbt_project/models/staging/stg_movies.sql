-- ==============================================================================
-- staging/stg_movies.sql
-- Modelo dbt para padronização e limpeza da tabela bruta de filmes (movies)
-- ==============================================================================

-- CTE para capturar os dados da fonte raw.movies configurada no schema.yml
with source as (
    select * from {{ source('raw', 'movies') }}
),

-- CTE para padronização, limpeza e engenharia de atributos (feature extraction)
renamed as (
    select
        movie_id,
        title,
        genres,
        -- Expressão Regular (Regex) para extrair os 4 dígitos do ano contidos entre parênteses
        -- Exemplo: "Toy Story (1995)" -> "1995"
        substring(title from '\((\d{4})\)') as release_year
    from source
)

-- Seleção final do modelo staging
select * from renamed