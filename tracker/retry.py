"""
Decorator de retry com backoff exponencial.

Chamadas de rede falham por motivos transitórios (timeout, instabilidade
momentânea do servidor). Em vez de desistir na primeira falha, tentamos
de novo algumas vezes, esperando um pouco mais a cada tentativa.
"""
import functools
import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger("tracker")

T = TypeVar("T")


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Decorator que reexecuta a função decorada em caso de exceção,
    com espera crescente entre tentativas (1s, 2s, 4s, ...).

    Uso:
        @retry_with_backoff(max_retries=3)
        def chamar_api():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        logger.error(
                            "%s falhou após %d tentativas: %s",
                            func.__name__, max_retries, exc,
                        )
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "%s falhou (tentativa %d/%d): %s. Tentando de novo em %.1fs...",
                        func.__name__, attempt, max_retries, exc, delay,
                    )
                    time.sleep(delay)
            raise last_exception  # pragma: no cover (inalcançável na prática)
        return wrapper
    return decorator
