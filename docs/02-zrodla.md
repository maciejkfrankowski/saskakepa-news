# 02 – Katalog źródeł (stan: 2026-11-22)

Saska Kępa to osiedle w dzielnicy Praga-Południe, a nie gmina: większość źródeł publicznych pisze
o całej dzielnicy lub całej Warszawie. Dlatego źródła dzielnicowe mają filtr `include` – wspólną listę
słów-kluczy `okolica` na początku `sources.yaml` (nazwa osiedla, ulice, park, mosty, stadion).

## Wdrożone w `sources.yaml`

| id | Źródło | Adres | Adapter | Stan sprawdzenia |
|---|---|---|---|---|
| prom | PROM Kultury – aktualności | https://promkultury.pl/feed/ | rss | kanał odczytany 22.11.2026 (ok. 1–2 wpisy/mies.) |
| prom-wydarzenia | PROM Kultury – repertuar | https://promkultury.pl/ | html_links + events | sprawdzone na zapisanej stronie; 6 najbliższych wydarzeń, lista rośnie z każdym przebiegiem |
| urzad | Urząd Dzielnicy Praga-Południe | https://pragapld.um.warszawa.pl/aktualnosci | html_links + include | sprawdzone na zapisanej stronie; z 20 wpisów filtr przepuszcza zwykle 0–1 |
| narodowy | PGE Narodowy | https://feeds.feedburner.com/stadionnarodowy | rss | kanał odczytany 22.11.2026; relacje zdjęciowe odfiltrowane |
| policja | KRP Warszawa VII | https://praga-poludnie.policja.gov.pl/r7/aktualnosci | html_links + include | ten sam system co policja w Grodzisku; nietestowane z GitHub Actions |

Żadne źródło nie było jeszcze pobierane z serwerów GitHub Actions – pierwszy przebieg pokaże stan na `/zrodla/`.

## Odrzucone lub odłożone

| Źródło | Adres | Powód |
|---|---|---|
| Zarząd Zieleni – tag „Park Skaryszewski” | https://zzw.waw.pl/tag/park-skaryszewski/feed/ | kanał działa, ale ostatni wpis z grudnia 2022 |
| PROM Kultury – pełny repertuar | https://promkultury.pl/wydarzenia/ | kalendarz miesięczny bez listy wpisów; wymagałby osobnego adaptera |
| Rada Dzielnicy – eSesja | https://pragapoludnie.esesja.pl/ | nieodczytane; zapowiedzi sesji są w aktualnościach urzędu |
| Komunikacja miejska | https://www.wtp.waw.pl/zmiany/ , https://ztm.waw.pl | nieodczytane; wymaga filtra po liniach i ulicach |
| Warszawa 19115 | https://warszawa19115.pl/powiadomienia | nieodczytane |
| saskakepa.info, pragapld.waw.pl | – | operator i charakter nieustalone |

## Do ustalenia
Biblioteka Publiczna im. Z. J. Rumla (filie na Saskiej Kępie), OSiR Praga-Południe, ZDM, Tramwaje Warszawskie,
MPWiK, Święto Saskiej Kępy, szkoły, parafie, kluby sportowe.

## Nie pobieramy
Serwisy komercyjne i prywatne: saskakepa.waw.pl, twoja-praga.pl, agregatory wydarzeń, prasa.
