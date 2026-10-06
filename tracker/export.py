"""Exportação dos dados coletados para arquivos CSV."""
import csv
from pathlib import Path

from tracker.database import fetch_all_news, fetch_all_weather


def export_news_to_csv(db_path: Path, output_path: Path) -> int:
    """Exporta todas as notícias coletadas para um CSV. Retorna a quantidade de linhas."""
    rows = fetch_all_news(db_path)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "source", "title", "link", "published", "collected_at"])
        for row in rows:
            writer.writerow([row["id"], row["source"], row["title"], row["link"], row["published"], row["collected_at"]])
    return len(rows)


def export_weather_to_csv(db_path: Path, output_path: Path) -> int:
    """Exporta todas as leituras de clima para um CSV. Retorna a quantidade de linhas."""
    rows = fetch_all_weather(db_path)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "city", "temperature_c", "wind_speed_kmh", "weather_code", "collected_at"])
        for row in rows:
            writer.writerow([
                row["id"], row["city"], row["temperature_c"],
                row["wind_speed_kmh"], row["weather_code"], row["collected_at"],
            ])
    return len(rows)
