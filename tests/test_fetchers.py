"""Testy adapterów na próbkach offline (bez sieci)."""
import unittest

from unittest import mock

from gn import fetch
from gn.build import photo_pool, pick_photo
from gn.fetch import add_images, merge
from gn.fetchers import html_links, rss, tribe_events
from gn.models import clean_lead
from gn.sudoku import count_solutions, daily

SOURCE = {"id": "t", "name": "Test", "category": "powiat",
          "url": "https://example.org/aktualnosci/wszystkie/", "link_pattern": r"/aktualnosci/\d+/?$"}

HTML_LIST = """
<html><body><nav><a href="/aktualnosci/wszystkie/">Aktualności</a></nav>
<div class="list">
  <div class="row"><a href="/aktualnosci/728"><img src="a.jpg" alt=""></a>
    <div><span>06.11.2026</span><h3><a href="/aktualnosci/728">Obchody Święta Niepodległości</a></h3>
    <p>Zapraszamy mieszkańców na uroczystości.</p><a href="/aktualnosci/728">czytaj więcej</a></div></div>
  <div class="row"><span class="d">30.10.2026</span>
    <a href="https://example.org/aktualnosci/727">Powiat dla zdrowia psychicznego</a></div>
</div>
<ul><li><a href="aktualnosci/726">28.10.2026 Informacje dla inwestorów giełdowych</a></li></ul>
</body></html>
"""

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>
<item><title>Turniej &amp; festyn</title><link>https://example.org/2026/09/10/turniej/</link>
<pubDate>Thu, 10 Sep 2026 14:03:30 +0000</pubDate>
<description><![CDATA[<p>Zapraszamy na <b>turniej</b>.</p>]]></description></item>
</channel></rss>"""


class HtmlLinksTest(unittest.TestCase):
    def setUp(self):
        self.items = {i.url.rsplit("/", 1)[-1]: i for i in html_links.parse(HTML_LIST, SOURCE)}

    def test_finds_only_article_links(self):
        self.assertEqual(sorted(self.items), ["726", "727", "728"])

    def test_title_date_lead(self):
        item = self.items["728"]
        self.assertEqual(item.title, "Obchody Święta Niepodległości")
        self.assertEqual(item.published, "2026-11-06")
        self.assertEqual(item.lead, "Zapraszamy mieszkańców na uroczystości.")

    def test_date_outside_anchor_and_inside_anchor(self):
        self.assertEqual(self.items["727"].published, "2026-10-30")
        self.assertEqual(self.items["726"].published, "2026-10-28")
        self.assertEqual(self.items["726"].title, "Informacje dla inwestorów giełdowych")


class StripTest(unittest.TestCase):
    def test_strips_cms_suffix(self):
        html = """<div><div class="n"><a href="/aktualnosci/728">Obchody Święta Niepodległości
        (Zam: 06.11.2026 r., godz. 12.00) 193</a><p>Zapraszamy na uroczystości.</p></div>
        <div class="n"><a href="/aktualnosci/727">Inny wpis powiatu (Zam: 30.10.2026 r., godz. 10.05) 224</a></div></div>"""
        source = dict(SOURCE, strip=[r"\(Zam:[^)]*\)\s*\d*"])
        first, second = html_links.parse(html, source)
        self.assertEqual(first.title, "Obchody Święta Niepodległości")
        self.assertEqual(first.published, "2026-11-06")
        self.assertEqual(first.lead, "Zapraszamy na uroczystości.")
        self.assertEqual(second.title, "Inny wpis powiatu")


GOV_LIST = """<html><body>
<nav><ul><li><a href="/web/kppsp-grodzisk-mazowiecki/kontakt">Kontakt z komendą</a></li>
<li><a href="/web/kppsp-grodzisk-mazowiecki/aktualnosci">Aktualności komendy</a></li></ul></nav>
<div class="art-prev"><ul>
<li><a href="/web/kppsp-grodzisk-mazowiecki/dzien-flagi"><picture><img src="x.jpg" alt=""></picture>
  <div><div class="event"><span class="date">02.05.2026</span></div>
  <div class="title">Dzień Flagi Rzeczypospolitej Polskiej</div>
  <div class="intro">Strażacy uczcili święto państwowe.</div></div></a></li>
<li><a href="/web/kppsp-grodzisk-mazowiecki/24-04-2026-polmaraton"><div><span class="date">24.04.2026</span>
  <div class="title">Mistrzostwa Polski w Półmaratonie Strażaków</div></div></a></li>
