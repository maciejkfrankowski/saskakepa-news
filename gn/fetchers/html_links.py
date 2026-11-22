"""Adapter HTML bez znajomości klas CSS.

Szuka linków pasujących do `link_pattern` (regex na pełnym URL), a tytuł, datę
i lead bierze z najbliższego kontenera, który zawiera dokładnie jeden taki wpis.
Dzięki temu jeden adapter obsługuje strony typu /aktualnosci/{id}.

Opcje źródła: `strip` (regexy wycinane z tytułu i leadu), `require_date` (pomija linki,
przy których nie ma daty – przydatne, gdy wzorzec URL łapie też menu), `events` (wpisy to
wydarzenia: data i „godz. GG:MM” albo „DD.MM.RRRR, GG:MM” z listy trafiają do `event_date`).
"""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from ..models import Item, clean_lead, clean_text, find_date, make_id, now_iso
from . import http

MAX_CLIMB = 5
MIN_TITLE = 8
TITLE_CLASS = re.compile(r"title|tytul", re.I)
ELLIPSIS = re.compile(r"\s*(\.{3}|…)\s*$")
AFTER_DATE = re.compile(r"\s*,?\s*(\d{1,2})[:.](\d{2})\b")  # „21.11.2026, 19:00”
TIME = re.compile(r"(?i)(?:\bgodz\.?\s*(\d{1,2})[:.](\d{2})|\b(\d{1,2})[:.](\d{2})\s*Uhr\b)")
DATE = (r"\b\d{1,2}\s?[.\-/]\s?\d{1,2}\s?[.\-/]\s?\d{4}\b(\s*r\.)?|\b\d{4}-\d{2}-\d{2}\b"
        r"|\b\d{1,2}\.?\s+(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember"
        r"|Jan|Feb|Mär|Apr|Jun|Jul|Aug|Sep|Sept|Okt|Nov|Dez)\.?\s+\d{4}\b")
MORE = re.compile(r"(?i)\b(czytaj (więcej|dalej)|więcej|zobacz|weiterlesen|mehr erfahren|mehr lesen|mehr)\b\s*[»>→]*")


def _container(anchor: Tag, url: str, base: str, pattern: re.Pattern) -> Tag:
    """Największy przodek, w którym wszystkie pasujące linki prowadzą do `url`."""
    best: Tag = anchor
    node = anchor.parent
    for _ in range(MAX_CLIMB):
        if node is None or node.name in ("body", "html", "[document]"):
            break
        urls = {
            urljoin(base, a["href"]).split("#")[0]
            for a in node.find_all("a", href=True)
            if pattern.search(urljoin(base, a["href"]))
        }
        if urls != {url}:
            break
        best = node
        node = node.parent
    return best


HEADING = re.compile(r"^h[1-6]$")
DATE_RE = re.compile(DATE)
EDGES = " \t,;:|·–-"


def _scope(anchor: Tag, box: Tag, strip: list[re.Pattern]) -> Tag:
    """Najmniejszy przodek linku (najwyżej `box`), w którym jest i tytuł, i data.

    Chroni przed sklejeniem wpisu z sąsiadem, gdy sąsiad nie ma własnego pasującego linku.
    """
    node = anchor
    while True:
        text = clean_text(node.get_text(" "))
        titled = (node.find(HEADING) or node.find(class_=TITLE_CLASS)
                  or (node is not anchor and len(DATE_RE.sub("", text)) >= MIN_TITLE + 4))
        if titled and find_date(text):
            return node
        if node is box or node.parent is None:
            return box
        node = node.parent


def _tidy(text: str, strip: list[re.Pattern], listing_date: str | None = None,
          anywhere: bool = False, drop_time: bool = False) -> str:
    """Czyści tytuł lub lead.

    Usuwa fragmenty z `strip` (sources.yaml) oraz datę wpisu z listy (`listing_date`): na początku
    lub końcu tekstu, a przy `anywhere` – jej pierwsze wystąpienie. Inne daty zostają, bo bywają
    częścią tytułu („…ab dem 01.08.2026…”). `drop_time` usuwa „godz. 18:00” / „18:00 Uhr”.
    """
    for pattern in strip:
        text = pattern.sub(" ", text)
    text = clean_text(text)
    if drop_time:
        text = clean_text(TIME.sub(" ", text))
    if listing_date:
        for match in DATE_RE.finditer(text):
            if find_date(match.group()) != listing_date:
                continue
            at_edge = not text[:match.start()].strip(EDGES) or not text[match.end():].strip(EDGES)
            if anywhere or at_edge:
                text = text[:match.start()] + " " + text[match.end():]
                break
    return clean_text(text).strip(EDGES).strip()


