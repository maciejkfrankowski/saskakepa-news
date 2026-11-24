# Rozbudowa puli ilustracji — lista do wygenerowania (2026-11-24)

Lista powstała z przeglądu 255 wpisów bez własnego zdjęcia w trzech serwisach (Grodzisk 45, Saska Kępa 10,
Boppard 200) — tych samych, na których działał test z 24.11. Pokazuje tematy, dla których dzisiejsza pula
nie ma pasującej sceny, oraz grupy, w których 6 scen to za mało przy liczbie wpisów.

Stan: **opisy scen są już w `gn/photo_scenes.yaml`**; scena zaczyna działać, gdy plik o podanej nazwie trafi do
`static/img/topics-photo/`. Nie trzeba generować wszystkiego naraz ani pełnych szóstek.

## Jak generować

Prompt jak dotąd (`03-pula-zdjec-ai.md`): stały początek, scena z tabeli, stałe zakończenie.

- Początek: `Photorealistic editorial stock photograph of`
- Zakończenie: `Small Central European town setting, natural light, 35mm lens, shallow depth of field, muted natural colours, landscape format 16:9. No text, no letters, no signs with writing, no logos, no flags, no recognizable faces, no uniforms with insignia.`
- Nazwa pliku dokładnie jak w tabeli, np. `meeting-1.jpg`. Zasady treści bez zmian (bez napisów, logo, twarzy, rozpoznawalnych miejsc).
- Jeśli obraz wyjdzie inny niż opis, popraw linię w `gn/photo_scenes.yaml` — model wybiera po opisie, nie po obrazie.
- Uwaga na sceny z cyframi i symbolami: wodomierz (`water-7`), zegar (`notice-8`), terminal płatniczy (`money-6`) — odrzucaj wersje z czytelnym tekstem.

## Priorytet 1 — częste we wszystkich serwisach

### meeting — szkolenia, konsultacje, spotkania informacyjne (np. „Szkolenie z kwalifikowanej pierwszej pomocy”, „Netzwerktreffen”, „Infoveranstaltung”)

| Plik | Scena |
|---|---|
| meeting-1 | a circle of empty chairs in a bright community room |
| meeting-2 | a blank flipchart on a stand next to a row of chairs |
| meeting-3 | a seminar room with tables in a U-shape, blank notepads and pens |
| meeting-4 | coffee cups and a thermos on a side table in a meeting room |
| meeting-5 | a blank projector screen in a small lecture hall with empty seats |
| meeting-6 | blank sticky notes and markers spread on a table |

### award — wyróżnienia, jubileusze, plebiscyty (np. „Wybierz Laureatkę…”, „91 Feuerwehrangehörige … ausgezeichnet”, „Freiherr-vom-Stein-Plakette”)

| Plik | Scena |
|---|---|
| award-1 | a plain glass trophy on a wooden table |
| award-2 | a bouquet of flowers next to a blank framed certificate |
| award-3 | a plain medal in an open presentation box |
| award-4 | two hands shaking, close-up, blurred hall behind |
| award-5 | a lectern with a microphone and flowers on an empty stage |
| award-6 | a plain golden cup on a shelf |

### kids — place zabaw, pikniki rodzinne, przedszkola (np. „Otwarcie Placu Zabaw w Kozerach Nowych”, „PIKNIK RODZINNY”, „Kita Weiler: Laternenvernissage”)

| Plik | Scena |
|---|---|
| kids-1 | an empty playground with swings and a slide |
| kids-2 | a sandbox with a bucket and a spade |
| kids-3 | colourful abstract chalk drawings on a pavement |
| kids-4 | glowing paper lanterns on sticks at dusk |
| kids-5 | soap bubbles floating in a park |
| kids-6 | a child's bicycle with training wheels leaning on a fence |

### build — budowy i remonty budynków (np. „Remont dachu”, „Richtfest: Kommunal-Akademie”, „Baugrundstück in Udenhausen”)

