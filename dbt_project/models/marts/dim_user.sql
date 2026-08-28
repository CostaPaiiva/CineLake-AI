-- ==============================================================================
-- marts/dim_user.sql
-- Tabela de Dimensão de Usuários (Camada Marts / Analytics)
-- ==============================================================================

-- CTE para extrair todos os identificadores únicos de usuários que avaliaram filmes
with usuarios as (
    select distinct user_id
    from {{ ref('stg_ratings') }}
)

-- Construção da dimensão de usuários para composição do modelo dimensional (Star Schema)
select
    user_id,
    -- Dimensão mínima: campos demográficos padronizados como placeholders,
    -- já que o dataset MovieLens não fornece atributos de perfil dos usuários
    'desconhecido' as genero,
    null as idade
from usuarios