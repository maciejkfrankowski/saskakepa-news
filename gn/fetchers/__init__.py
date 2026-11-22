"""Rejestr adapterów: nazwa z sources.yaml -> funkcja fetch(source) -> list[Item]."""
from . import html_links, http, rss, tribe_events

ADAPTERS = {
    "rss": rss.fetch,
    "html_links": html_links.fetch,
    "tribe_events": tribe_events.fetch,
}
