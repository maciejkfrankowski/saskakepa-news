"""Wspólny klient HTTP: identyfikowalny User-Agent, timeout, jedna próba ponowienia."""
from __future__ import annotations

import time

import requests

USER_AGENT = "lokalnie-news-bot/0.2"  # gn.fetch dopisuje adres z site.yaml (bot_url)
TIMEOUT = 25


def get(url: str, tries: int = 2) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(tries):
        try:
            response = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Language": "pl, de;q=0.9, en;q=0.5",
                    "Accept": "application/rss+xml, application/xml, text/html;q=0.9, */*;q=0.8",
                    "Cache-Control": "no-cache",
                },
            )
            response.raise_for_status()
            return response
        except requests.RequestException as error:  # noqa: PERF203
            last_error = error
            if attempt + 1 < tries:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{url}: {last_error}")