</ul></div><a href="/web/kppsp-grodzisk-mazowiecki/aktualnosci?page=2">2</a></body></html>"""


class GovListTest(unittest.TestCase):
    def test_require_date_and_title_class(self):
        source = dict(SOURCE, url="https://www.gov.pl/web/kppsp-grodzisk-mazowiecki/aktualnosci",
                      link_pattern=r"/web/kppsp-grodzisk-mazowiecki/[^/?#]+$", require_date=True)
        items = html_links.parse(GOV_LIST, source)
        self.assertEqual([i.title for i in items], ["Dzień Flagi Rzeczypospolitej Polskiej",
                                                    "Mistrzostwa Polski w Półmaratonie Strażaków"])
        self.assertEqual(items[0].published, "2026-05-02")
        self.assertEqual(items[0].lead, "Strażacy uczcili święto państwowe.")
        self.assertEqual(items[1].lead, "")


class EventsTest(unittest.TestCase):
    def test_parse_and_refresh(self):
        payload = """{"events": [
          {"url": "https://e.org/wydarzenie/a/", "title": "Koncert &#8211; dla dzieci", "start_date": "2026-11-15 13:00:00",
           "all_day": false, "excerpt": "", "description": "<p>Zapraszamy na koncert familijny.</p>", "venue": {"venue": "Mediateka"}},
          {"url": "https://e.org/wydarzenie/b/", "title": "Wystawa plakatu", "start_date": "2026-11-20 00:00:00",
           "all_day": true, "excerpt": "", "description": "", "venue": []}]}"""
        first, second = tribe_events.parse(payload, SOURCE)
        self.assertEqual(first.title, "Koncert – dla dzieci")
        self.assertEqual(first.event_date, "2026-11-15 13:00:00")
        self.assertEqual(first.lead, "Mediateka · Zapraszamy na koncert familijny.")
        self.assertEqual((second.lead, second.event_date), ("", "2026-11-20 00:00:00"))
        merged, _ = merge([], [first.to_dict()])
        moved = dict(first.to_dict(), event_date="2026-11-16 18:00:00")
        merged, added = merge(merged, [moved])
        self.assertEqual((added, merged[0]["event_date"]), (0, "2026-11-16 18:00:00"))


class LeadTest(unittest.TestCase):
    def test_empty_like_leads(self):
        self.assertEqual(clean_lead("."), "")
        self.assertEqual(clean_lead(" – "), "")
        self.assertEqual(clean_lead("Szczegóły na plakacie"), "Szczegóły na plakacie")


class SudokuTest(unittest.TestCase):
    def test_daily_is_valid_unique_and_stable(self):
        today = daily("2026-11-15")
        self.assertEqual(today, daily("2026-11-15"))
        self.assertNotEqual(today, daily("2026-11-16"))
        for level in today["levels"]:
            grid = [int(c) for c in level["puzzle"]]
            self.assertEqual(count_solutions(grid[:]), 1)
            self.assertTrue(all(p in ("0", s) for p, s in zip(level["puzzle"], level["solution"])))
            for unit in range(9):
                self.assertEqual(sorted(level["solution"][unit * 9:unit * 9 + 9]), list("123456789"))


OSIR_HOME = """<html><body>
<table class="cal"><tr><td><a href="/kalendarz-wydarzen/lotto-bogoria-vs-energia.html">LOTTO SUPERLIGA: Orlen Bogoria Grodzisk Mazowiecki VS. KS Energia TTCup</a></td>
<td><a href="/kalendarz-wydarzen/stand-up.html">Stand-UP w programie ATLAS</a></td></tr></table>
<div class="latest">
 <div class="ev"><span>18 - 11 - 2026</span> <span>Godz. 18:00</span>
   <a href="/kalendarz-wydarzen/lotto-bogoria-vs-energia.html">LOTTO SUPERLIGA: Orlen Bogoria Grodzisk Mazowiecki...</a></div>
 <div class="ev"><a href="/kalendarz-wydarzen/folk.html">13 - 12 - 2026 Godz. 17:00 Grodzisk Folk Festiwal - Górale na Mazowszu</a></div>
