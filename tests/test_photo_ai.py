"""Testy doboru ilustracji modelem AI – bez sieci (odpowiedź modelu jest podstawiana)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gn import photo_ai
from gn.build import assign_photos, photo_candidates

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = [{"id": "a1", "title": "Skradziono rower sprzed sklepu", "lead": "Policja szuka sprawcy."},
           {"id": "b2", "title": "Dziki lokator w pustostanie", "lead": ""},
           {"id": "c3", "title": "Tragiczny wypadek na obwodnicy", "lead": ""}]
POOL = {"police": [f"police-{n}.jpg" for n in range(1, 7)], "general": ["general-1.jpg", "general-2.jpg"]}


class CatalogTest(unittest.TestCase):
    def test_catalog_matches_pool_files(self):
        catalog = photo_ai.load_catalog()
        described = {key for group in catalog.values() for key in group["scenes"]}
        for topic, group in catalog.items():
            self.assertRegex(topic, r"^[a-z]+$")  # nazwa grupy = początek nazwy pliku, same litery
            self.assertTrue(group.get("use"), topic)
            self.assertTrue(all(key.startswith(topic + "-") for key in group["scenes"]), topic)
        files = {Path(name).stem for names in photo_ai.photo_pool(ROOT).values() for name in names}
        if files:  # paczka z kodem nie zawiera obrazów; w repo sprawdzamy zgodność
            self.assertEqual(files - described, set(), "pliki bez opisu w photo_scenes.yaml")

    def test_catalog_limited_to_pool(self):
        catalog = photo_ai.load_catalog({"police": ["police-4.jpg"], "road": [], "xmas": []})
        self.assertEqual(list(catalog), ["police"])
        self.assertEqual(list(catalog["police"]["scenes"]), ["police-4"])

    def test_prompt_lists_only_available_scenes(self):
        prompt = photo_ai.system_prompt(photo_ai.load_catalog(POOL))
        self.assertIn("police-4: a bicycle locked", prompt)
        self.assertIn('"missing"', prompt)
        self.assertNotIn("[xmas]", prompt)


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.catalog = photo_ai.load_catalog()

    def parse(self, payload):
        text = payload if isinstance(payload, str) else json.dumps(payload)
        return photo_ai.parse_answer(text, ENTRIES, self.catalog)

    def test_valid_answer_with_code_fence(self):
        text = '```json\n{"items": [{"id": 1, "topic": "police", "picks": ["police-4", "police-5"]}]}\n```'
        self.assertEqual(self.parse(text), {"a1": {"topic": "police", "picks": ["police-4", "police-5"]}})

    def test_rejects_unknown_ids_topics_and_foreign_files(self):
        result = self.parse({"items": [
            {"id": 9, "topic": "police", "picks": ["police-1"]},           # numer spoza paczki
            {"id": 1, "topic": "crime", "picks": ["police-1"]},            # temat spoza katalogu
            {"id": "2", "topic": "general", "picks": ["boar-1", "general-4", "general-4", "general-99", 7]},
        ]})
        self.assertEqual(result, {"b2": {"topic": "general", "picks": ["general-4"]}})

    def test_none_and_pick_limit(self):
        result = self.parse({"items": [
            {"id": 3, "topic": "none", "picks": ["police-1"], "missing": "ambulance"},
            {"id": 1, "topic": "Police", "picks": ["police-4", "police-5", "police-1", "police-2"]},
        ]})
        self.assertEqual(result["c3"], {"topic": "none", "picks": []})
        self.assertEqual(result["a1"]["picks"], ["police-4", "police-5", "police-1"])

    def test_missing_is_cleaned(self):
        result = self.parse({"items": [
            {"id": 1, "topic": "general", "picks": [], "missing": " Squatted <b>House</b>! "},
            {"id": 2, "topic": "general", "picks": [], "missing": ["x"]},
        ]})
        self.assertEqual(result["a1"]["missing"], "squatted bhouseb")
        self.assertNotIn("missing", result["b2"])

    def test_truncated_answer_keeps_complete_items(self):
        text = ('{"items": [{"id": 1, "topic": "police", "picks": ["police-4"]},\n'
                ' {"id": 2, "topic": "general", "picks": ["general-1"]},\n {"id": 3, "topic": "no')
        self.assertEqual(list(self.parse(text)), ["a1", "b2"])

    def test_garbage_gives_empty_result(self):
        for text in ("", "Nie wiem.", '{"items": "x"}', '{"items": [1, null]}', "{broken", '{"id": 1, "picks": "x"}'):
            self.assertEqual(self.parse(text), {})


class ClassifyTest(unittest.TestCase):
    def test_failed_batch_does_not_stop_the_rest(self):
        catalog = photo_ai.load_catalog()
        entries = [{"id": f"e{n}", "title": "t", "lead": ""} for n in range(photo_ai.BATCH + 2)]
        answers = [RuntimeError("503"), ({"e25": {"topic": "road", "picks": []}}, {"prompt_tokens": 10})]
        with mock.patch.object(photo_ai, "ask", side_effect=answers):
            results, usage = photo_ai.classify(entries, catalog)
        self.assertEqual(list(results), ["e25"])
        self.assertEqual((usage["calls"], usage["prompt_tokens"], len(usage["errors"])), (2, 10, 1))
        self.assertEqual(usage["asked"], ["e25", "e26"])

    def test_call_limit(self):
        entries = [{"id": f"e{n}", "title": "t", "lead": ""} for n in range(photo_ai.BATCH * 3)]
        with mock.patch.object(photo_ai, "ask", return_value=({}, {})) as ask:
            photo_ai.classify(entries, photo_ai.load_catalog(), max_calls=2)
        self.assertEqual(ask.call_count, 2)

    def test_request_shape_and_missing_key(self):
        catalog = photo_ai.load_catalog()
        with mock.patch.dict("os.environ", {}, clear=True), self.assertRaises(RuntimeError):
            photo_ai.ask(ENTRIES, catalog)
        reply = mock.Mock()
        reply.json.return_value = {"choices": [{"message": {"content": None}, "finish_reason": "length"}],
                                   "usage": {"prompt_tokens": 5}}
        with mock.patch.object(photo_ai.requests, "post", return_value=reply) as post:
            found, usage = photo_ai.ask(ENTRIES, catalog, key="test")
        self.assertEqual(found, {})
        self.assertIn("finish_reason=length", usage["note"])
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["model"], photo_ai.DEFAULT_MODEL)
        self.assertIn("Skradziono rower", body["messages"][1]["content"])
        self.assertNotIn("a1", body["messages"][1]["content"])  # do modelu idzie numer, nie identyfikator
        self.assertGreaterEqual(body["max_tokens"], 4000)


class AnnotateTest(unittest.TestCase):
    """Zapis wyniku przy wpisach (`gn.fetch` woła `annotate` po pobraniu źródeł)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        folder = self.root / photo_ai.POOL_DIR
        folder.mkdir(parents=True)
        for name in ("police-4.jpg", "police-5.jpg", "general-1.jpg"):
            (folder / name).write_bytes(b"x")
        self.items = [
            {"id": "n1", "source": "s", "title": "Skradziono rower", "lead": "", "image": ""},
            {"id": "n2", "source": "s", "title": "Wypadek", "lead": "", "image": ""},
            {"id": "n3", "source": "s", "title": "Niejasny wpis", "lead": "", "image": ""},
            {"id": "ev", "source": "s", "title": "Koncert", "lead": "", "event_date": "2026-12-01 18:00:00"},
            {"id": "im", "source": "s", "title": "Ze zdjęciem", "lead": "", "image": "https://example.org/a.jpg"},
            {"id": "ok", "source": "s", "title": "Już oceniony", "lead": "", "image": "", "photo_ai": {"topic": "general"}},
        ]

    def test_without_key_nothing_changes(self):
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(photo_ai, "ask") as ask:
            message = photo_ai.annotate(self.items, self.root)
        ask.assert_not_called()
        self.assertIn("wyłączony", message)
        self.assertNotIn("photo_ai", self.items[0])

    def test_stores_answers_once(self):
        answer = ({"n1": {"topic": "police", "picks": ["police-4"], "missing": "bike"},
                   "n2": {"topic": "none", "picks": []}}, {"prompt_tokens": 100, "completion_tokens": 20})
        with mock.patch.dict("os.environ", {photo_ai.KEY_ENV: "k"}), \
                mock.patch.object(photo_ai, "ask", return_value=answer) as ask:
            message = photo_ai.annotate(self.items, self.root)
            asked = [entry["id"] for entry in ask.call_args.args[0]]
            photo_ai.annotate(self.items, self.root)  # drugi przebieg: nie ma już o co pytać
        self.assertEqual(asked, ["n1", "n2", "n3"])  # bez wydarzenia, wpisu ze zdjęciem i już ocenionego
        self.assertEqual(ask.call_count, 1)
        self.assertEqual(self.items[0]["photo_ai"], {"topic": "police", "picks": ["police-4"], "missing": "bike"})
        self.assertEqual(self.items[1]["photo_ai"]["topic"], "none")
        self.assertEqual(self.items[2]["photo_ai"], {"topic": "", "picks": []})  # pytany, bez poprawnej odpowiedzi
        self.assertIn("odpowiedzi 2", message)

    def test_failed_call_leaves_items_for_next_run(self):
        with mock.patch.dict("os.environ", {photo_ai.KEY_ENV: "k"}), \
                mock.patch.object(photo_ai, "ask", side_effect=RuntimeError("timeout")):
            message = photo_ai.annotate(self.items, self.root)
        self.assertNotIn("photo_ai", self.items[0])
        self.assertIn("timeout", message)

    def test_repeated_thumbnail_counts_as_no_photo(self):
        items = [{"id": str(n), "source": "s", "title": "t", "image": "https://example.org/logo.png"} for n in range(3)]
        self.assertEqual(len(photo_ai.needs_photo(items, True)), 3)   # logo źródła, nie zdjęcie artykułu
        self.assertEqual(len(photo_ai.needs_photo(items[:2], True)), 0)
        self.assertEqual(len(photo_ai.needs_photo(items[:2], False)), 2)  # serwis bez miniatur (Boppard)

    def test_stats(self):
        found = photo_ai.stats([{"photo_ai": {"topic": "police", "missing": "bike"}}, {"photo_ai": {"topic": "police"}},
                                {"photo_ai": {"topic": ""}}, {"photo_ai": {"topic": "none"}}, {}])
        self.assertEqual(found, {"asked": 3, "topics": [("police", 2), ("none", 1)], "missing": [("bike", 1)]})


