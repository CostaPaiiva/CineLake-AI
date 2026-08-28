-- ==============================================================================
-- staging/stg_tags.sql
-- Modelo dbt para padronização e conversão temporal da tabela de tags de usuários
-- ==============================================================================

-- CTE para capturar os dados brutos da fonte raw.tags configurada no schema.yml
with source as (
    select * from {{ source('raw', 'tags') }}
),

-- CTE para padronização de nomes e conversão do timestamp Unix
renamed as (
    select
        user_id,   -- Identificador único do usuário que aplicou a tag
        movie_id,  -- Identificador único do filme tagueado
        tag,       -- Palavra-chave ou texto da tag aplicada
        ts,        -- Timestamp Unix bruto (em segundos)
        -- Converte o timestamp Unix numérico para timestamp legível com timezone
        to_timestamp(ts) as tagged_at
    from source
)

-- Consulta final materializada como View na camada staging
select * from renamed