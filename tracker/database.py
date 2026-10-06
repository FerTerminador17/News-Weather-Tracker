"""
Camada de acesso ao banco de dados (SQLite).

Usamos SQLite por ser leve, não precisar de servidor separado, e já
vir embutido no Python — ótimo para um projeto que roda localmente
ou em automações agendadas.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL UNIQUE,
    published TEXT,
    collected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    temperature_c REAL NOT NULL,
    wind_speed_kmh REAL,
    weather_code INTEGER,
    collected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_news_source ON news(source);
CREATE INDEX IF NOT EXISTS idx_weather_city ON weather(city);
"""


@contextmanager
def get_connection(db_path: Path):
    """Context manager que garante que a conexão é sempre fechada corretamente."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path):
    """Cria as tabelas do banco, caso ainda não existam."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def save_news_items(db_path: Path, items: list[dict]) -> int:
    """
    Salva itens de notícia no banco, ignorando duplicados (mesmo link).
    Retorna a quantidade de itens realmente inseridos (novos).
    """
    inserted = 0
    with get_connection(db_path) as conn:
        for item in items:
            try:
                conn.execute(
                    "INSERT INTO news (source, title, link, published, collected_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        item["source"],
                        item["title"],
                        item["link"],
                        item.get("published"),
                        datetime.now().isoformat(),
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                # Link já existe no banco (notícia já coletada antes) — ignora
                continue
    return inserted


def save_weather_reading(db_path: Path, reading: dict):
    """Salva uma leitura de clima no banco."""
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO weather (city, temperature_c, wind_speed_kmh, weather_code, collected_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                reading["city"],
                reading["temperature_c"],
                reading.get("wind_speed_kmh"),
                reading.get("weather_code"),
                datetime.now().isoformat(),
            ),
        )


def get_news_summary(db_path: Path, days: int = 7) -> list[sqlite3.Row]:
    """Retorna a contagem de notícias por fonte nos últimos N dias."""
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT source, COUNT(*) as total FROM news "
            "WHERE collected_at >= datetime('now', ?) "
            "GROUP BY source ORDER BY total DESC",
            (f"-{days} days",),
        )
        return cursor.fetchall()


def get_latest_weather(db_path: Path) -> list[sqlite3.Row]:
    """Retorna a leitura de clima mais recente de cada cidade."""
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT city, temperature_c, wind_speed_kmh, collected_at FROM weather "
            "WHERE id IN (SELECT MAX(id) FROM weather GROUP BY city) "
            "ORDER BY city"
        )
        return cursor.fetchall()


def fetch_all_news(db_path: Path) -> list[sqlite3.Row]:
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT * FROM news ORDER BY collected_at DESC")
        return cursor.fetchall()


def fetch_all_weather(db_path: Path) -> list[sqlite3.Row]:
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT * FROM weather ORDER BY collected_at DESC")
        return cursor.fetchall()
