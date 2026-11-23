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

## Rozszerzenie z arkusza Marka (23.11.2026, `baza_zrodel_saskiej_kepy.xlsx`, 32 pozycje)

Dodane do `sources.yaml` (odczytane narzędziem Claude 23.11; z GitHub Actions jeszcze nietestowane):

| id | Źródło | Adres | Adapter | Uwagi |
|---|---|---|---|---|
| biblioteka | Biblioteka Publiczna im. Z. J. Rumla | https://bppragapd.pl/feed/ | rss + include | 10 wpisów w kanale, aktywny; filie w całej dzielnicy, tytuły zwykle zawierają adres filii |
| zdm | Zarząd Dróg Miejskich | https://zdm.waw.pl/aktualnosci/ | html_links + include | 9 wpisów na stronę, bez dat i opisów (data = dzień pobrania); struktura HTML niesprawdzona; kanał `/feed/` nie odpowiada |
| zielen | Zarząd Zieleni | https://zzw.waw.pl/feed/ | rss + include | kanał główny aktywny (zamiast martwego kanału tagu „Park Skaryszewski”) |
| samorzad | Samorząd Mieszkańców Saskiej Kępy | https://saska.kepa.warszawa.pl/feed/ | rss | bardzo mało wpisów (ostatni z maja 2026), część to odsyłacze do prasy |
| parafia-atenska | Parafia Miłosierdzia Bożego | https://atenska12.pl/feed/ | rss + exclude_title | aktywny; cotygodniowe „Ogłoszenia parafialne” odfiltrowane |
| parafia-nobla | Parafia MB Nieustającej Pomocy | https://nobla16.pl/ | html_links, wyłączone | wpisy `intro.php?display=blog_caly_wpis&blog_id=N`, tytuły to nazwy niedziel; do decyzji |

Urząd dzielnicy oznaczony `enabled: false` (403 z GitHub Actions).

Odrzucone z arkusza:

| Źródło | Powód |
|---|---|
| Centrum Promocji Kultury (cpk.art.pl) | kanał RSS martwy (ostatni wpis sierpień 2025) |
| DK Orion / SBM Ateńska | kanał zawiera tylko ogłoszenia spółdzielni (windy, lokale), brak wydarzeń domu kultury |
| SaskaKepa.info | kanał to katalog firm (sklepy, usługi), nie wiadomości |
| Mieszkaniec, Tu Stolica | media komercyjne – nie pobieramy treści |
| OSiR Praga-Południe, ZGN Praga-Południe | strony nie odpowiedziały narzędziu (portal sportowy miasta jest na tej samej platformie co urząd) |
| Dom Białoruski, Liceum Francuskie | brak dat lub nieaktualne wpisy |
| Szkoły (SP 143, 168, 373, ITSW) | strony na platformach szkolnych bez kanału; nie sprawdzano |
| BIP, Warszawa 19115 | ogólnomiejskie, bez możliwości zawężenia do osiedla |
| Pozycje z samym Facebookiem (Dzielnia, Święto Saskiej Kępy, Caritas, fundacja) | Facebooka nie pobieramy |