class BuildUsesPicksTest(unittest.TestCase):
    def entry(self, key, **extra):
        return {"id": key, "image": "", "event_date": "", "category": "miasto", "topic": "police", **extra}

    def test_picks_go_first_then_rest_of_group_then_general(self):
        order = photo_candidates(POOL, "police", "abc", ["police-4", "police-9", "police-2"])
        self.assertEqual(order[:2], ["police-4.jpg", "police-2.jpg"])
        self.assertEqual(sorted(order), sorted(POOL["police"] + POOL["general"]))
        self.assertEqual(order[-2:][0][:7], "general")
        self.assertEqual(photo_candidates(POOL, "police", "abc"), photo_candidates(POOL, "police", "abc", []))

    def test_no_repeats_rule_wins_over_first_pick(self):
        first, second = self.entry("a", picks=["police-4", "police-5"]), self.entry("b", picks=["police-4", "police-5"])
        assign_photos(POOL, [first, second], [])
        self.assertEqual((first["pool_file"], second["pool_file"]), ("police-4.jpg", "police-5.jpg"))

    def test_sensitive_entry_gets_no_pool_photo(self):
        entry = self.entry("a", topic="", no_pool=True)
        assign_photos(POOL, [entry], [])
        self.assertEqual(entry["pool_file"], "")


if __name__ == "__main__":
    unittest.main()
