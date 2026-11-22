"""Adapter RSS/Atom (WordPress i pokrewne)."""
from __future__ import annotations

import re
import time
from datetime import date

import feedparser

from ..models import Item, clean_lead, clean_text, make_id, now_iso
from . import http


IMG = re.compile(r'<img[^>]+src=["\']([^"\']+)', re.I)


def entry_image(entry) -> str:
    """Miniatura wpisu, jeśli kanał ją podaje (media:content, enclosure albo pierwszy obraz w treści)."""
    for key in ("media_content", "media_thumbnail"):
        for media in entry.get(key, []):
            if media.get("url") and "image" in (media.get("type") or media.get("medium") or "image"):
                return media["url"]
    for enclosure in entry.get("enclosures", []):
        if enclosure.get("type", "").startswith("image") and enclosure.get("href"):
            return enclosure["href"]
    html = " ".join(part.get("value", "") for part in entry.get("content", [])) + entry.get("summary", "")
    for url in IMG.findall(html):
        if not re.search(r"emoji|\.svg|\.gif|pixel|gravatar", url, re.I):
            return url
    return ""


def parse(content: bytes | str, source: dict) -> list[Item]:
    feed = feedparser.parse(content)
    fetched = now_iso()
    items: list[Item] = []
    for entry in feed.entries:
        url = (entry.get("link") or "").strip()
        title = clean_text(entry.get("title", ""))
        if not url or not title:
            continue
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        published = time.strftime("%Y-%m-%d", stamp) if stamp else date.today().isoformat()
        items.append(
            Item(
                id=make_id(url),
                source=source["id"],
                source_name=source["name"],
                category=source["category"],
                title=title,
                lead=clean_lead(entry.get("summary", "")),
                url=url,
                published=published,
                fetched_at=fetched,
                image=entry_image(entry),
            )
        )
    return items


def fetch(source: dict) -> list[Item]:
    """Próbuje `url`, a potem `fallback_urls`; przy 0 wpisów zgłasza, co zwrócił serwer."""
    notes = []
    for url in [source["url"], *source.get("fallback_urls", [])]:
        try:
            response = http.get(url)
        except RuntimeError as error:
            notes.append(str(error)[:120])
            continue
        items = parse(response.content, source)
        if items:
            return items
        snippet = clean_text(response.text[:400])[:70]
        notes.append(f"{url}: HTTP {response.status_code}, "
                     f"{response.headers.get('Content-Type', '?')}, treść: „{snippet}”")
    raise RuntimeError("0 wpisów w RSS. " + " | ".join(notes))
