"""
Cliente para a API Open-Meteo (https://open-meteo.com).

Escolhida por ser gratuita, não exigir cadastro ou chave de API,
e ter limites de uso generosos — ideal para um projeto de portfólio
que qualquer pessoa pode clonar e rodar sem precisar configurar credenciais.
"""
import logging

import requests

from tracker.config import REQUEST_TIMEOUT_SECONDS, MAX_RETRIES
from tracker.retry import retry_with_backoff

logger = logging.getLogger("tracker")

API_URL = "https://api.open-meteo.com/v1/forecast"


@retry_with_backoff(max_retries=MAX_RETRIES, exceptions=(requests.RequestException,))
def _fetch_weather_data(latitude: float, longitude: float) -> dict:
    """Consulta a condição climática atual para uma coordenada."""
    response = requests.get(
        API_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def get_current_weather(city_name: str, latitude: float, longitude: float) -> dict | None:
    """
    Retorna um dicionário com a leitura atual de clima para a cidade,
    ou None se a chamada falhar após todas as tentativas.
    """
    try:
        data = _fetch_weather_data(latitude, longitude)
    except requests.RequestException as exc:
        logger.error("Não foi possível obter o clima de %s: %s", city_name, exc)
        return None

    current = data.get("current_weather")
    if not current:
        logger.warning("Resposta da API sem dados de clima atual para %s", city_name)
        return None

    return {
        "city": city_name,
        "temperature_c": current.get("temperature"),
        "wind_speed_kmh": current.get("windspeed"),
        "weather_code": current.get("weathercode"),
    }


def collect_weather_for_cities(cities: list[tuple[str, float, float]]) -> list[dict]:
    """Coleta o clima atual para todas as cidades configuradas."""
    readings = []
    for city_name, lat, lon in cities:
        logger.info("Consultando clima de %s...", city_name)
        reading = get_current_weather(city_name, lat, lon)
        if reading:
            readings.append(reading)
            logger.info("  %s: %.1f°C", city_name, reading["temperature_c"])
    return readings
