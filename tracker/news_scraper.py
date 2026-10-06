"""
Coletor de notícias a partir de feeds RSS.

Por que RSS e não scraping direto de HTML?
- RSS é um formato público, feito justamente para ser consumido por
  programas automatizados — diferente de "raspar" o HTML de um site,
  que pode violar termos de uso e quebra a cada mudança de layout.
- O XML do RSS é estruturado e estável, então o parsing é muito mais
  confiável.
"""
import logging
import xml.etree.ElementTree as ET

import requests

from tracker.config import REQUEST_TIMEOUT_SECONDS, MAX_RETRIES
from tracker.retry import retry_with_backoff

logger = logging.getLogger("tracker")


@retry_with_backoff(max_retries=MAX_RETRIES, exceptions=(requests.RequestException,))
def _fetch_feed_content(url: str) -> bytes:
    """Baixa o conteúdo bruto (XML) de um feed RSS."""
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "news-weather-tracker/1.0"},
    )
    response.raise_for_status()
    return response.content


def parse_feed(xml_content: bytes, source_name: str) -> list[dict]:
    """
    Converte o XML de um feed RSS 2.0 em uma lista de dicionários
    {source, title, link, published}.
    """
    items = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        logger.error("Falha ao parsear XML do feed %s: %s", source_name, exc)
        return items

    # RSS 2.0: <rss><channel><item>...</item></channel></rss>
    for item in root.findall(".//item"):
        title = _get_text(item, "title")
        link = _get_text(item, "link")
        published = _get_text(item, "pubDate")

        if title and link:
            items.append({
                "source": source_name,
                "title": title.strip(),
                "link": link.strip(),
                "published": published,
            })

    return items


def _get_text(item: ET.Element, tag: str) -> str | None:
    element = item.find(tag)
    return element.text if element is not None else None


def collect_news_from_feed(source_name: str, feed_url: str) -> list[dict]:
    """
    Busca e parseia um feed RSS completo.
    Retorna lista vazia (sem levantar exceção) se o feed falhar após
    todas as tentativas de retry, para não travar a coleta de outras fontes.
    """
    try:
        content = _fetch_feed_content(feed_url)
    except requests.RequestException as exc:
        logger.error("Não foi possível coletar o feed de %s: %s", source_name, exc)
        return []

    return parse_feed(content, source_name)


def collect_all_feeds(feeds: list[tuple[str, str]]) -> list[dict]:
    """Coleta notícias de todos os feeds configurados, agregando os resultados."""
    all_items = []
    for source_name, feed_url in feeds:
        logger.info("Coletando notícias de %s...", source_name)
        items = collect_news_from_feed(source_name, feed_url)
        logger.info("  %d notícia(s) encontrada(s) em %s", len(items), source_name)
        all_items.extend(items)
    return all_items
