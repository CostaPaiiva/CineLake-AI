# 📊 Medidas DAX Prontas — CineLake AI

Copie e cole as medidas abaixo no Power BI para formatar automaticamente seus números e KPIs.

---

### 1. Total de Filmes no Catálogo
```dax
Total Filmes = 
COUNTROWS('dim_movie')
```

### 2. Total de Usuários Avaliadores
```dax
Total Usuarios = 
DISTINCTCOUNT('fact_rating'[user_id])
```

### 3. Total de Avaliações Registradas (Formatado em K)
```dax
Total Avaliacoes = 
COUNTROWS('fact_rating')
```

### 4. Média Geral de Notas (com estrelas)
```dax
Nota Media = 
AVERAGE('fact_rating'[rating])
```

### 5. Hit Rate Médio dos Modelos de IA (%)
```dax
Hit Rate % = 
AVERAGE('mart_powerbi_recommendation_analytics'[hit_rate])
```

### 6. CTR de Recomendações (Taxa de Clique %)
```dax
CTR Recomendacoes % = 
AVERAGE('mart_powerbi_executive_overview'[ctr_recomendacao])
```

---

## 🎨 Como Aplicar o Tema Oficial Dark Mode:

1. Abra o **Power BI Desktop**.
2. No menu superior, clique na aba **Exibir**.
3. Na seção de **Temas**, clique na setinha para baixo e selecione **Procurar temas**.
4. Selecione o arquivo:
   `I:\Meus_Projetos\Github\CineLake-AI\powerbi\cinelake_theme.json`
5. Pronto! O fundo ficará preto/azul profundo `#0B0F19`, os cartões ficarão arredondados e a paleta neon será aplicada automaticamente.
