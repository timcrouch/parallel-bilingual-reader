#!/usr/bin/env python3
"""Build the bundled bilingual classics library from public-domain web editions.

The generated JSON is committed to the app so reading never depends on the
source sites being online. Run this script from the repository root.
"""

from __future__ import annotations

import json
import math
import re
import sys
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "books"
USER_AGENT = "ParallelReader/1.0 (personal bilingual reading project)"


@dataclass(frozen=True)
class Source:
    url: str
    landing_url: str
    parser: str


@dataclass(frozen=True)
class Book:
    id: str
    title: str
    target_title: str
    author: str
    language: str
    language_name: str
    flag: str
    cover: str
    target: Source
    english: Source
    edition_note: str


PG = "https://www.gutenberg.org/cache/epub/{0}/pg{0}-images.html"
PG_LANDING = "https://www.gutenberg.org/ebooks/{0}"


def pg(book_id: int, parser: str) -> Source:
    return Source(PG.format(book_id), PG_LANDING.format(book_id), parser)


BOOKS = [
    Book(
        "alice-ru",
        "Alice’s Adventures in Wonderland",
        "Приключения Алисы в стране чудес",
        "Lewis Carroll",
        "ru-RU",
        "Russian",
        "RU",
        "alice-cover",
        Source(
            "https://ru.wikisource.org/wiki/%D0%9F%D1%80%D0%B8%D0%BA%D0%BB%D1%8E%D1%87%D0%B5%D0%BD%D0%B8%D1%8F_%D0%90%D0%BB%D0%B8%D1%81%D1%8B_%D0%B2_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B5_%D1%87%D1%83%D0%B4%D0%B5%D1%81_%28%D0%9A%D1%8D%D1%80%D1%80%D0%BE%D0%BB%D0%BB%3B_%D0%A0%D0%BE%D0%B6%D0%B4%D0%B5%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D1%81%D0%BA%D0%B0%D1%8F%29",
            "https://ru.wikisource.org/wiki/%D0%9F%D1%80%D0%B8%D0%BA%D0%BB%D1%8E%D1%87%D0%B5%D0%BD%D0%B8%D1%8F_%D0%90%D0%BB%D0%B8%D1%81%D1%8B_%D0%B2_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B5_%D1%87%D1%83%D0%B4%D0%B5%D1%81_%28%D0%9A%D1%8D%D1%80%D1%80%D0%BE%D0%BB%D0%BB%3B_%D0%A0%D0%BE%D0%B6%D0%B4%D0%B5%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D1%81%D0%BA%D0%B0%D1%8F%29",
            "alice_ru",
        ),
        pg(11, "alice_en"),
        "Russian translation by A. Rozhdestvenskaya (1909).",
    ),
    Book(
        "garden-ru",
        "The Secret Garden",
        "Таинственный сад",
        "Frances Hodgson Burnett",
        "ru-RU",
        "Russian",
        "RU",
        "garden-cover",
        Source(
            "https://ru.wikisource.org/wiki/%D0%A2%D0%B0%D0%B8%D0%BD%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B9_%D1%81%D0%B0%D0%B4_%28%D0%91%D1%91%D1%80%D0%BD%D0%B5%D1%82%D1%82%29",
            "https://ru.wikisource.org/wiki/%D0%A2%D0%B0%D0%B8%D0%BD%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B9_%D1%81%D0%B0%D0%B4_%28%D0%91%D1%91%D1%80%D0%BD%D0%B5%D1%82%D1%82%29",
            "garden_ru",
        ),
        pg(17396, "garden_en"),
        "Russian translation by R. Rubinova (1914).",
    ),
    Book(
        "time-ru",
        "The Time Machine",
        "Машина времени",
        "H. G. Wells",
        "ru-RU",
        "Russian",
        "RU",
        "time-cover",
        Source(
            "https://ru.wikisource.org/wiki/%D0%9C%D0%B0%D1%88%D0%B8%D0%BD%D0%B0_%D0%B2%D1%80%D0%B5%D0%BC%D0%B5%D0%BD%D0%B8_%28%D0%A3%D1%8D%D0%BB%D0%BB%D1%81%3B_%D0%9C%D0%BE%D1%80%D0%BE%D0%B7%D0%BE%D0%B2%29",
            "https://ru.wikisource.org/wiki/%D0%9C%D0%B0%D1%88%D0%B8%D0%BD%D0%B0_%D0%B2%D1%80%D0%B5%D0%BC%D0%B5%D0%BD%D0%B8_%28%D0%A3%D1%8D%D0%BB%D0%BB%D1%81%3B_%D0%9C%D0%BE%D1%80%D0%BE%D0%B7%D0%BE%D0%B2%29",
            "time_ru",
        ),
        pg(35, "time_en"),
        "Russian translation by N. A. Morozov (1909).",
    ),
    Book(
        "alice-de",
        "Alice’s Adventures in Wonderland",
        "Alice’s Abenteuer im Wunderland",
        "Lewis Carroll",
        "de-DE",
        "German",
        "DE",
        "alice-de-cover",
        pg(19778, "alice_de"),
        pg(11, "alice_en"),
        "German translation by Antonie Zimmermann (1869).",
    ),
    Book(
        "treasure-de",
        "Treasure Island",
        "Die Schatzinsel",
        "Robert Louis Stevenson",
        "de-DE",
        "German",
        "DE",
        "treasure-cover",
        pg(49424, "treasure_de"),
        pg(120, "treasure_en"),
        "German edition published in 1922.",
    ),
    Book(
        "faust-de",
        "Faust, Part One",
        "Faust. Der Tragödie erster Teil",
        "Johann Wolfgang von Goethe",
        "de-DE",
        "German",
        "DE",
        "faust-cover",
        pg(2229, "faust_de"),
        pg(14591, "faust_en"),
        "English translation by Bayard Taylor (1870–71).",
    ),
]