</div><a href="/kalendarz-wydarzen/">Kalendarz</a></body></html>"""


class EventLinksTest(unittest.TestCase):
    def test_events_from_listing(self):
        source = dict(SOURCE, url="https://grodzisksport.pl/", events=True,
                      link_pattern=r"grodzisksport\.pl/kalendarz-wydarzen/.+\.html$")
        items = {i.url.rsplit("/", 1)[-1]: i for i in html_links.parse(OSIR_HOME, source)}
        self.assertEqual(sorted(items), ["folk.html", "lotto-bogoria-vs-energia.html"])  # bez daty = pominięte
        match = items["lotto-bogoria-vs-energia.html"]
        self.assertEqual(match.event_date, "2026-11-18 18:00:00")
        self.assertEqual(match.title, "LOTTO SUPERLIGA: Orlen Bogoria Grodzisk Mazowiecki VS. KS Energia TTCup")
        self.assertEqual(items["folk.html"].title, "Grodzisk Folk Festiwal - Górale na Mazowszu")
        self.assertEqual(items["folk.html"].event_date, "2026-12-13 17:00:00")


VRM_LIST = """<html><body><div class="news">
 <div class="teaser"><h3>Förderbescheide an Landrat übergeben</h3><time>16.04.2026</time>
   <a href="https://extern.example/presse">Pressemitteilung</a></div>
 <div class="teaser"><h3>24 Buslinien starten ab dem 01.08.2026 mit neuen Betreibern</h3>
   <span>17. Juli 2026</span><p>Die Verträge laufen am 31.07.2026 aus.</p>
   <a href="/news/detailansicht/24-buslinien/">mehr erfahren</a></div>
</div></body></html>"""


class NeighbourAndDatesTest(unittest.TestCase):
    def test_keeps_dates_in_title_and_ignores_neighbour(self):
        source = dict(SOURCE, url="https://www.vrminfo.de/news/", require_date=True,
                      link_pattern=r"/news/detailansicht/[^/?#]+/$")
        (item,) = html_links.parse(VRM_LIST, source)
        self.assertEqual(item.title, "24 Buslinien starten ab dem 01.08.2026 mit neuen Betreibern")
        self.assertEqual(item.published, "2026-07-17")
        self.assertEqual(item.lead, "Die Verträge laufen am 31.07.2026 aus.")

    def test_merge_refreshes_title(self):
        old = dict(id="a", source="s", title="Kreisverwaltung bleibt am geschlossen", lead="", published="2026-11-01",
                   fetched_at="x")
        new = dict(old, title="Kreisverwaltung bleibt am 24.12.2026 geschlossen", published="2026-11-16")
        merged, added = merge([old], [new])
        self.assertEqual((added, merged[0]["title"], merged[0]["published"]),
                         (0, "Kreisverwaltung bleibt am 24.12.2026 geschlossen", "2026-11-01"))


class ImagesTest(unittest.TestCase):
    def test_rss_image_sources(self):
        feed = """<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"
          xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel><title>x</title>
        <item><title>Wpis ze zdjęciem w media</title><link>https://e.org/a</link>
          <media:content url="https://e.org/a.jpg" medium="image"/></item>
        <item><title>Wpis ze zdjęciem w treści</title><link>https://e.org/b</link>
          <content:encoded><![CDATA[<p><img src="https://s.w.org/emoji/1.svg"><img src="https://e.org/b.jpg"></p>]]></content:encoded></item>
        <item><title>Wpis bez zdjęcia w kanale</title><link>https://e.org/c</link></item></channel></rss>"""
        first, second, third = rss.parse(feed, SOURCE)
        self.assertEqual((first.image, second.image, third.image), ("https://e.org/a.jpg", "https://e.org/b.jpg", ""))
        self.assertNotIn("image", third.to_dict())

    def test_add_images_checks_each_item_once(self):
        items = [{"url": "https://e.org/1"}, {"url": "https://e.org/2", "image": ""},
                 {"url": "https://e.org/3", "event_date": "2026-11-20 10:00:00"}]
        page = '<html><head><meta property="og:image" content="/img/foto.jpg?a=1&amp;b=2"></head></html>'
        with mock.patch.object(fetch.http, "get", return_value=mock.Mock(text=page)) as get:
            self.assertEqual(add_images(items), 1)
            self.assertEqual(add_images(items), 0)
        self.assertEqual(get.call_count, 1)
        self.assertEqual(items[0]["image"], "https://e.org/img/foto.jpg?a=1&b=2")
        self.assertNotIn("image", items[2])


PROM_HOME = """<div class="repertuar_list">
<div class="repertuar_item"><div class="link"><a href="https://promkultury.pl/wydarzenie/sinatra-koncert/">
 <div class="repertuar_image"><img src="a.jpg" alt="" title="Sinatra – koncert"></div>
 <div class="repertuar_timeline"><p class="timeline">21.11.2026, 19:00</p></div>
 <div class="repertuar_content"><h3>Sinatra – Out of Lights koncert</h3><p>Portret muzyczny</p></div></a></div>
 <p class="ticket"><a href="https://bilety.promkultury.pl/rezerwacja/x.html?id=3102">KUP BILET</a></p></div>
<div class="repertuar_item"><div class="link"><a href="https://promkultury.pl/wydarzenie/kino-kepa-roza/">
 <div class="repertuar_timeline"><p class="timeline">22.11.2026, 18:00</p></div>
 <div class="repertuar_content"><h3>KINO KĘPA: Róża</h3><p>reż. Markus Schleinzer, Austria 2026, 94 min</p></div></a></div></div>
</div>"""