| Plik | Scena |
|---|---|
| build-1 | scaffolding on the facade of a townhouse |
| build-2 | a tower crane above a building site, seen from a distance |
| build-3 | a roof under renovation with stacks of new tiles |
| build-4 | a concrete mixer and a pallet of bricks on a building site |
| build-5 | the timber roof frame of a new building against the sky |
| build-6 | an empty fenced building plot with surveying stakes |

### nature — środowisko, lasy, susza, polowania (np. „Piknik ekologiczny”, „Szkody spowodowane przez suszę”, „Treibjagd … Traumschleife meiden”)

| Plik | Scena |
|---|---|
| nature-1 | a forest path in autumn |
| nature-2 | freshly planted young trees with stakes in a park |
| nature-3 | dry cracked soil in a field |
| nature-4 | a wooden hunting high seat at the edge of a forest |
| nature-5 | a wildflower meadow with a bee on a flower |
| nature-6 | hands holding a seedling with soil |

### seniors — seniorzy, opieka, zajęcia ruchowe (np. „Aktiv und Fit”, „Sprechstunde-Plaudercafé mit der Gemeindeschwesterplus”, „Krajowy Trening Rodzinny”)

| Plik | Scena |
|---|---|
| seniors-1 | two cups of coffee and a board game on a table in a day room |
| seniors-2 | a walking stick leaning against a park bench |
| seniors-3 | exercise mats and light dumbbells in a community hall |
| seniors-4 | knitting needles and wool on an armchair |
| seniors-5 | two elderly people walking in a park, seen from behind at a distance |
| seniors-6 | a teapot and biscuits on a lace tablecloth |

### work — praca, targi pracy, przedsiębiorcy (np. „XXV Grodziskie Targi Pracy”, „Azubikalender”, „Netzwerktreffen für Gründer*innen”)

| Plik | Scena |
|---|---|
| work-1 | rows of empty tables and chairs in a job-fair hall |
| work-2 | a tool belt and work gloves on a workbench |
| work-3 | a laptop, a blank notebook and a hard hat on a desk |
| work-4 | a handshake over a desk, close-up |
| work-5 | a carpenter's hands planing a wooden board |
| work-6 | a small office with empty desks and chairs |

### animals — zwierzęta (np. „Informacja o wściekliźnie wśród lisów”, „Szczepienie lisów”, „Chroń zwierzęta w upały!”)

| Plik | Scena |
|---|---|
| animals-1 | a fox at the edge of a forest at dusk |
| animals-2 | a dog on a leash on a pavement, seen from behind |
| animals-3 | a cat sitting on a windowsill |
| animals-4 | a bowl of water for animals on a pavement in summer |
| animals-5 | a pet carrier and a stethoscope on a vet's table |
| animals-6 | a hedgehog in autumn leaves |

### xmas — jarmarki i wydarzenia świąteczne (np. „Bopparder Weihnachtsmarkt 2026”, „Musik und Poesie zur Weihnachtszeit”); w grudniu dojdzie tego więcej

| Plik | Scena |
|---|---|
| xmas-1 | fir branches with warm fairy lights, soft bokeh |
| xmas-2 | a wooden market stall with string lights on a snowy evening |
| xmas-3 | baubles on a Christmas tree, close-up |
| xmas-4 | mugs of mulled wine on a wooden counter |
| xmas-5 | an Advent wreath with burning candles |
| xmas-6 | a decorated Christmas tree on a small town square at dusk |

## Priorytet 2 — głównie Boppard

### hiking — szlaki i turystyka, głównie Boppard (np. „TV-Wanderer erleben …”, „Traumschleife Fünfseenblick”, „Sesselbahn Boppard”)

| Plik | Scena |
|---|---|
| hiking-1 | hiking boots on a rocky viewpoint above a river valley |
| hiking-2 | a wooden trail signpost with blank arrows in a forest |
| hiking-3 | a path through vineyards on a hillside |
| hiking-4 | a backpack and trekking poles leaning against a bench |
| hiking-5 | a chairlift above a wooded hillside |
| hiking-6 | a wooden bench at a viewpoint over hills |

