"""Dobór ilustracji z puli małym modelem AI (opis: docs/04-dobor-zdjec-ai.md).

Jedno zapytanie na paczkę wpisów: model dostaje katalog scen (`gn/photo_scenes.yaml`) oraz tytuły
i zajawki, a dla każdego wpisu zwraca temat, ranking najwyżej 3 plików z tego tematu i – gdy żadna
scena nie pasuje – krótką nazwę brakującego zdjęcia. Odpowiedź jest sprawdzana z listą plików;
wszystko spoza listy odrzucamy (wpis zostaje przy regexie).

`gn.fetch` woła `annotate()` po pobraniu źródeł; wynik zostaje przy wpisie w `data/items.json`
(pole `photo_ai`), więc każdy wpis jest oceniany raz. `gn.build` czyta to pole przy doborze zdjęć.
Bez klucza w zmiennej OPENROUTER_API_KEY nic się nie dzieje i serwis działa na regexie.

    python -m gn.photo_ai --compare 50      # raport photo_ai_report.html: regex kontra model
    python -m gn.photo_ai --prompt          # wypisuje prompt systemowy (bez sieci i bez klucza)
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
from collections import Counter
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCENES_PATH = Path(__file__).resolve().parent / "photo_scenes.yaml"
POOL_DIR = Path("static") / "img" / "topics-photo"
POOL_FILE = re.compile(r"^([a-z]+)[-_ ].*\.(jpe?g|png|webp)$", re.I)
API_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_ENV = "OPENROUTER_API_KEY"
DEFAULT_MODEL = "anthropic/claude-haiku-5.5"
BATCH = 25          # ile wpisów w jednym zapytaniu
MAX_CALLS = 10      # limit zapytań na przebieg (250 wpisów: wystarcza na jednorazowe uzupełnienie starych)
MAX_PICKS = 3
TIMEOUT = 120
MAX_TOKENS = 8000   # z dużym zapasem: część modeli wlicza tu także tokeny „namysłu” przed odpowiedzią
NONE = "none"       # model uznał, że wpis nie powinien dostać zdjęcia z puli (temat wrażliwy)

PROMPT = """You choose a stock illustration for cards on a small-town local news site.
The illustration is a generic symbolic photo (an object or a place). It never shows the actual event.
Each article is given as its title and a short lead, in Polish or German.

Photo groups and scenes (id: what the photo shows):
{catalog}

For every article decide:
1. "topic": the one group that matches what the article is ABOUT. Judge the meaning, not single words:
   "dziki lokator" (a squatter) is not about boars, "sesja zdjęciowa" (a photo shoot) is not a council session,
   a concert held in a library is "stage". Use "general" when the subject is neutral but fits no group.
2. "picks": up to {max_picks} scene ids from that group only, best first. Prefer the scene whose object and mood fit
   the article (a stolen bicycle: a locked bicycle; a remembrance ceremony: a wreath or candles, not bunting
   or balloons). Give fewer picks when the other scenes would look out of place.
3. "missing": only when no scene in the catalog really fits the article, name the photo you would have wanted
   in 1-3 English words, lowercase (for example "playground", "christmas tree", "dog"). Otherwise omit it.

Use topic "none" with empty picks when a symbolic photo would be tasteless or misleading:
a death, obituary or funeral, national mourning, an accident with casualties, violence or a crime against
a person, a missing person, harm to children, a suicide, a named person's serious illness.

