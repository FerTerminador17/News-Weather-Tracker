"""Testes do cliente da API de clima (Open-Meteo), usando mocks de requests."""
from unittest.mock import patch, MagicMock

import requests

from tracker.weather_client import get_current_weather, collect_weather_for_cities

SAMPLE_WEATHER_RESPONSE = {
    "latitude": -23.5,
    "longitude": -46.6,
    "current_weather": {
        "temperature": 24.3,
        "windspeed": 12.1,
        "weathercode": 2,
        "time": "2026-01-01T10:00",
    },
}


@patch("tracker.weather_client.requests.get")
def test_get_current_weather_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_WEATHER_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    reading = get_current_weather("São Paulo", -23.55, -46.63)

    assert reading is not None
    assert reading["city"] == "São Paulo"
    assert reading["temperature_c"] == 24.3
    assert reading["wind_speed_kmh"] == 12.1


@patch("tracker.weather_client.requests.get")
def test_get_current_weather_missing_data_returns_none(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"latitude": -23.5, "longitude": -46.6}  # sem current_weather
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    reading = get_current_weather("São Paulo", -23.55, -46.63)

    assert reading is None


@patch("tracker.weather_client.requests.get")
@patch("tracker.retry.time.sleep")
def test_get_current_weather_returns_none_on_persistent_failure(mock_sleep, mock_get):
    mock_get.side_effect = requests.Timeout("Timeout simulado")

    reading = get_current_weather("Cidade Instável", 0, 0)

    assert reading is None
    assert mock_get.call_count == 3


@patch("tracker.weather_client.get_current_weather")
def test_collect_weather_for_cities_skips_failed_cities(mock_get_weather):
    # Primeira cidade retorna dado válido, segunda falha (retorna None)
    mock_get_weather.side_effect = [
        {"city": "São Paulo", "temperature_c": 25.0, "wind_speed_kmh": 10, "weather_code": 1},
        None,
    ]

    cities = [("São Paulo", -23.55, -46.63), ("Cidade Fantasma", 0, 0)]
    readings = collect_weather_for_cities(cities)

    assert len(readings) == 1
    assert readings[0]["city"] == "São Paulo"
