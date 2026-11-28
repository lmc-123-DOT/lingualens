"""Data-integrity and detector smoke tests for the 24-language grammar atlas.

Run with:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import re
import unittest
import urllib.request

from core.grammar import all_library, analyze
from core.languages import GRAMMAR_LANGUAGE_ORDER, LANGUAGES
from core.text import detect_language
from grammar_data import ALL_ENTRIES, GRAMMAR


REQUIRED = (
    "id", "language", "title", "english", "category", "cefr",
    "formula", "summary", "sections", "examples",
)


class GrammarLibraryTests(unittest.TestCase):
    def test_no_duplicate_ids(self):
        self.assertEqual(len(GRAMMAR), len(ALL_ENTRIES))

    def test_every_entry_is_complete(self):
        for entry in ALL_ENTRIES:
            with self.subTest(entry=entry["id"]):
                for key in REQUIRED:
                    self.assertIn(key, entry)
                self.assertTrue(entry["id"].startswith(entry["language"] + "-"))
                self.assertIn(entry["language"], GRAMMAR_LANGUAGE_ORDER)
                self.assertGreaterEqual(len(entry["sections"]), 1)
                self.assertGreaterEqual(len(entry["examples"]), 1)
                for example in entry["examples"]:
                    self.assertTrue(example.get("source"))
                    self.assertTrue(example.get("translation"))
                for link in entry.get("links", []):
                    self.assertTrue(link.get("url", "").startswith("http"))
                    self.assertTrue(link.get("label"))
                for pattern in entry.get("patterns", []):
                    re.compile(pattern, re.I)

    def test_samples_match_their_patterns(self):
        for entry in ALL_ENTRIES:
            patterns = entry.get("patterns") or []
            if not patterns:
                continue
            with self.subTest(entry=entry["id"]):
                sample = entry.get("sample", "")
                self.assertTrue(sample)
                self.assertTrue(
                    any(re.search(pattern, sample, re.I) for pattern in patterns),
                    f"{entry['id']} sample does not match its own patterns",
                )

    def test_samples_are_detected_by_the_analyzer(self):
        for entry in ALL_ENTRIES:
            if not entry.get("patterns"):
                continue
            with self.subTest(entry=entry["id"]):
                result = analyze(entry["sample"], entry["language"])
                ids = {point["id"] for point in result["points"]}
                self.assertIn(entry["id"], ids)

    def test_every_language_has_a_library(self):
        counts = {}
        for entry in ALL_ENTRIES:
            counts[entry["language"]] = counts.get(entry["language"], 0) + 1
        for code in GRAMMAR_LANGUAGE_ORDER:
            with self.subTest(language=code):
                self.assertGreaterEqual(counts.get(code, 0), 3, f"{code} has too few entries")

    def test_all_library_is_ordered_and_unique(self):
        library = all_library()
        self.assertEqual(len(library), len(GRAMMAR))
        self.assertEqual(len({entry["id"] for entry in library}), len(library))


class DetectionTests(unittest.TestCase):
    CASES = {
        "en": "The book that I bought yesterday was written by a teacher who lives in London.",
        "zh-CN": "这本书是我昨天在书店买的，读起来很有意思。",
        "ja": "昨日買った本はとても面白かったので、友達にも勧めました。",
        "ko": "어제 산 책이 아주 재미있어서 친구에게도 추천했습니다.",
        "es": "El libro que compré ayer es muy interesante y se lo recomendé a mi amiga.",
        "fr": "Le livre que j'ai acheté hier est très intéressant et je l'ai recommandé à ma sœur.",
        "de": "Das Buch, das ich gestern gekauft habe, ist sehr interessant und ich habe es meiner Schwester empfohlen.",
        "pt": "O livro que comprei ontem é muito interessante e recomendei-o à minha irmã.",
        "it": "Il libro che ho comprato ieri è molto interessante e l'ho consigliato a mia sorella.",
        "ru": "Книга, которую я купил вчера, очень интересная, и я посоветовал её сестре.",
        "uk": "Книга, яку я купив учора, дуже цікава, і я порадив її сестрі.",
        "pl": "Książka, którą kupiłem wczoraj, jest bardzo ciekawa i poleciłem ją siostrze.",
        "ar": "الكتاب الذي اشتريته أمس ممتع جدا وقد أوصيت به لأختي.",
        "fa": "کتابی که دیروز خریدم بسیار جالب است و آن را به خواهرم توصیه کردم.",
        "he": "הספר שקניתי אתמול מעניין מאוד והמלצתי עליו לאחותי.",
        "tr": "Dün aldığım kitap çok ilginç ve onu kız kardeşime tavsiye ettim.",
        "hi": "कल जो किताब मैंने खरीदी थी वह बहुत दिलचस्प है और मैंने उसे अपनी बहन को सुझाया।",
        "bn": "কাল যে বইটি কিনেছিলাম সেটি খুব আকর্ষণীয় এবং আমি এটি আমার বোনকে সুপারিশ করেছি।",
        "ur": "کل جو کتاب میں نے خریدی وہ بہت دلچسپ ہے اور میں نے اسے اپنی بہن کو تجویز کیا۔",
        "id": "Buku yang saya beli kemarin sangat menarik dan saya merekomendasikannya kepada saudara perempuan saya.",
        "vi": "Cuốn sách tôi mua hôm qua rất thú vị và tôi đã giới thiệu nó cho em gái tôi.",
        "th": "หนังสือที่ฉันซื้อเมื่อวานนี้น่าสนใจมากและฉันแนะนำให้กับน้องสาวของฉัน",
        "nl": "Het boek dat ik gisteren heb gekocht is erg interessant en ik heb het aan mijn zus aanbevolen.",
        "sv": "Boken som jag köpte igår är mycket intressant och jag rekommenderade den till min syster.",
    }

    def test_language_detection(self):
        for expected, text in self.CASES.items():
            with self.subTest(language=expected):
                detected = detect_language(text)
                self.assertEqual(detected["code"], expected, detected)


class ServerApiTests(unittest.TestCase):
    BASE = os.environ.get("LINGUALENS_TEST_BASE", "http://127.0.0.1:8765")

    def get_json(self, path):
        with urllib.request.urlopen(self.BASE + path, timeout=10) as response:
            import json
            return json.loads(response.read().decode("utf-8"))

    def test_health_counts_24_languages(self):
        try:
            health = self.get_json("/api/health")
        except Exception as exc:  # pragma: no cover - server optional
            self.skipTest(f"local server not running: {exc}")
        self.assertEqual(health["version"], "2.0.0")
        self.assertGreaterEqual(health["grammar"]["total"], 231)
        self.assertEqual(len(health["grammar"]["languages"]), 24)

    def test_every_detail_endpoint(self):
        try:
            listing = self.get_json("/api/grammar")
        except Exception as exc:  # pragma: no cover - server optional
            self.skipTest(f"local server not running: {exc}")
        for item in listing["items"]:
            detail = self.get_json("/api/grammar/" + item["id"])["grammar"]
            self.assertEqual(detail["id"], item["id"])
            self.assertNotIn("patterns", detail)


if __name__ == "__main__":
    unittest.main()