UM_LIST = """<ul><li><div class="t"><a href="https://pragapld.um.warszawa.pl/-/sesja-rady"><img src="x.png" alt="Znak">
 <h3>XL Sesja Rady Dzielnicy Praga-Południe</h3></a></div>
 <div><time datetime="2026-11-17 16:06:00">17.11.2026</time> <span> Artykuł </span></div>
 <p>W dniu 24 listopada 2026 roku o godz. 14:00 odbędzie się sesja.</p>
 <p>źródło: <a href="https://pragapld.um.warszawa.pl/-/sesja-rady"> pragapld.um.warszawa.pl </a></p></li>
<li><div class="t"><a href="https://pragapld.um.warszawa.pl/-/spacer-po-kepie"><h3>Spacer śladami architektury</h3></a></div>
 <div><time datetime="2026-11-13 14:57:00">13.11.2026</time> <span> Artykuł </span></div>
 <p>Zbiórka przy ul. Francuskiej, na Saskiej Kępie.</p>
 <p>źródło: <a href="https://pragapld.um.warszawa.pl/-/spacer-po-kepie"> pragapld.um.warszawa.pl </a></p></li></ul>"""


class SaskaTest(unittest.TestCase):
    def test_time_right_after_date(self):
        source = dict(SOURCE, url="https://promkultury.pl/", events=True,
                      link_pattern=r"promkultury\.pl/wydarzenie/[^/?#]+/?$")
        first, second = html_links.parse(PROM_HOME, source)
        self.assertEqual(first.title, "Sinatra – Out of Lights koncert")
        self.assertEqual(first.event_date, "2026-11-21 19:00:00")
        self.assertEqual(second.event_date, "2026-11-22 18:00:00")

    def test_district_list_and_include(self):
        source = dict(SOURCE, url="https://pragapld.um.warszawa.pl/aktualnosci", require_date=True,
                      link_pattern=r"pragapld\.um\.warszawa\.pl/-/[^/?#]+$",
                      strip=[r"\bArtykuł\b", r"źródło:\s*pragapld\.um\.warszawa\.pl"])
        items = html_links.parse(UM_LIST, source)
        self.assertEqual([i.published for i in items], ["2026-11-17", "2026-11-13"])
        self.assertTrue(items[0].lead.startswith("W dniu 24 listopada"))
        keep = fetch.include_pattern([r"sask\w+ kęp", "francusk"])
        self.assertEqual([i.title for i in items if keep.search(f"{i.title} {i.lead}")],
                         ["Spacer śladami architektury"])
        self.assertTrue(fetch.include_pattern("KĘPA").search("kino kępa"))


class PhotoPoolTest(unittest.TestCase):
    def test_groups_and_stable_choice(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "static" / "img" / "topics-photo"
            folder.mkdir(parents=True)
            for name in ("road-1.jpg", "road-2.PNG", "general-1.webp", "notatki.txt", "bus.jpg"):
                (folder / name).write_bytes(b"x")
            pool = photo_pool(Path(tmp))
        self.assertEqual(pool, {"general": ["general-1.webp"], "road": ["road-1.jpg", "road-2.PNG"]})
        self.assertIn(pick_photo(pool, "road", "abc"), pool["road"])
        self.assertEqual(pick_photo(pool, "road", "abc"), pick_photo(pool, "road", "abc"))
        self.assertEqual(pick_photo(pool, "", "abc"), "general-1.webp")   # brak tematu -> grupa ogólna
        self.assertEqual(pick_photo(pool, "cinema", "abc"), "general-1.webp")
        self.assertEqual(pick_photo({}, "road", "abc"), "")


class RssTest(unittest.TestCase):
    def test_parse(self):
        (item,) = rss.parse(RSS, SOURCE)
        self.assertEqual(item.title, "Turniej & festyn")
        self.assertEqual(item.published, "2026-09-10")
        self.assertEqual(item.lead, "Zapraszamy na turniej.")


class MergeTest(unittest.TestCase):
    def test_no_duplicates(self):
        fresh = [i.to_dict() for i in html_links.parse(HTML_LIST, SOURCE)]
        merged, added = merge([], fresh)
        self.assertEqual(added, 3)
        merged, added = merge(merged, fresh)
        self.assertEqual((len(merged), added), (3, 0))


if __name__ == "__main__":
    unittest.main()