### garden — BUGA29 i zieleń, głównie Boppard (ok. 30 wpisów o BUGA, np. „BUGA-Staudenmix: Pflanzworkshop”, „Mittelrheinkirsche: Baumverkaufsaktion”)

| Plik | Scena |
|---|---|
| garden-1 | flower beds in a riverside park |
| garden-2 | a hand trowel and potted perennials ready for planting |
| garden-3 | a watering can among flowers |
| garden-4 | a cherry tree in blossom |
| garden-5 | butterflies on lavender |
| garden-6 | gardening gloves and secateurs on a wooden crate |

### food — kulinaria i wino (np. „Internationaler Kochabend”, „Weinfestival Koblenz 2026”)

| Plik | Scena |
|---|---|
| food-1 | wine glasses on a table with a vineyard behind |
| food-2 | a pot and a wooden spoon on a stove |
| food-3 | a long table set with shared dishes |
| food-4 | fresh bread and cheese on a wooden board |
| food-5 | chopped vegetables on a cutting board |
| food-6 | ripe grapes on a vine |

### bike — rowery (np. „Fuß- und Radwegebrücke über die Lahn”, „Welterbe per E-Bike”, „VorTour der Hoffnung”)

| Plik | Scena |
|---|---|
| bike-1 | an empty cycle path along a river |
| bike-2 | bicycles parked in a rack |
| bike-3 | a bicycle handlebar and bell, close-up |
| bike-4 | a cyclist on a riverside path, seen from behind at a distance |
| bike-5 | a bike pump and repair tools on the ground |
| bike-6 | a helmet hanging on bicycle handlebars |

## Priorytet 3 — rzadsze albo sezonowe

### winter — śnieg, odśnieżanie, sezon grzewczy; w danych jeszcze brak (jest listopad), dodane z wyprzedzeniem

| Plik | Scena |
|---|---|
| winter-1 | a snow shovel leaning against a wall by a cleared pavement |
| winter-2 | a snow-covered street with tyre tracks in the morning |
| winter-3 | frost patterns on a window pane |
| winter-4 | a grit bin by a snowy roadside |
| winter-5 | a radiator with a thermostat under a window |
| winter-6 | icicles hanging from a roof gutter |

### farm — rolnictwo i dożynki (np. „Dożynki gminne”, „Szkody … w uprawach owoców i warzyw”)

| Plik | Scena |
|---|---|
| farm-1 | a harvest wreath made of grain ears |
| farm-2 | hay bales on a stubble field |
| farm-3 | crates of apples in an orchard |
| farm-4 | a tractor on a field track, no markings |
| farm-5 | a basket of vegetables on a market table |
| farm-6 | a loaf of bread and grain ears on a linen cloth |

### energy — prąd, gaz, ogrzewanie (np. „Informacja PGE”, „Auftrag für Gasbelieferung”)

| Plik | Scena |
|---|---|
| energy-1 | power lines and a pylon against the sky |
| energy-2 | a household fuse box with switches, no labels |
| energy-3 | a glowing light bulb |
| energy-4 | solar panels on a tiled roof |
| energy-5 | a burning gas hob |
| energy-6 | a street lamp lit at dusk |

### money — finanse i dotacje (np. „Manipulacja instrumentami finansowymi…”, „Haushaltsentwurf 2027”, „Förderbescheide”)

| Plik | Scena |
|---|---|
| money-1 | stacks of coins on a table |
| money-2 | a calculator and a pen on blank sheets |
| money-3 | a piggy bank on a windowsill |
| money-4 | an open wallet with coins |
| money-5 | a hand dropping a coin into a glass jar |
| money-6 | a payment terminal and a plain card on a counter |

### digital — usługi online i kursy komputerowe (np. „EDV und neue Medien”, „Aktionsmonat Cybersicherheit”, „VRM Fahrplan-App”)

