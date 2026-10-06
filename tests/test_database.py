"""Testes da camada de banco de dados, usando um banco SQLite temporário por teste."""
from tracker.database import (
    init_db, save_news_items, save_weather_reading,
    get_news_summary, get_latest_weather, fetch_all_news,
)


def test_init_db_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    assert db_path.exists()


def test_save_news_items_inserts_new_items(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    items = [
        {"source": "G1", "title": "Notícia 1", "link": "http://g1.com/1", "published": "2026-01-01"},
        {"source": "G1", "title": "Notícia 2", "link": "http://g1.com/2", "published": "2026-01-01"},
    ]
    inserted = save_news_items(db_path, items)

    assert inserted == 2
    assert len(fetch_all_news(db_path)) == 2


def test_save_news_items_ignores_duplicates(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    item = {"source": "G1", "title": "Notícia 1", "link": "http://g1.com/1", "published": "2026-01-01"}

    first_insert = save_news_items(db_path, [item])
    second_insert = save_news_items(db_path, [item])  # mesmo link de novo

    assert first_insert == 1
    assert second_insert == 0  # ignorado por já existir
    assert len(fetch_all_news(db_path)) == 1


def test_save_weather_reading(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    reading = {"city": "São Paulo", "temperature_c": 25.5, "wind_speed_kmh": 10.2, "weather_code": 1}
    save_weather_reading(db_path, reading)

    latest = get_latest_weather(db_path)
    assert len(latest) == 1
    assert latest[0]["city"] == "São Paulo"
    assert latest[0]["temperature_c"] == 25.5


def test_get_latest_weather_returns_most_recent_per_city(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    save_weather_reading(db_path, {"city": "São Paulo", "temperature_c": 20.0, "wind_speed_kmh": 5, "weather_code": 0})
    save_weather_reading(db_path, {"city": "São Paulo", "temperature_c": 22.0, "wind_speed_kmh": 5, "weather_code": 0})

    latest = get_latest_weather(db_path)

    assert len(latest) == 1  # só uma linha por cidade
    assert latest[0]["temperature_c"] == 22.0  # a mais recente


def test_get_news_summary_groups_by_source(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    items = [
        {"source": "G1", "title": "A", "link": "http://g1.com/a", "published": None},
        {"source": "G1", "title": "B", "link": "http://g1.com/b", "published": None},
        {"source": "CNN Brasil", "title": "C", "link": "http://cnn.com/c", "published": None},
    ]
    save_news_items(db_path, items)

    summary = get_news_summary(db_path, days=7)
    summary_dict = {row["source"]: row["total"] for row in summary}

    assert summary_dict == {"G1": 2, "CNN Brasil": 1}