class ReadingHTMLParser(HTMLParser):
    """Collect headings and paragraphs in document order."""

    TAGS = {"h1", "h2", "h3", "h4", "p"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.capture: str | None = None
        self.parts: list[str] = []
        self.items: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.TAGS and self.capture is None:
            self.capture = tag
            self.parts = []
        elif self.capture and tag == "br":
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != self.capture:
            return
        text = clean_text("".join(self.parts))
        if text:
            self.items.append((tag, text))
        self.capture = None
        self.parts = []


def clean_text(value: str) -> str:
    value = value.replace("\u00ad", "").replace("\xa0", " ")
    value = re.sub(r"\[Pg\.?\s*\d+\]", " ", value, flags=re.I)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    return value.strip()


def fetch(source: Source) -> list[tuple[str, str]]:
    request = urllib.request.Request(source.url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        document = response.read().decode("utf-8")
    parser = ReadingHTMLParser()
    parser.feed(document)
    return parser.items


def make_chapter_parser(
    starts: Callable[[str, str], bool],
    *,
    stop: Callable[[str, str], bool] | None = None,
    following_title: Callable[[str, str], bool] | None = None,
) -> Callable[[list[tuple[str, str]]], list[dict]]:
    def parse(items: list[tuple[str, str]]) -> list[dict]:
        chapters: list[dict] = []
        current: dict | None = None
        for tag, text in items:
            if stop and stop(tag, text):
                break
            if starts(tag, text):
                current = {"title": text, "paragraphs": []}
                chapters.append(current)
                continue
            if current is None:
                continue
            if following_title and not current["paragraphs"] and following_title(tag, text):
                current["title"] = f'{current["title"]} {text}'
                continue
            if tag == "p" and text not in {"Image", "* * *"} and not re.fullmatch(r"\[?\d+\]?", text):
                current["paragraphs"].append(text)
        return [chapter for chapter in chapters if chapter["paragraphs"]]

    return parse


LICENSE = lambda tag, text: tag.startswith("h") and "FULL PROJECT GUTENBERG" in text.upper()
ROMAN = r"[IVXLCDM]+"
GERMAN_ORDINAL = (
    r"(?:Erstes|Zweites|Drittes|Viertes|Fünftes|Sechstes|Siebentes|Achtes|Neuntes|"
    r"Zehntes|Elftes|Zwölftes|Dreizehntes|Vierzehntes|Fünfzehntes|Sechzehntes|"
    r"Siebzehntes|Achtzehntes|Neunzehntes|Zwanzigstes|Einundzwanzigstes|"
    r"Zweiundzwanzigstes|Dreiundzwanzigstes|Vierundzwanzigstes|Fünfundzwanzigstes|"
    r"Sechsundzwanzigstes|Siebenundzwanzigstes|Achtundzwanzigstes|Neunundzwanzigstes|"
    r"Dreißigstes|Einunddreißigstes|Zweiunddreißigstes|Dreiunddreißigstes|"
    r"Vierunddreißigstes|Fünfunddreißigstes|Sechsunddreißigstes)"
)


PARSERS: dict[str, Callable[[list[tuple[str, str]]], list[dict]]] = {
    "alice_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.match(rf"^CHAPTER {ROMAN}\.\s", text)),
        stop=LICENSE,
    ),
    "alice_de": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.fullmatch(rf"{GERMAN_ORDINAL} Kapitel\.", text)),
        stop=LICENSE,
        following_title=lambda tag, text: tag == "h2",
    ),
    "alice_ru": make_chapter_parser(
        lambda tag, text: tag == "h3" and bool(re.match(rf"^{ROMAN}\.\s", text)),
    ),
    "garden_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.fullmatch(rf"CHAPTER {ROMAN}", text)),
        stop=LICENSE,
        following_title=lambda tag, text: tag == "h3",
    ),
    "garden_ru": make_chapter_parser(
        lambda tag, text: tag in {"h3", "h4"} and bool(re.fullmatch(rf"Глава {ROMAN}", text)),
    ),
    "time_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and (bool(re.match(rf"^{ROMAN}\.\s", text)) or text == "Epilogue"),
        stop=LICENSE,
    ),
    "time_ru": make_chapter_parser(
        lambda tag, text: tag == "h3" and text in {
            "Введение", "Машина времени", "Путешественник возвращается", "Путешествие во времени",
            "В Золотом Веке", "Закат человечества", "Внезапный удар", "Объяснение", "Морлоки",
            "Когда настала ночь", "Дворец из зеленого фарфора", "В темноте",
            "Ловушка Белого Сфинкса", "Дальнейшее путешествие", "Возвращение Путешественника",
            "После рассказа", "Эпилог",
        },
    ),
    "treasure_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.match(rf"^{ROMAN}\s", text)),
        stop=LICENSE,
    ),
    "treasure_de": make_chapter_parser(
        lambda tag, text: tag == "h3" and "Kapitel" in text,
        stop=LICENSE,
    ),
    "faust_de": make_chapter_parser(
        lambda tag, text: tag == "h2" and text not in {
            "The Project Gutenberg eBook of Faust: Der Tragödie erster Teil", "by Johann Wolfgang von Goethe",
            "Contents", "FAUST: Der Tragödie erster Teil",
        } and "FULL PROJECT GUTENBERG" not in text.upper(),
        stop=LICENSE,
    ),
    "faust_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and (
            text in {"DEDICATION", "PRELUDE AT THE THEATRE", "PROLOGUE IN HEAVEN"}
            or bool(re.fullmatch(ROMAN, text))
        ),
        stop=LICENSE,
    ),
}


