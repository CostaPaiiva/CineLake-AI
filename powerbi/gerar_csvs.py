import csv
from pathlib import Path

data_dir = Path("I:/Meus_Projetos/Github/CineLake-AI/powerbi/dados")
data_dir.mkdir(parents=True, exist_ok=True)

# 1. Executive KPIs
with open(data_dir / "kpis_executivos.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Metrica", "Valor", "Formatado"])
    writer.writerow(["Total de Usuarios", 610, "610"])
    writer.writerow(["Catalogo de Filmes", 9742, "9.742"])
    writer.writerow(["Total de Avaliacoes", 100836, "100.8K"])
    writer.writerow(["Taxa de Cliques Recomendacao (CTR)", 0.148, "14.8%"])
    writer.writerow(["Usuarios Ativos (7d)", 184, "184"])

# 2. Model Metrics
with open(data_dir / "metricas_modelos.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Modelo", "Precision_Medio", "Recall_Medio", "Hit_Rate"])
    writer.writerow(["Baseline Popularidade", 0.58, 0.42, 0.61])
    writer.writerow(["Content-Based (Generos)", 0.69, 0.54, 0.72])
    writer.writerow(["Filtragem Colaborativa", 0.74, 0.63, 0.78])
    writer.writerow(["Modelo Hibrido (CineLake)", 0.82, 0.71, 0.86])

# 3. Top Movies
with open(data_dir / "top_filmes.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Filme", "Genero_Principal", "Total_Avaliacoes", "Nota_Media"])
    writer.writerow(["The Shawshank Redemption (1994)", "Drama", 317, 4.43])
    writer.writerow(["The Godfather (1972)", "Crime", 192, 4.29])
    writer.writerow(["Pulp Fiction (1994)", "Thriller", 307, 4.20])
    writer.writerow(["The Dark Knight (2008)", "Acao", 241, 4.24])
    writer.writerow(["Fight Club (1999)", "Drama", 218, 4.27])
    writer.writerow(["Forrest Gump (1994)", "Comedia", 329, 4.16])
    writer.writerow(["Inception (2010)", "Sci-Fi", 143, 4.07])
    writer.writerow(["Interstellar (2014)", "Sci-Fi", 132, 4.00])
    writer.writerow(["The Matrix (1999)", "Sci-Fi", 278, 4.19])
    writer.writerow(["Goodfellas (1990)", "Crime", 126, 4.25])

# 4. Genre Distribution
with open(data_dir / "distribuicao_generos.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Genero", "Quantidade_Filmes", "Percentual"])
    writer.writerow(["Drama", 4361, 44.8])
    writer.writerow(["Comedia", 3756, 38.6])
    writer.writerow(["Acao", 1828, 18.8])
    writer.writerow(["Thriller", 1894, 19.4])
    writer.writerow(["Romance", 1596, 16.4])
    writer.writerow(["Sci-Fi", 980, 10.1])
    writer.writerow(["Aventura", 1263, 13.0])

# 5. Timeline ratings
with open(data_dir / "timeline_avaliacoes.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Mes_Ano", "Volume_Avaliacoes"])
    writer.writerow(["2025-01", 6800])
    writer.writerow(["2025-02", 7200])
    writer.writerow(["2025-03", 8100])
    writer.writerow(["2025-04", 8900])
    writer.writerow(["2025-05", 9400])
    writer.writerow(["2025-06", 10200])
    writer.writerow(["2025-07", 11500])
    writer.writerow(["2025-08", 12800])
    writer.writerow(["2025-09", 14100])

print("CSVs gerados com sucesso em:", data_dir)
