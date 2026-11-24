"""Pobiera wszystkie włączone źródła i scala je z data/items.json.

Uruchomienie: python -m gn.fetch
Błąd jednego źródła nie przerywa pozostałych; wynik każdego trafia do data/status.json.
"""
from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import urljoin
from pathlib import Path

import yaml

from . import photo_ai
from .fetchers import ADAPTERS, http
from .models import now_iso

ROOT = Path(__file__).resolve().parent.parent
ITEMS_PATH = ROOT / "data" / "items.json"
STATUS_PATH = ROOT / "data" / "status.json"
MAX_ITEMS = 600
MAX_PER_RUN = 50
MAX_IMAGE_LOOKUPS = 40  # ile stron artykułów odwiedzamy w jednym przebiegu w poszukiwaniu miniatury
OG_IMAGE = re.compile(r"<meta[^>]+(?:property|name)=[\"'](?:og:image|twitter:image)[\"'][^>]*>", re.I)  # ile najnowszych wpisów bierzemy z jednego źródła na przebieg


def load_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def merge(existing: list[dict], fresh: list[dict]) -> tuple[list[dict], int]:
    """Dokleja nowe wpisy. Znane wpisy zachowują datę publikacji, ale tytuł i lead są
    odświeżane (źródło mogło je poprawić, a poprawki adapterów mają objąć stare wpisy);
    wydarzenia (`event_date`) dostają też aktualny termin.
    """
    known = {item["id"]: item for item in existing}
    titles = {(item["source"], item["title"].casefold()) for item in existing}
    added = 0
    for item in fresh:
        key = (item["source"], item["title"].casefold())
        if item["id"] in known:
            old = known[item["id"]]
            titles.discard((old["source"], old["title"].casefold()))
            old.update(title=item["title"], lead=item["lead"])
            if item.get("event_date"):
                old["event_date"] = item["event_date"]
            titles.add(key)
            continue
        if key in titles and not item.get("event_date"):
            continue
        existing.append(item)
        known[item["id"]] = item
        titles.add(key)
        added += 1
    existing.sort(key=lambda i: (i["published"], i["fetched_at"]), reverse=True)
    return existing[:MAX_ITEMS], added


def page_image(url: str) -> str:
    """Adres miniatury z nagłówka strony artykułu (og:image) albo pusty tekst."""
    try:
        html = http.get(url, tries=1).text[:300_000]
    except Exception:  # noqa: BLE001 – brak miniatury nie jest błędem
        return ""
    for tag in OG_IMAGE.findall(html):
        found = re.search(r"content=[\"']([^\"']+)", tag)
        if found:
            return urljoin(url, unescape(found.group(1)))
    return ""


def add_images(items: list[dict], budget: int = MAX_IMAGE_LOOKUPS) -> int:
    """Uzupełnia miniatury wpisów, których jeszcze nie sprawdzano (brak klucza `image`).

    Wydarzenia pomijamy (mają kafelek z datą). Każdy wpis sprawdzamy raz; wynik – także pusty –
    zostaje zapisany, więc kolejne przebiegi nie odwiedzają tej samej strony ponownie.
    """
    done = 0
    for item in items:  # lista jest posortowana od najnowszych
        if done >= budget:
            break
        if "image" in item or item.get("event_date"):
            continue
        item["image"] = page_image(item["url"])
        done += 1
    return done


def include_pattern(include: str | list[str]) -> re.Pattern:
    """Filtr `include` z sources.yaml: jeden regex albo lista regexów (dowolny pasujący wystarcza)."""
    parts = [include] if isinstance(include, str) else list(include)
    return re.compile("|".join(f"(?:{part})" for part in parts), re.I)


def run() -> int:
    sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))["sources"]
    site = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    if site.get("bot_url"):  # bot przedstawia się adresem repozytorium serwisu
        http.USER_AGENT = f"lokalnie-news-bot/0.2 (+{site['bot_url']})"
    items = load_json(ITEMS_PATH, [])
    status = []
    for source in sources:
        if not source.get("enabled", True):
            continue
        entry = {"id": source["id"], "name": source["name"], "url": source["url"],
                 "home": source.get("home", source["url"]), "checked_at": now_iso()}
        try:
            fetched = ADAPTERS[source["adapter"]](source)
            total = len(fetched)
            if source.get("exclude_title"):  # np. powtarzalne ogłoszenia bez wartości dla czytelnika
                skip = re.compile(source["exclude_title"], re.I)
                fetched = [item for item in fetched if not skip.search(item.title)]
            if source.get("include"):  # źródło szersze niż serwis (dzielnica, miasto): tylko wpisy o okolicy
                keep = include_pattern(source["include"])
                fetched = [item for item in fetched if keep.search(f"{item.title} {item.lead}")]
                entry["filtered"] = True
            fresh = sorted((i.to_dict() for i in fetched), key=lambda i: i["published"],
                           reverse=True)[:MAX_PER_RUN]
            items, added = merge(items, fresh)
            # przy filtrze `include` zero trafień to normalny wynik, a nie błąd struktury strony
            ok = bool(fetched) or (entry.pop("filtered", False) and total > 0)
            entry.update(ok=ok, found=len(fetched), added=added,
                         error="" if ok else "0 wpisów – sprawdź strukturę strony")
        except Exception as error:  # noqa: BLE001 – jedno źródło nie może zatrzymać reszty
            entry.update(ok=False, found=0, added=0, error=str(error)[:600])
        status.append(entry)
        print(f"[{'OK ' if entry['ok'] else 'ERR'}] {entry['id']}: znaleziono {entry['found']}, "
              f"nowych {entry['added']} {entry['error']}")
    if site.get("source_images"):
        print(f"Miniatury: sprawdzono {add_images(items)} wpisów")
    try:  # dobór ilustracji modelem AI; bez klucza albo przy awarii serwis zostaje przy słowach-kluczach
        print(photo_ai.annotate(items, ROOT, bool(site.get("source_images")),
                                site.get("photo_ai_model") or photo_ai.DEFAULT_MODEL))
    except Exception as error:  # noqa: BLE001
        print(f"Dobór zdjęć AI: pominięty ({str(error)[:300]})")
    save_json(ITEMS_PATH, items)
    save_json(STATUS_PATH, status)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