def sequence_length(values: list[str]) -> int:
    return sum(len(value) for value in values)


def align_sequences(target: list[str], english: list[str]) -> list[tuple[str, str]]:
    """Length-align two translated sequences with small merge groups."""
    if not target or not english:
        return [(" ".join(target), " ".join(english))]

    ratio = max(0.35, min(2.8, sequence_length(target) / max(1, sequence_length(english))))
    operations = [(1, 1, 0.0), (1, 2, 0.16), (2, 1, 0.16), (2, 2, 0.24), (1, 3, 0.42), (3, 1, 0.42)]
    rows, columns = len(target), len(english)
    infinity = float("inf")
    scores = [[infinity] * (columns + 1) for _ in range(rows + 1)]
    previous: list[list[tuple[int, int] | None]] = [[None] * (columns + 1) for _ in range(rows + 1)]
    scores[0][0] = 0.0

    for i in range(rows + 1):
        for j in range(columns + 1):
            if not math.isfinite(scores[i][j]):
                continue
            for take_target, take_english, penalty in operations:
                ni, nj = i + take_target, j + take_english
                if ni > rows or nj > columns:
                    continue
                target_length = sequence_length(target[i:ni])
                english_length = sequence_length(english[j:nj])
                length_cost = abs(math.log((target_length + 4) / (english_length * ratio + 4)))
                score = scores[i][j] + length_cost + penalty
                if score < scores[ni][nj]:
                    scores[ni][nj] = score
                    previous[ni][nj] = (i, j)

    if previous[rows][columns] is None:
        return [(" ".join(target), " ".join(english))]

    groups: list[tuple[str, str]] = []
    i, j = rows, columns
    while i or j:
        point = previous[i][j]
        if point is None:
            return [(" ".join(target), " ".join(english))]
        pi, pj = point
        groups.append((" ".join(target[pi:i]), " ".join(english[pj:j])))
        i, j = pi, pj
    groups.reverse()
    return groups


SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?…])\s+(?=[—\-\"“„'A-ZА-ЯЁÄÖÜ])")


def sentences(paragraph: str) -> list[str]:
    pieces = [piece.strip() for piece in SENTENCE_BOUNDARY.split(paragraph) if piece.strip()]
    return pieces or [paragraph]


def align_chapters(target: list[dict], english: list[dict]) -> list[dict]:
    target_lengths = [str(sequence_length(chapter["paragraphs"])) for chapter in target]
    english_lengths = [str(sequence_length(chapter["paragraphs"])) for chapter in english]

    # Reuse the alignment path, but retain chapter indexes rather than its strings.
    ratio = sum(map(int, target_lengths)) / max(1, sum(map(int, english_lengths)))
    operations = [(1, 1, 0.0), (1, 2, 0.2), (2, 1, 0.2), (2, 2, 0.3)]
    rows, columns = len(target), len(english)
    inf = float("inf")
    scores = [[inf] * (columns + 1) for _ in range(rows + 1)]
    previous: list[list[tuple[int, int] | None]] = [[None] * (columns + 1) for _ in range(rows + 1)]
    scores[0][0] = 0.0
    for i in range(rows + 1):
        for j in range(columns + 1):
            if not math.isfinite(scores[i][j]):
                continue
            for take_target, take_english, penalty in operations:
                ni, nj = i + take_target, j + take_english
                if ni > rows or nj > columns:
                    continue
                left = sum(sequence_length(chapter["paragraphs"]) for chapter in target[i:ni])
                right = sum(sequence_length(chapter["paragraphs"]) for chapter in english[j:nj])
                cost = abs(math.log((left + 20) / (right * ratio + 20))) + penalty
                if scores[i][j] + cost < scores[ni][nj]:
                    scores[ni][nj] = scores[i][j] + cost
                    previous[ni][nj] = (i, j)
    if previous[rows][columns] is None:
        raise RuntimeError(f"Unable to align {rows} target chapters with {columns} English chapters")

    chapter_groups: list[tuple[int, int, int, int]] = []
    i, j = rows, columns
    while i or j:
        pi, pj = previous[i][j] or (0, 0)
        chapter_groups.append((pi, i, pj, j))
        i, j = pi, pj
    chapter_groups.reverse()

    output: list[dict] = []
    for target_start, target_end, english_start, english_end in chapter_groups:
        target_group = target[target_start:target_end]
        english_group = english[english_start:english_end]
        target_paragraphs = [paragraph for chapter in target_group for paragraph in chapter["paragraphs"]]
        english_paragraphs = [paragraph for chapter in english_group for paragraph in chapter["paragraphs"]]
        paragraph_pairs = align_sequences(target_paragraphs, english_paragraphs)
        segments: list[list[str]] = []
        for target_paragraph, english_paragraph in paragraph_pairs:
            segments.extend([list(pair) for pair in align_sequences(sentences(target_paragraph), sentences(english_paragraph))])
        output.append({
            "title": " / ".join(chapter["title"] for chapter in target_group),
            "englishTitle": " / ".join(chapter["title"] for chapter in english_group),
            "segments": segments,
        })
    return output


def build_book(book: Book, cache: dict[str, list[tuple[str, str]]]) -> dict:
    print(f"Fetching {book.id}…", flush=True)
    if book.target.url not in cache:
        cache[book.target.url] = fetch(book.target)
    if book.english.url not in cache:
        cache[book.english.url] = fetch(book.english)
    target_items = cache[book.target.url]
    english_items = cache[book.english.url]
    target_chapters = PARSERS[book.target.parser](target_items)
    english_chapters = PARSERS[book.english.parser](english_items)
    if not target_chapters or not english_chapters:
        raise RuntimeError(f"No chapters parsed for {book.id}")
    chapters = align_chapters(target_chapters, english_chapters)
    segment_count = sum(len(chapter["segments"]) for chapter in chapters)
    if segment_count < 100:
        raise RuntimeError(f"Suspiciously small book {book.id}: {segment_count} aligned segments")
    print(
        f"  {len(target_chapters)} target + {len(english_chapters)} English chapters "
        f"→ {len(chapters)} reading chapters, {segment_count} aligned segments",
        flush=True,
    )
    return {
        "id": book.id,
        "title": book.title,
        "targetTitle": book.target_title,
        "author": book.author,
        "language": book.language,
        "languageName": book.language_name,
        "flag": book.flag,
        "cover": book.cover,
        "editionNote": book.edition_note,
        "sources": [
            {"label": "Target-language edition", "url": book.target.landing_url},
            {"label": "English edition", "url": book.english.landing_url},
        ],
        "chapters": chapters,
    }


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cache: dict[str, list[tuple[str, str]]] = {}
    catalog = []
    for book in BOOKS:
        document = build_book(book, cache)
        path = OUTPUT / f"{book.id}.json"
        path.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        catalog.append({key: document[key] for key in (
            "id", "title", "targetTitle", "author", "language", "languageName", "flag", "cover", "editionNote"
        )} | {"chapterCount": len(document["chapters"]), "path": f"./books/{book.id}.json"})
    (OUTPUT / "catalog.json").write_text(
        json.dumps({"books": catalog}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(catalog)} complete books to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
