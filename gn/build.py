"""Generator statyczny: data/items.json + content/articles/*.md -> dist/.

Uruchomienie: python -m gn.build
"""
from __future__ import annotations

import json
import re
import shutil
import zlib
from datetime import date
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import clean_lead
from .sudoku import daily

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BRAND = "Lokalos"  # napis pod nazwą miejscowości, taki sam w każdym serwisie
T: dict = {}  # teksty interfejsu z i18n/<lang>.yaml, ładowane w build()
PL_MAP = str.maketrans({**str.maketrans("ąćęłńóśźż", "acelnoszz"),
                        ord("ä"): "ae", ord("ö"): "oe", ord("ü"): "ue", ord("ß"): "ss"})


POOL_DIR = Path("static") / "img" / "topics-photo"
POOL_FILE = re.compile(r"^([a-z]+)[-_ ].*\.(jpe?g|png|webp)$", re.I)
POOL_WIDTH = 800


def photo_pool(root: Path) -> dict[str, list[str]]:
    """Pula zdjęć tematycznych: pliki `<temat>-<cokolwiek>.jpg|png|webp` pogrupowane po temacie."""
    pool: dict[str, list[str]] = {}
    folder = root / POOL_DIR
    for path in sorted(folder.iterdir()) if folder.is_dir() else []:
        match = POOL_FILE.match(path.name)
        if match:
            pool.setdefault(match.group(1).lower(), []).append(path.name)
    return pool


def pick_photo(pool: dict[str, list[str]], topic: str, key: str) -> str:
    """Zdjęcie z puli dla tematu (albo z grupy `general`); to samo dla danego wpisu przy każdej budowie."""
    files = pool.get(topic) or pool.get("general") or []
    return files[zlib.crc32(key.encode()) % len(files)] if files else ""


def publish_pool(pool: dict[str, list[str]], dist: Path) -> dict[str, str]:
    """Zmniejsza zdjęcia z puli do WebP w `dist/` (oryginały zostają tylko w repo). Zwraca nazwa -> ścieżka."""
    folder = dist / POOL_DIR
    names = [name for files in pool.values() for name in files]
    try:
        from PIL import Image, ImageOps
    except ImportError:  # bez Pillow publikujemy oryginały
        return {name: (POOL_DIR / name).as_posix() for name in names}
    published = {}
    for name in names:
        source = folder / name
        target = source.with_suffix(".webp")
        try:
            with Image.open(source) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((POOL_WIDTH, POOL_WIDTH * 2))
                image.save(target, "WEBP", quality=80)
            if source != target:
                source.unlink()
            published[name] = (POOL_DIR / target.name).as_posix()
        except Exception as error:  # noqa: BLE001 – uszkodzony plik nie może zatrzymać budowy
            print(f"Pula zdjęć: pominięto {name}: {error}")
            source.unlink(missing_ok=True)
    return published


def date_pl(iso: str) -> str:
    """Data w formacie języka serwisu (np. „14 listopada 2026” / „14. November 2026”)."""
    year, month, day = (int(part) for part in iso[:10].split("-"))
    return T["date_fmt"].format(d=day, month=T["months"][month - 1], y=year)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower().translate(PL_MAP)).strip("-")