def parse(html: str, source: dict) -> list[Item]:
    base = source["url"]
    strip = [re.compile(p) for p in source.get("strip", [])]
    pattern = re.compile(source["link_pattern"])
    soup = BeautifulSoup(html, "lxml")
    fetched = now_iso()

    anchors: dict[str, list[Tag]] = {}
    for anchor in soup.find_all("a", href=True):
        url = urljoin(base, anchor["href"]).split("#")[0]
        if pattern.search(url):
            anchors.setdefault(url, []).append(anchor)

    events = bool(source.get("events"))
    items: list[Item] = []
    for url, group in anchors.items():
        # ten sam link bywa na stronie kilka razy (lista, siatka kalendarza, miniatura);
        # bierzemy wystąpienie, przy którym jest data
        boxes = [_scope(anchor, _container(anchor, url, base, pattern), strip) for anchor in group]
        texts = [clean_text(box.get_text(" ")) for box in boxes]
        dated = next((n for n, text in enumerate(texts) if find_date(text)), None)
        if dated is None and (events or source.get("require_date")):
            continue  # link z menu lub stopki, nie wpis z listy
        box, box_text = boxes[dated or 0], texts[dated or 0]
        heading = box.find(HEADING) or box.find(class_=TITLE_CLASS)
        candidates = [clean_text(a.get_text(" ")) for a in group] + [a.get("title", "") for a in group]
        if heading:
            candidates.insert(0, clean_text(heading.get_text(" ")))
        candidates = [c for c in candidates if len(_tidy(c, strip)) >= MIN_TITLE]
        if not candidates:
            continue
        raw_title = candidates[0] if heading else max(candidates, key=len)
        # data wpisu to data z listy, a nie data wymieniona w samym tytule
        listed = find_date(box_text.replace(raw_title, " ")) or find_date(box_text)
        published = listed or date.today().isoformat()

        def tidy(text: str, anywhere: bool = False) -> str:
            return _tidy(text, strip, listed, anywhere=anywhere, drop_time=events)

        title = tidy(raw_title)
        if ELLIPSIS.search(title):  # ucięty tytuł: szukamy pełnej wersji przy innym wystąpieniu linku
            stem = ELLIPSIS.sub("", title)[:20]
            full = [t for t in (tidy(c) for c in candidates)
                    if t.startswith(stem) and not ELLIPSIS.search(t)]
            title = max(full, key=len) if full else title

        event_date = ""
        if events:
            clock = TIME.search(box_text)
            hour, minute = (clock.group(1) or clock.group(3), clock.group(2) or clock.group(4)) if clock else (0, "00")
            if not clock:  # godzina bez „godz.”, zaraz po dacie z listy
                for match in DATE_RE.finditer(box_text):
                    after = AFTER_DATE.match(box_text, match.end())
                    if after and find_date(match.group()) == listed and int(after.group(1)) < 24:
                        hour, minute = after.group(1), after.group(2)
                        break
            event_date = f"{published} {int(hour):02d}:{minute}:00"
            published, lead = date.today().isoformat(), ""
        else:
            lead = tidy(box_text.replace(raw_title, " "), anywhere=True).replace(title, " ")
            lead = MORE.sub(" ", lead)
        items.append(
            Item(
                id=make_id(url),
                source=source["id"],
                source_name=source["name"],
                category=source["category"],
                title=title,
                lead=clean_lead(lead),
                url=url,
                published=published,
                fetched_at=fetched,
                event_date=event_date,
            )
        )
    return items


def fetch(source: dict) -> list[Item]:
    response = http.get(source["url"])
    response.encoding = response.apparent_encoding or response.encoding
    return parse(response.text, source)
