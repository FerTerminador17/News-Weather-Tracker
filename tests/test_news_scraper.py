"""
Testes do coletor de notícias (RSS).

Usamos unittest.mock para simular as respostas HTTP, assim os testes
rodam rápido e de forma determinística, sem depender de internet ou
dos feeds reais estarem no ar.
"""
from unittest.mock import patch, MagicMock

import pytest
import requests

from tracker.news_scraper import parse_feed, collect_news_from_feed, collect_all_feeds

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Portal de Teste</title>
    <item>
      <title>Primeira notícia de teste</title>
      <link>https://exemplo.com/noticia-1</link>
      <pubDate>Mon, 01 Jan 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Segunda notícia de teste</title>
      <link>https://exemplo.com/noticia-2</link>
      <pubDate>Mon, 01 Jan 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode("utf-8")

MALFORMED_XML = b"<rss><channel><item><title>sem fechamento"


def test_parse_feed_extracts_items_correctly():
    items = parse_feed(SAMPLE_RSS, source_name="Portal de Teste")

    assert len(items) == 2
    assert items[0]["title"] == "Primeira notícia de teste"
    assert items[0]["link"] == "https://exemplo.com/noticia-1"
    assert items[0]["source"] == "Portal de Teste"
    assert items[1]["title"] == "Segunda notícia de teste"


def test_parse_feed_handles_malformed_xml_gracefully():
    items = parse_feed(MALFORMED_XML, source_name="Portal Quebrado")
    assert items == []  # não deve lançar exceção, só retornar lista vazia


def test_parse_feed_skips_items_without_title_or_link():
    xml_incompleto = """<rss><channel>
        <item><title>Só tem título</title></item>
        <item><link>https://exemplo.com/sem-titulo</link></item>
    </channel></rss>""".encode("utf-8")

    items = parse_feed(xml_incompleto, source_name="Teste")
    assert items == []


@patch("tracker.news_scraper.requests.get")
def test_collect_news_from_feed_success(mock_get):
    mock_response = MagicMock()
    mock_response.content = SAMPLE_RSS
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    items = collect_news_from_feed("Portal de Teste", "https://exemplo.com/rss")

    assert len(items) == 2
    mock_get.assert_called_once()


@patch("tracker.news_scraper.requests.get")
@patch("tracker.retry.time.sleep")  # evita esperar de verdade entre retries
def test_collect_news_from_feed_returns_empty_list_on_persistent_failure(mock_sleep, mock_get):
    mock_get.side_effect = requests.ConnectionError("Falha simulada de conexão")

    items = collect_news_from_feed("Portal Instável", "https://exemplo.com/rss")

    assert items == []
    assert mock_get.call_count == 3  # respeitou o número de tentativas configurado


@patch("tracker.news_scraper.collect_news_from_feed")
def test_collect_all_feeds_aggregates_results_from_multiple_sources(mock_collect):
    mock_collect.side_effect = [
        [{"source": "G1", "title": "A", "link": "http://g1.com/a", "published": None}],
        [{"source": "CNN", "title": "B", "link": "http://cnn.com/b", "published": None}],
    ]

    feeds = [("G1", "http://g1.com/rss"), ("CNN", "http://cnn.com/rss")]
    items = collect_all_feeds(feeds)

    assert len(items) == 2
    assert items[0]["source"] == "G1"
    assert items[1]["source"] == "CNN"