Answer with JSON only, no commentary, one object per article, in the order given:
{{"items": [{{"id": <article number>, "topic": "<group or none>", "picks": ["<scene id>", ...], "missing": "<optional>"}}]}}"""


def photo_pool(root: Path) -> dict[str, list[str]]:
    """Pula zdjęć tematycznych: pliki `<temat>-<cokolwiek>.jpg|png|webp` pogrupowane po temacie."""
    pool: dict[str, list[str]] = {}
    folder = root / POOL_DIR
    for path in sorted(folder.iterdir()) if folder.is_dir() else []:
        match = POOL_FILE.match(path.name)
        if match:
            pool.setdefault(match.group(1).lower(), []).append(path.name)
    return pool


def load_catalog(pool: dict[str, list[str]] | None = None) -> dict[str, dict]:
    """Katalog scen: temat -> {"use": opis grupy, "scenes": {nazwa pliku bez rozszerzenia: opis}}.

    Gdy podano pulę (`photo_pool`), zostają tylko sceny, których pliki naprawdę są w repo –
    katalog może więc opisywać obrazy, które dopiero zostaną wgrane.
    """
    catalog = yaml.safe_load(SCENES_PATH.read_text(encoding="utf-8")) or {}
    if pool is None:
        return catalog
    kept = {}
    for topic, group in catalog.items():
        present = {Path(name).stem for name in pool.get(topic, [])}
        scenes = {key: text for key, text in group["scenes"].items() if key in present}
        if scenes:
            kept[topic] = {"use": group.get("use", ""), "scenes": scenes}
    return kept


def needs_photo(items: list[dict], show_images: bool) -> list[dict]:
    """Wpisy, które na stronie dostają zdjęcie z puli: bez terminu wydarzenia i bez użytecznej miniatury.

    Ta sama reguła co w `gn.build.load_items`: miniatura powtórzona przy więcej niż dwóch wpisach
    jednego źródła to logo serwisu, a nie zdjęcie artykułu.
    """
    counts = Counter((item["source"], item["image"]) for item in items if item.get("image"))
    found = []
    for item in items:
        image = item.get("image") or ""
        usable = show_images and image.startswith(("https://", "data:")) and counts[(item["source"], image)] <= 2
        if not item.get("event_date") and not usable:
            found.append(item)
    return found


def system_prompt(catalog: dict[str, dict]) -> str:
    lines = []
    for topic, group in catalog.items():
        lines.append(f"\n[{topic}] {group['use']}")
        lines += [f"  {key}: {text}" for key, text in group["scenes"].items()]
    return PROMPT.format(catalog="\n".join(lines).strip(), max_picks=MAX_PICKS)


def user_prompt(entries: list[dict]) -> str:
    """Wpisy do oceny: numer w paczce, tytuł i zajawka (dane publiczne).

    Numer zamiast identyfikatora wpisu: długie identyfikatory model przepisuje drogo i z błędami.
    """
    rows = [json.dumps({"id": number, "title": entry["title"], "lead": (entry.get("lead") or "")[:240]},
                       ensure_ascii=False) for number, entry in enumerate(entries, 1)]
    return "Articles:\n" + "\n".join(rows)


def parse_answer(text: str, entries: list[dict], catalog: dict[str, dict]) -> dict[str, dict]:
    """Odpowiedź modelu -> {id wpisu: {"topic": ..., "picks": [...], "missing": ...}}; tylko poprawne pozycje.

    Odrzucamy: numery spoza paczki, tematy spoza katalogu, pliki spoza wybranego tematu.
    Temat bez żadnego poprawnego pliku zostaje (ranking uzupełni kolejność domyślna).
    Czytamy pozycja po pozycji, więc z odpowiedzi uciętej w połowie zostają wszystkie pełne pozycje,
    a dopiski modelu (```json, komentarz) nie przeszkadzają.
    """
    numbers = {str(number): entry["id"] for number, entry in enumerate(entries, 1)}
    result: dict[str, dict] = {}
    for chunk in re.findall(r"\{[^{}]*\}", text or ""):
        try:
            row = json.loads(chunk)
        except ValueError:
            continue
        key = numbers.get(str(row.get("id")).strip())
        if key is None or key in result:
            continue
        topic = str(row.get("topic") or "").strip().lower()
        picks = row.get("picks") if isinstance(row.get("picks"), list) else []
        if topic == NONE:
            result[key] = {"topic": NONE, "picks": []}
            continue
        if topic not in catalog:
            continue
        scenes = catalog[topic]["scenes"]
        picks = [p for p in dict.fromkeys(x for x in picks if isinstance(x, str)) if p in scenes]
        result[key] = {"topic": topic, "picks": picks[:MAX_PICKS]}
        missing = row.get("missing")
        missing = re.sub(r"[^\w -]", "", missing.lower()).strip()[:40] if isinstance(missing, str) else ""
        if missing:
            result[key]["missing"] = missing
    return result


def ask(entries: list[dict], catalog: dict[str, dict], model: str = DEFAULT_MODEL,
        key: str | None = None) -> tuple[dict[str, dict], dict]:
    """Jedno zapytanie do OpenRouter. Zwraca (wyniki, zużycie tokenów). Błędy sieci idą wyjątkiem."""
    key = key or os.environ.get(KEY_ENV, "")
    if not key:
        raise RuntimeError(f"Brak klucza: ustaw zmienną środowiskową {KEY_ENV}")
    response = requests.post(API_URL, timeout=TIMEOUT, headers={"Authorization": f"Bearer {key}"}, json={
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "system", "content": system_prompt(catalog)},
                     {"role": "user", "content": user_prompt(entries)}],
    })
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:  # OpenRouter zwraca też błędy dostawcy ze statusem 200
        raise RuntimeError(str(payload["error"])[:300])
    choice = payload["choices"][0]
    text = choice["message"].get("content") or ""
    usage = dict(payload.get("usage") or {})
    found = parse_answer(text, entries, catalog)
    if len(found) < len(entries):  # ślad do diagnozy: ucięta odpowiedź, pusta treść, inny format
        usage["note"] = (f"{len(found)}/{len(entries)} pozycji, finish_reason={choice.get('finish_reason')}, "
                         f"początek odpowiedzi: {text[:160]!r}")
    return found, usage


def classify(entries: list[dict], catalog: dict[str, dict], model: str = DEFAULT_MODEL,
             max_calls: int = MAX_CALLS) -> tuple[dict[str, dict], dict]:
    """Ocenia wpisy paczkami po `BATCH`; błąd paczki nie przerywa pozostałych. Limit wywołań na przebieg.

    `usage["asked"]` to identyfikatory wpisów z paczek, na które model odpowiedział choć jedną poprawną
    pozycją – tych wpisów nie pytamy ponownie, nawet jeśli ich pozycja została odrzucona.
    """
    results: dict[str, dict] = {}
    usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "errors": [], "asked": []}
    for start in range(0, len(entries), BATCH):
        if usage["calls"] >= max_calls:
            break
        usage["calls"] += 1
        batch = entries[start:start + BATCH]
        try:
            found, used = ask(batch, catalog, model)
        except Exception as error:  # noqa: BLE001 – awaria modelu nie zatrzymuje przebiegu
            usage["errors"].append(str(error)[:300])
            continue
        results.update(found)
        if found:
            usage["asked"] += [entry["id"] for entry in batch]
        for name in ("prompt_tokens", "completion_tokens"):
            usage[name] += int(used.get(name) or 0)
        if used.get("note"):
            usage["errors"].append(used["note"])
    return results, usage


def annotate(items: list[dict], root: Path = ROOT, show_images: bool = True, model: str = DEFAULT_MODEL,
             max_calls: int = MAX_CALLS) -> str:
    """Dopisuje wpisom pole `photo_ai` (temat, ranking plików, brakujące zdjęcie). Zwraca komunikat do logu.

    Pytamy tylko o wpisy, które dostają zdjęcie z puli i nie mają jeszcze pola `photo_ai`, od najnowszych.
    Wpis z paczki, na którą model odpowiedział, ale bez poprawnej pozycji, dostaje pusty temat (zostaje
    przy regexie i nie jest pytany ponownie). Po błędzie całej paczki wpisy spróbują w następnym przebiegu.
    """
    if not os.environ.get(KEY_ENV):
        return f"Dobór zdjęć AI: wyłączony (brak {KEY_ENV})"
    catalog = load_catalog(photo_pool(root))
    todo = [item for item in needs_photo(items, show_images) if "photo_ai" not in item][:BATCH * max_calls]
    if not catalog or not todo:
        return "Dobór zdjęć AI: brak nowych wpisów" if catalog else "Dobór zdjęć AI: pusta pula lub katalog"
    results, usage = classify(todo, catalog, model, max_calls)
    asked = set(usage["asked"])
    for item in todo:
        if item["id"] in results:
            item["photo_ai"] = results[item["id"]]
        elif item["id"] in asked:
            item["photo_ai"] = {"topic": "", "picks": []}
    notes = f"; uwagi: {' | '.join(usage['errors'])}" if usage["errors"] else ""
    return (f"Dobór zdjęć AI ({model}): wpisów {len(todo)}, odpowiedzi {len(results)}, wywołań {usage['calls']}, "
            f"tokeny {usage['prompt_tokens']} wejście / {usage['completion_tokens']} wyjście{notes}")


def stats(items: list[dict]) -> dict:
    """Podsumowanie dla strony /zrodla/: ile wpisów w której grupie i jakich zdjęć najczęściej brakowało."""
    topics: Counter = Counter()
    missing: Counter = Counter()
    for item in items:
        info = item.get("photo_ai") or {}
        if info.get("topic"):
            topics[info["topic"]] += 1
        if info.get("missing"):
            missing[info["missing"]] += 1
    return {"asked": sum(topics.values()), "topics": topics.most_common(), "missing": missing.most_common(15)}


# --- raport „regex kontra model” -------------------------------------------------------------------

REPORT = """<!doctype html><html lang="pl"><meta charset="utf-8"><title>Dobór zdjęć: regex kontra model</title>
<style>body{{font:15px/1.4 system-ui,sans-serif;margin:24px;max-width:1100px}}
table{{border-collapse:collapse;width:100%}}td,th{{border-top:1px solid #ddd;padding:8px;vertical-align:top;text-align:left}}
img{{width:200px;height:125px;object-fit:cover;display:block;background:#eee}}small{{color:#666}}
.t{{font-weight:600}}#sum{{position:sticky;top:0;background:#fff;padding:8px 0;border-bottom:2px solid #333}}
label{{display:block;white-space:nowrap}}</style>
<h1>Dobór zdjęć: regex kontra model</h1>
<p>{meta}</p><p>{summary}</p><p id="sum"></p>
<table><tr><th>Wpis</th><th>Regex (dziś)</th><th>Model</th><th>Lepsze</th></tr>
{rows}</table>
<script>
function tally(){{var c={{r:0,m:0,e:0}},n=0;document.querySelectorAll('input:checked').forEach(function(i){{c[i.value]++;n++}});
document.getElementById('sum').textContent='Ocenione: '+n+' z {count} | regex lepszy: '+c.r+' | model lepszy: '+c.m+' | bez różnicy: '+c.e}}
document.addEventListener('change',tally);tally();
</script></html>"""


def _cell(topic: str, stem: str, files: dict[str, str], extra: str = "") -> str:
    name = files.get(stem, "")
    image = f'<img src="static/img/topics-photo/{html.escape(name)}" alt="">' if name else "<small>bez zdjęcia z puli</small>"
    return f"<td>{image}<small>{html.escape(topic or '–')} / {html.escape(stem or '–')}{extra}</small></td>"


def compare(count: int, model: str) -> Path:
    """Raport HTML: dla `count` najnowszych wpisów bez zdjęcia pokazuje wybór regexu i wybór modelu."""
    from .build import photo_candidates  # import tutaj: raport potrzebuje pakietów budowy

    site = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    texts = yaml.safe_load((ROOT / "i18n" / f"{site.get('lang', 'pl')}.yaml").read_text(encoding="utf-8"))
    topics = [(name, re.compile(pattern, re.I)) for name, pattern in (texts.get("topics") or {}).items()]
    pool = photo_pool(ROOT)
    files = {Path(name).stem: name for names in pool.values() for name in names}
    catalog = load_catalog(pool)
    items = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    entries = needs_photo(items, bool(site.get("source_images")))[:count]
    results, usage = classify(entries, catalog, model, max_calls=len(entries) // BATCH + 1)

    rows, changed = [], 0
    for entry in entries:
        old_topic = next((name for name, pattern in topics if pattern.search(entry["title"])), "")
        old_stem = Path(next(iter(photo_candidates(pool, old_topic, entry["id"])), "")).stem
        new = results.get(entry["id"])
        if new is None:
            new_cell = "<td><small>brak odpowiedzi → zostaje regex</small></td>"
        elif new["topic"] == NONE:
            new_cell = "<td><small>none: temat wrażliwy, bez zdjęcia z puli</small></td>"
        else:
            extra = "".join(f"<br>{label}: {html.escape(value)}" for label, value in (
                ("rezerwa", ", ".join(new["picks"][1:])), ("brakuje", new.get("missing", ""))) if value)
            new_cell = _cell(new["topic"], (new["picks"] or [""])[0], files, extra)
        changed += bool(new) and (new["topic"] != (old_topic or "general") or (new["picks"] or [""])[0] != old_stem)
        choice = "".join(f'<label><input type="radio" name="{entry["id"]}" value="{value}"> {label}</label>'
                         for value, label in (("r", "regex"), ("m", "model"), ("e", "bez różnicy")))
        rows.append(f'<tr><td><div class="t">{html.escape(entry["title"])}</div>'
                    f'<small>{html.escape(entry.get("source_name", ""))} · {entry["published"]}</small>'
                    f'<div>{html.escape(entry.get("lead") or "")}</div></td>'
                    f'{_cell(old_topic or "general", old_stem, files)}{new_cell}<td>{choice}</td></tr>')
    meta = (f"Serwis: {html.escape(site.get('title', ''))} · model: {html.escape(model)} · wpisów: {len(entries)} · "
            f"odpowiedzi: {len(results)} · inny wybór niż regex: {changed} · wywołań: {usage['calls']} · "
            f"tokeny: {usage['prompt_tokens']} wejście, {usage['completion_tokens']} wyjście"
            + (f" · uwagi: {html.escape('; '.join(usage['errors']))}" if usage["errors"] else ""))
    found = stats([{"photo_ai": value} for value in results.values()])
    summary = ("Grupy: " + ", ".join(f"{name} {number}" for name, number in found["topics"])
               + " · Brakujące zdjęcia: " + (", ".join(f"{name} {number}" for name, number in found["missing"]) or "–"))
    target = ROOT / "photo_ai_report.html"
    target.write_text(REPORT.format(meta=meta, summary=html.escape(summary), rows="\n".join(rows),
                                    count=len(entries)), encoding="utf-8")
    print(meta)
    print(summary)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Dobór ilustracji modelem AI")
    parser.add_argument("--compare", type=int, metavar="N", help="raport dla N najnowszych wpisów bez zdjęcia")
    parser.add_argument("--model", default=os.environ.get("PHOTO_AI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--prompt", action="store_true", help="wypisz prompt systemowy i zakończ")
    args = parser.parse_args()
    if args.prompt:
        print(system_prompt(load_catalog(photo_pool(ROOT))))
    elif args.compare:
        print(f"Raport: {compare(args.compare, args.model)}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
