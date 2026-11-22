# CLAUDE.md – zasady pracy w repo saskakepa-news

## Cel
Statyczny serwis lokalnych wiadomości i prostej rozrywki dla Saskiej Kępy (Warszawa, dzielnica Praga-Południe).
Etap: demo na darmowej infrastrukturze (GitHub Actions + Pages). Docelowo możliwa migracja na VPS.

## Zasady
- Dokumentacja i komunikaty po polsku; identyfikatory w kodzie po angielsku.
- Najpierw aktualizacja `docs/`, potem kod.
- Brak backendu: stan trzymamy w repo (`data/*.json`, `content/articles/*.md`).
- Wpisy zewnętrzne: tylko tytuł, krótki lead (≤220 znaków), data i link do źródła.
  Nie kopiujemy pełnych treści ani zdjęć. Mediów komercyjnych nie pobieramy.
- Każde źródło = wpis w `sources.yaml`. Nowy adapter tylko wtedy, gdy istniejące nie wystarczą.
- Paczki z poprawkami zawierają wyłącznie kod. Nigdy: `data/`, `content/`, `static/img/uploads/`,
  `static/img/topics-photo/`,
  `site.yaml`, `sources.yaml`, `admin/config.yml` – te pliki żyją w repo (bot, redakcja, edycje na GitHubie).
  Zmiany w konfiguracji przekazujemy jako fragment do wklejenia.
- Adapter ma funkcję `parse(content, source) -> list[Item]` (testowalna offline) i `fetch(source)`.
- Błąd jednego źródła nie może przerwać przebiegu; wynik trafia do `data/status.json`.
- Linki w szablonach zawsze przez zmienną `root` (serwis działa w podkatalogu `/saskakepa-news/`).
- Wygląd: wariant zielony (wspólny z grodzisk-news) (zmienne w `:root` w `static/style.css`). Główny blok: zdjęcie artykułu
  z zielonym przyciemnieniem albo – bez zdjęcia – rysowana panorama `static/img/panorama.svg`.
  Kafelki bez zdjęć: pastel w kolorze kategorii. Zdjęcia podpisujemy polem `image_credit` („Fot. …”).
- Front bez frameworków i bez zewnętrznych bibliotek; JS w `static/app.js`.
- Przed commitem: `python -m unittest discover -s tests && python -m gn.build`.

## Mapa
| Ścieżka | Rola |
|---|---|
| `sources.yaml` | katalog źródeł |
| `site.yaml` | nazwa, kategorie, slot reklamowy, e-mail kontaktowy |
| `gn/fetch.py` | pobieranie + scalanie z `data/items.json` |
| `gn/fetchers/` | adaptery `rss`, `html_links`, `tribe_events`, klient HTTP |
| `gn/sudoku.py`, `static/sudoku.js` | generator i gra „Sudoku dnia” |
| `gn/build.py` | generator `dist/` |
| `templates/`, `static/` | szablony Jinja2, CSS, JS |
| `static/img/topics-photo/` | pula zdjęć ilustracyjnych (pliki wgrywa redakcja; opis w `docs/03-pula-zdjec-ai.md`) |
| `content/articles/` | własne artykuły (Markdown + YAML) |
| `content/krzyzowki/` | gotowe krzyżówki jako samodzielne pliki HTML |
| `admin/` | panel redakcji: Sveltia CMS (wersja przypięta w `index.html`), pola w `config.yml` |
| `.github/workflows/build.yml` | cron, commit danych, deploy Pages |

## Otwarte
- Potwierdzić, że źródła nie blokują adresów IP GitHub Actions (strona `/zrodla/`).
- Kategorie w `admin/config.yml` trzeba zmieniać razem z `site.yaml`.
- Logowanie do panelu dla osób bez konta GitHub (wymaga pośrednika OAuth) – na później.
- Większość źródeł obejmuje całą dzielnicę: filtr `include` (lista `okolica` w `sources.yaml`).
- Kod wspólny z `grodzisk-news` i `boppard-news` – poprawki przenosić do wszystkich trzech.
