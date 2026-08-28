-- ==============================================================================
-- staging/stg_links.sql
-- Modelo dbt para padronização da tabela de identificadores externos (links)
-- ==============================================================================

-- CTE para ler os dados brutos da fonte raw.links configurada no schema.yml
with source as (
    select * from {{ source('raw', 'links') }}
),

-- CTE para padronização e seleção explícita das colunas de identificadores
renamed as (
    select
        movie_id,  -- ID interno do filme no MovieLens (chave primária/estrangeira)
        imdb_id,   -- Identificador único do filme no IMDb
        tmdb_id    -- Identificador único do filme no TMDb (The Movie Database)
    from source
)

-- Consulta final que será materializada como View no schema staging
select * from renamed