def load_articles() -> list[dict]:
    """Własne artykuły: Markdown z nagłówkiem YAML między liniami `---`."""
    articles = []
    for path in sorted((ROOT / "content" / "articles").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
        if not match:
            print(f"[POMINIĘTO] {path.name}: brak nagłówka YAML")
            continue
        meta = yaml.safe_load(match.group(1)) or {}
        if meta.get("draft") or not meta.get("title") or not meta.get("date"):
            continue
        slug = meta.get("slug") or slugify(path.stem)
        articles.append({
            "title": meta["title"],
            "lead": meta.get("lead") or "",
            "published": str(meta["date"])[:10],
            "category": meta.get("category") or "redakcja",
            "image": str(meta.get("image") or "").lstrip("/"),
            "image_credit": str(meta.get("image_credit") or "").strip(),
            "featured": bool(meta.get("featured")),
            "href": f"{T['paths']['article']}/{slug}/",
            "external": False,
            "source_name": T["editorial"],
            "body": markdown.markdown(match.group(2), extensions=["extra"]),
        })
    return articles


def load_items(show_images: bool = False) -> list[dict]:
    path = ROOT / "data" / "items.json"
    items = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    for item in items:
        item.update(href=item["url"], external=True, featured=False, image=item.get("image") or "",
                    event_date=item.get("event_date", ""))
        if not item["event_date"]:
            item["lead"] = clean_lead(item["lead"])
    # Miniatury ze źródeł: tylko gdy włączone w site.yaml. Ten sam obraz przy wielu wpisach jednego
    # źródła to zwykle logo serwisu, a nie zdjęcie artykułu – takie pomijamy.
    counts: dict[tuple, int] = {}
    for item in items:
        if item["image"]:
            counts[(item["source"], item["image"])] = counts.get((item["source"], item["image"]), 0) + 1
    for item in items:
        usable = show_images and item["image"].startswith(("https://", "data:")) and not item["event_date"]
        if not usable or counts[(item["source"], item["image"])] > 2:
            item["image"] = ""
    return items


def event_labels(stamp: str) -> dict:
    """Etykiety terminu wydarzenia z `RRRR-MM-DD GG:MM:SS`."""
    year, month, day = (int(part) for part in stamp[:10].split("-"))
    time = stamp[11:16] if stamp[11:16] not in ("", "00:00") else ""
    label = T["event_fmt"].format(d=day, month=T["months"][month - 1], y=year)
    return {"event_pl": label + (T["event_time_fmt"].format(time=time) if time else ""),
            "event_day": day, "event_mon": T["months"][month - 1][:3]}


BACK_BAR = ('<a href="../../" style="display:block;padding:10px 14px;background:#173b2a;color:#fff;'
            'font:600 14px system-ui,sans-serif;text-decoration:none">← {label}</a>')


def build_crosswords(site: dict) -> list[dict]:
    """Kopiuje gotowe krzyżówki (samodzielne pliki HTML) do dist/<fun>/<crosswords>/.

    Do każdej dokleja pasek powrotu do serwisu; plik źródłowy pozostaje bez zmian.
    """
    base = f"{T['paths']['fun']}/{T['paths']['crosswords']}"
    bar = BACK_BAR.format(label=f"{site['title']} {site['subtitle']} · {T['nav_fun']}")
    found = []
    folder = ROOT / "content" / "krzyzowki"
    for path in sorted(folder.glob("*.html")) if folder.exists() else []:
        html = path.read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
        slug = slugify(path.stem)
        html = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + bar, html, count=1, flags=re.I)
        target = DIST / base / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        name = (title.group(1).strip() if title else path.stem)
        suffix = re.escape(T["crossword_suffix"])
        found.append({"title": re.sub(rf"\s*[–-]\s*{suffix}\s*$", "", name, flags=re.I),
                      "href": f"{base}/{slug}/"})
    return found


