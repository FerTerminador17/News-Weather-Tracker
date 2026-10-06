"""
Interface de linha de comando do News & Weather Tracker.

Comandos disponíveis:
    collect-news       Coleta notícias dos feeds RSS configurados
    collect-weather     Coleta o clima atual das cidades configuradas
    report              Mostra um resumo dos dados coletados
    export-csv           Exporta os dados para arquivos CSV
"""
import argparse
import logging
import sys
from pathlib import Path

from tracker.config import DATABASE_PATH, NEWS_FEEDS, CITIES
from tracker.database import (
    init_db, save_news_items, save_weather_reading,
    get_news_summary, get_latest_weather,
)
from tracker.news_scraper import collect_all_feeds
from tracker.weather_client import collect_weather_for_cities
from tracker.export import export_news_to_csv, export_weather_to_csv

logger = logging.getLogger("tracker")


def cmd_collect_news(args) -> int:
    items = collect_all_feeds(NEWS_FEEDS)
    inserted = save_news_items(DATABASE_PATH, items)
    print(f"\n{len(items)} notícia(s) encontrada(s), {inserted} nova(s) salva(s) no banco.")
    return 0


def cmd_collect_weather(args) -> int:
    readings = collect_weather_for_cities(CITIES)
    for reading in readings:
        save_weather_reading(DATABASE_PATH, reading)
    print(f"\n{len(readings)} leitura(s) de clima salva(s) no banco.")
    return 0


def cmd_report(args) -> int:
    print(f"\n=== Resumo de notícias (últimos {args.days} dias) ===")
    news_summary = get_news_summary(DATABASE_PATH, days=args.days)
    if not news_summary:
        print("Nenhuma notícia coletada ainda nesse período.")
    for row in news_summary:
        print(f"  {row['source']}: {row['total']} notícia(s)")

    print("\n=== Clima mais recente por cidade ===")
    weather = get_latest_weather(DATABASE_PATH)
    if not weather:
        print("Nenhum dado de clima coletado ainda.")
    for row in weather:
        print(f"  {row['city']}: {row['temperature_c']}°C (vento: {row['wind_speed_kmh']} km/h) em {row['collected_at']}")

    return 0


def cmd_export_csv(args) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    news_path = output_dir / "news.csv"
    weather_path = output_dir / "weather.csv"

    news_count = export_news_to_csv(DATABASE_PATH, news_path)
    weather_count = export_weather_to_csv(DATABASE_PATH, weather_path)

    print(f"\n{news_count} notícia(s) exportada(s) para {news_path}")
    print(f"{weather_count} leitura(s) de clima exportada(s) para {weather_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tracker",
        description="Coleta notícias (RSS) e clima (Open-Meteo), salva em SQLite e gera relatórios.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_news = subparsers.add_parser("collect-news", help="Coleta notícias dos feeds RSS configurados")
    p_news.set_defaults(func=cmd_collect_news)

    p_weather = subparsers.add_parser("collect-weather", help="Coleta o clima atual das cidades configuradas")
    p_weather.set_defaults(func=cmd_collect_weather)

    p_report = subparsers.add_parser("report", help="Mostra um resumo dos dados coletados")
    p_report.add_argument("--days", type=int, default=7, help="Janela de dias para o resumo de notícias (padrão: 7)")
    p_report.set_defaults(func=cmd_report)

    p_export = subparsers.add_parser("export-csv", help="Exporta os dados coletados para arquivos CSV")
    p_export.add_argument("--output-dir", type=str, default="exports", help="Pasta de destino dos CSVs (padrão: exports/)")
    p_export.set_defaults(func=cmd_export_csv)

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    init_db(DATABASE_PATH)

    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
