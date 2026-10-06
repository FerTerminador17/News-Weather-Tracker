"""
Configurações centrais: fontes de notícias (RSS) e cidades monitoradas.

Para adicionar uma nova fonte de notícia, basta incluir uma tupla
(nome_da_fonte, url_do_feed_rss) em NEWS_FEEDS.

Para adicionar uma cidade, inclua (nome, latitude, longitude) em CITIES.
As coordenadas são usadas na API Open-Meteo (gratuita, sem necessidade de chave).
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "tracker.db"
DATABASE_PATH.parent.mkdir(exist_ok=True)

# Feeds RSS públicos de portais de notícias brasileiros
NEWS_FEEDS: list[tuple[str, str]] = [
    ("G1", "https://g1.globo.com/rss/g1/"),
    ("CNN Brasil", "https://www.cnnbrasil.com.br/feed/"),
    ("BBC Brasil", "https://www.bbc.com/portuguese/index.xml"),
]

# Cidades monitoradas: nome, latitude, longitude
CITIES: list[tuple[str, float, float]] = [
    ("São Paulo", -23.5505, -46.6333),
    ("Rio de Janeiro", -22.9068, -43.1729),
    ("Belo Horizonte", -19.9167, -43.9345),
]

REQUEST_TIMEOUT_SECONDS = 10
MAX_RETRIES = 3