def build() -> None:
    site = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    site["subtitle"] = BRAND  # wspólna marka wszystkich serwisów; `subtitle` z site.yaml jest ignorowane
    T.clear()
    T.update(yaml.safe_load((ROOT / "i18n" / f"{site.get('lang', 'pl')}.yaml").read_text(encoding="utf-8")))
    paths = T["paths"]
    categories = {c["slug"]: c for c in site["categories"]}
    fallback = site["categories"][0]

    today_iso = date.today().isoformat()
    everything = load_articles() + load_items(bool(site.get("source_images")))
    for entry in everything:
        entry.setdefault("event_date", "")
        entry["cat"] = categories.get(entry["category"], fallback)
        entry["date_pl"] = date_pl(entry["published"])
        if entry["event_date"]:
            entry.update(event_labels(entry["event_date"]))
    topics = [(name, re.compile(pattern, re.I)) for name, pattern in (T.get("topics") or {}).items()]
    for entry in everything:  # ilustracja tematyczna tylko tam, gdzie nie ma zdjęcia
        entry["topic"] = "" if entry["image"] or entry["event_date"] else next(
            (name for name, pattern in topics if pattern.search(entry["title"])), "")
    # zdjęcie ilustracyjne z puli zastępuje rysowaną ilustrację; wpisy ze zdjęciem i wydarzenia zostają bez zmian
    pool = photo_pool(ROOT)
    for entry in everything:
        entry["pool_file"] = "" if entry["image"] or entry["event_date"] else pick_photo(
            pool, entry["topic"], entry.get("id") or entry["href"])
    # Wydarzenia (z terminem) idą osobnym torem: tylko nadchodzące, od najbliższego
    events = sorted((e for e in everything if e["event_date"][:10] >= today_iso),
                    key=lambda e: e["event_date"])
    # to samo wydarzenie bywa u źródła pod dwoma adresami (np. strona główna i podstrona filii)
    unique: dict[tuple, dict] = {}
    for event in events:
        unique.setdefault((event["source"], event["title"].casefold(), event["event_date"]), event)
    events = list(unique.values())
    entries = [e for e in everything if not e["event_date"]]
    entries.sort(key=lambda e: (e["published"], not e["external"]), reverse=True)

    status_path = ROOT / "data" / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else []
    sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))["sources"]

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    # dolny pasek na telefonie: z konfiguracji albo pierwsza kategoria + transportowa (ikona autobusu)
    transit = [c["slug"] for c in site["categories"][1:] if c.get("icon") == "bus"]
    tab_slugs = site.get("tabbar") or [site["categories"][0]["slug"], *(transit or [c["slug"] for c in site["categories"][1:2]])]
    env.globals.update(show_events=site.get("events_nav", True), tabs=[categories[s] for s in tab_slugs if s in categories], t=T, p=paths, lang=site.get("lang", "pl"), site=site, nav=[c for c in site["categories"] if c.get("nav", True)],
                       build_date=date_pl(date.today().isoformat()))

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST / "static")
    shutil.copytree(ROOT / "admin", DIST / "admin")
    published = publish_pool(pool, DIST)
    for entry in everything:
        entry["photo"] = published.get(entry.pop("pool_file"), "")
    (DIST / ".nojekyll").write_text("")

    def render(template: str, target: str, **context) -> None:
        path = DIST / target / "index.html" if target else DIST / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        root = "../" * target.strip("/").count("/") + "../" if target else ""
        path.write_text(env.get_template(template).render(root=root, **context), encoding="utf-8")

    # Strona główna
    hero = next((e for e in entries if e["featured"]), entries[0] if entries else None)
    rest = [e for e in entries if e is not hero]
    today, seen = events[:2], set()
    for entry in rest:  # „Grodzisk dziś”: najnowszy wpis z każdej kategorii
        if entry["category"] not in seen:
            seen.add(entry["category"])
            today.append(entry)
    fresh = [e for e in rest if e not in today[:4]]
    top, more = fresh[:2], fresh[2:8]  # dwie duże pozycje + zwarta lista
    # Strona główna zawiera też zawartość kategorii (domyślnie po 4 najnowsze), a na końcu wydarzenia;
    # menu przewija do tych sekcji. Pełne listy zostają na podstronach kategorii.
    per_category = int(site.get("home_per_category", 4))   # opcjonalne klucze w site.yaml
    home_events = int(site.get("home_events", 8))
    sections = []
    for cat in env.globals["nav"]:
        found = [e for e in entries if e["category"] == cat["slug"]]
        if found:
            sections.append({"cat": cat, "entries": found[:per_category], "total": len(found)})
    env.globals["anchors"] = {section["cat"]["slug"] for section in sections}
    env.globals["events_anchor"] = bool(events)
    render("index.html", "", hero=hero, today=today[:4], top=top, more=more, events=events[:home_events],
           events_total=len(events), sections=sections, active="")

    # Kategorie
    for cat in site["categories"]:
        render("list.html", f"{paths['cat']}/{cat['slug']}", cat=cat, active=cat["slug"],
               entries=[e for e in entries if e["category"] == cat["slug"]][:60])

    # Artykuły własne
    for entry in entries:
        if not entry["external"]:
            render("article.html", entry["href"].strip("/"), entry=entry, active="")

    crosswords = build_crosswords(site)
    sudoku = daily(today_iso)
    for level in sudoku["levels"]:
        level["name"] = T["sudoku_levels"].get(level["slug"], level["name"])
    render("wydarzenia.html", paths["events"], entries=events[:80], active="events")
    render("rozrywka.html", paths["fun"], active="fun", sudoku=sudoku, crosswords=crosswords,
           sudoku_date=date_pl(today_iso))
    render("zrodla.html", paths["sources"], sources=sources, active="",
           status={s["id"]: s for s in status}, pool={topic: len(files) for topic, files in pool.items()})
    if site.get("operator"):  # strony wymagane prawem (np. w Niemczech)
        render("impressum.html", paths["imprint"], active="")
        render("datenschutz.html", paths["privacy"], active="")

    search = [{"t": e["title"], "l": e["lead"], "u": e["href"], "x": e["external"],
               "d": e.get("event_pl") or e["date_pl"], "s": e["source_name"]}
              for e in events[:80] + entries[:300]]
    (DIST / "search.json").write_text(json.dumps(search, ensure_ascii=False), encoding="utf-8")
    print(f"Zbudowano dist/: {len(entries)} wpisów, {len(events)} wydarzeń, {len(site['categories'])} kategorii")


if __name__ == "__main__":
    build()
