-- ==============================================================================
-- staging/stg_ratings.sql
-- Modelo dbt para padronização e conversão de tipos da tabela de avaliações (ratings)
-- ==============================================================================

-- CTE para capturar os dados brutos da fonte raw.ratings definida no schema.yml
with source as (
    select * from {{ source('raw', 'ratings') }}
),

-- CTE para padronização, renomeação e conversão temporal
renamed as (
    select
        user_id,
        movie_id,
        rating,
        ts,
        -- Converte o timestamp Unix numérico (segundos desde a Unix Epoch 1970-01-01)
        -- para o tipo data/hora padrão com fuso horário (timestamp with time zone)
        to_timestamp(ts) as rated_at
    from source
)

-- Retorna a consulta final que será materializada como uma View no schema staging
select * from renamed