| Plik | Scena |
|---|---|
| digital-1 | hands typing on a laptop keyboard |
| digital-2 | a hand holding a smartphone with a blank screen |
| digital-3 | a small padlock lying on a laptop keyboard |
| digital-4 | a wifi router with glowing lights |
| digital-5 | a tablet with a blank screen on a desk next to glasses |
| digital-6 | a computer mouse and network cables on a desk |

### alert — ostrzeżenia i sytuacje kryzysowe (np. „Bundesweiter Warntag”, „Umweltschaden nach Dieselaustritt”, „Waldbrandübung”)

| Plik | Scena |
|---|---|
| alert-1 | a warning siren on a rooftop against the sky |
| alert-2 | dark storm clouds over town rooftops |
| alert-3 | sandbags stacked by a doorway |
| alert-4 | an orange warning lamp on a road barrier |
| alert-5 | a torch, a battery radio and water bottles on a table |
| alert-6 | a flooded riverside path with a barrier |

## Dodatkowe sceny w istniejących grupach

### bus — w Grodzisku co czwarty wpis bez zdjęcia to zmiana rozkładu lub trasy autobusu

| Plik | Scena |
|---|---|
| bus-7 | a bus stop pole with a blank sign beside a road |
| bus-8 | a ticket validator on a pole inside a bus |
| bus-9 | a row of buses parked at a depot, no markings |

### notice — zamknięcia urzędów i zmiany godzin (np. „Kreisverwaltung bleibt … geschlossen”, „Zmiana godzin pracy”)

| Plik | Scena |
|---|---|
| notice-7 | a closed office door with an empty sign holder |
| notice-8 | a wall clock without numerals above an empty waiting room |
| notice-9 | a stack of folders and a rubber stamp on a desk |

### health — pierwsza pomoc, zdrowie psychiczne (np. „11 nowych ratowników”, „Powiat Grodziski dla zdrowia psychicznego”)

| Plik | Scena |
|---|---|
| health-7 | a first-aid training manikin on a mat in a hall |
| health-8 | bandage rolls and plasters laid out on a table |
| health-9 | an armchair and a box of tissues in a quiet counselling room |

### water — w Boppard kilkanaście wpisów wodociągów (wodomierze, pompownie, przetargi)

| Plik | Scena |
|---|---|
| water-7 | a household water meter on a pipe in a cellar, dial out of focus |
| water-8 | a water tower on a hill above a small town |
| water-9 | pumps and blue pipes inside a waterworks station |

### sport — w Boppard piłka nożna co tydzień, do tego wioślarstwo i ju-jutsu

| Plik | Scena |
|---|---|
| sport-7 | close-up of a goal net on a grass football pitch |
| sport-8 | football boots and shin pads on a changing-room bench |
| sport-9 | rowing boats stored on racks by a river |
| sport-10 | oars and a rowing boat on calm water at a jetty |
| sport-11 | a folded martial-arts jacket with a black belt on a mat |
| sport-12 | a referee's whistle and a stopwatch on a bench |

### stage — programy miesięczne domów kultury, jazz, wernisaże (Saska Kępa)

| Plik | Scena |
|---|---|
| stage-7 | a saxophone on a stand in a dim jazz club |
| stage-8 | a drum kit and amplifiers on a small stage |
| stage-9 | an easel with brushes and paint tubes in a studio |

## Podsumowanie

- Nowych grup: 19 (po 6 scen), dodatkowych scen w istniejących grupach: 21; razem 135 obrazów.
- Sam priorytet 1 to 54 obrazy i obejmuje tematy, które w przeglądzie najczęściej nie miały pasującej sceny.
- Po włączeniu doboru strona `/zrodla/` pokaże, jakich zdjęć modelowi najczęściej brakowało — to źródło do kolejnej rundy.
- Pula 114 → do 249 obrazów; prompt modelu rośnie proporcjonalnie (koszt nadal poniżej 2 zł miesięcznie).
