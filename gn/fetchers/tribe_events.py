"""Adapter kalendarza „The Events Calendar” (WordPress) przez REST API.

Adres: {strona}/wp-json/tribe/events/v1/events – zwraca nadchodzące wydarzenia.
"""
from __future__ import annotations

import json
from datetime import date

from ..models import Item, clean_lead, clean_text, make_id, now_iso
from . import http


def parse(content: bytes | str, source: dict) -> list[Item]:
    payload = json.loads(content)
    fetched = now_iso()
    items: list[Item] = []
    for event in payload.get("events", []):
        url = (event.get("url") or "").strip()
        title = clean_text(event.get("title", ""))
        start = (event.get("start_date") or "").strip()
        if not url or not title or len(start) < 10:
            continue
        venue = event.get("venue") or {}
        place = clean_text(venue.get("venue", "")) if isinstance(venue, dict) else ""
        text = clean_lead(event.get("excerpt") or event.get("description") or "", limit=180)
        items.append(
            Item(
                id=make_id(url),
                source=source["id"],
                source_name=source["name"],
                category=source["category"],
                title=title,
                lead=" · ".join(part for part in (place, text) if part),
                url=url,
                published=date.today().isoformat(),
                fetched_at=fetched,
                event_date=start if not event.get("all_day") else start[:10] + " 00:00:00",
            )
        )
    return items


def fetch(source: dict) -> list[Item]:
    return parse(http.get(source["url"]).content, source)
