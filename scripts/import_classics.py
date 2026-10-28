#!/usr/bin/env python3
"""Build the bundled bilingual classics library from public-domain web editions.

The generated JSON is committed to the app so reading never depends on the
source sites being online. Run this script from the repository root.
"""

from __future__ import annotations

import json
import math
import os
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
    cache_name: str | None = None


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
    difficulty: str = "intermediate"
    normalize_russian_spelling: bool = False


PG = "https://www.gutenberg.org/cache/epub/{0}/pg{0}-images.html"
PG_LANDING = "https://www.gutenberg.org/ebooks/{0}"


def pg(book_id: int, parser: str, cache_name: str | None = None) -> Source:
    return Source(PG.format(book_id), PG_LANDING.format(book_id), parser, cache_name)


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
        "accessible",
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
        "intermediate",
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
        "intermediate",
    ),
    Book(
        "call-wild-ru",
        "The Call of the Wild",
        "Зов предков",
        "Jack London",
        "ru-RU",
        "Russian",
        "RU",
        "call-cover",
        Source(
            "https://ru.wikisource.org/wiki/%D0%97%D0%BE%D0%B2_%D0%BF%D1%80%D0%B5%D0%B4%D0%BA%D0%BE%D0%B2_(%D0%9B%D0%BE%D0%BD%D0%B4%D0%BE%D0%BD%3B_%D0%92%D0%B5%D1%80%D1%88%D0%B8%D0%BD%D0%B8%D0%BD%D0%B0)",
            "https://ru.wikisource.org/wiki/%D0%97%D0%BE%D0%B2_%D0%BF%D1%80%D0%B5%D0%B4%D0%BA%D0%BE%D0%B2_(%D0%9B%D0%BE%D0%BD%D0%B4%D0%BE%D0%BD%3B_%D0%92%D0%B5%D1%80%D1%88%D0%B8%D0%BD%D0%B8%D0%BD%D0%B0)",
            "call_ru",
            "call-wild-ru",
        ),
        pg(215, "call_en", "call-wild-en"),
        "Russian translation by Z. A. Vershinina (1928).",
        "accessible",
    ),
    Book(
        "sea-wolf-ru",
        "The Sea-Wolf",
        "Морской волк",
        "Jack London",
        "ru-RU",
        "Russian",
        "RU",
        "sea-cover",
        Source(
            "https://ru.wikisource.org/wiki/%D0%9C%D0%BE%D1%80%D1%81%D0%BA%D0%BE%D0%B9_%D0%B2%D0%BE%D0%BB%D0%BA_(%D0%9B%D0%BE%D0%BD%D0%B4%D0%BE%D0%BD%3B_%D0%92%D0%B5%D1%80%D1%88%D0%B8%D0%BD%D0%B8%D0%BD%D0%B0)",
            "https://ru.wikisource.org/wiki/%D0%9C%D0%BE%D1%80%D1%81%D0%BA%D0%BE%D0%B9_%D0%B2%D0%BE%D0%BB%D0%BA_(%D0%9B%D0%BE%D0%BD%D0%B4%D0%BE%D0%BD%3B_%D0%92%D0%B5%D1%80%D1%88%D0%B8%D0%BD%D0%B8%D0%BD%D0%B0)",
            "sea_ru",
            "sea-wolf-ru",
        ),
        pg(1074, "sea_en", "sea-wolf-en"),
        "Russian translation by Z. A. Vershinina (1929).",
        "intermediate",
    ),
    Book(
        "war-worlds-ru",
        "The War of the Worlds",
        "Борьба миров",
        "H. G. Wells",
        "ru-RU",
        "Russian",
        "RU",
        "war-cover",
        Source(
            "https://ru.wikisource.org/wiki/%D0%91%D0%BE%D1%80%D1%8C%D0%B1%D0%B0_%D0%BC%D0%B8%D1%80%D0%BE%D0%B2_(%D0%A3%D1%8D%D0%BB%D0%BB%D1%81%3B_%D0%9F%D0%B8%D0%BC%D0%B5%D0%BD%D0%BE%D0%B2%D0%B0)",
            "https://ru.wikisource.org/wiki/%D0%91%D0%BE%D1%80%D1%8C%D0%B1%D0%B0_%D0%BC%D0%B8%D1%80%D0%BE%D0%B2_(%D0%A3%D1%8D%D0%BB%D0%BB%D1%81%3B_%D0%9F%D0%B8%D0%BC%D0%B5%D0%BD%D0%BE%D0%B2%D0%B0)",
            "war_ru",
            "war-worlds-ru",
        ),
        pg(36, "war_en", "war-worlds-en"),
        "Russian translation by Emilia Pimenova (1927).",
        "intermediate",
    ),
    Book(
        "little-princess-ru",
        "A Little Princess",
        "Маленькая принцесса",
        "Frances Hodgson Burnett",
        "ru-RU",
        "Russian",
        "RU",
        "princess-cover",
        Source(
            "http://az.lib.ru/b/bernett_f_e/text_1905_a_little_princess.shtml",
            "http://az.lib.ru/b/bernett_f_e/text_1905_a_little_princess.shtml",
            "princess_ru_complete",
            "little-princess-ru-az",
        ),
        pg(146, "princess_en", "little-princess-en"),
        "Complete Russian translation by A. N. Rozhdestvenskaya (1908).",
        "accessible",
    ),
    Book(
        "robinson-crusoe-ru",
        "Robinson Crusoe",
        "Робинзон Крузо",
        "Daniel Defoe",
        "ru-RU",
        "Russian",
        "RU",
        "robinson-cover",
        Source(
            "https://ru.wikisource.org/wiki/%D0%A0%D0%BE%D0%B1%D0%B8%D0%BD%D0%B7%D0%BE%D0%BD_%D0%9A%D1%80%D1%83%D0%B7%D0%BE_(%D0%94%D0%B5%D1%84%D0%BE%3B_%D0%A8%D0%B8%D1%88%D0%BC%D0%B0%D1%80%D1%91%D0%B2%D0%B0)",
            "https://ru.wikisource.org/wiki/%D0%A0%D0%BE%D0%B1%D0%B8%D0%BD%D0%B7%D0%BE%D0%BD_%D0%9A%D1%80%D1%83%D0%B7%D0%BE_(%D0%94%D0%B5%D1%84%D0%BE%3B_%D0%A8%D0%B8%D1%88%D0%BC%D0%B0%D1%80%D1%91%D0%B2%D0%B0)",
            "robinson_ru",
            "robinson-crusoe-ru",
        ),
        pg(521, "robinson_en", "robinson-crusoe-en"),
        "Russian translation by Maria Shishmareva (1928). Chapter breaks are reconstructed from the English edition.",
        "intermediate",
    ),
    Book(
        "treasure-ru",
        "Treasure Island",
        "Остров сокровищ",
        "Robert Louis Stevenson",
        "ru-RU",
        "Russian",
        "RU",
        "treasure-ru-cover",
        Source(
            "https://ru.wikisource.org/wiki/%D0%9E%D1%81%D1%82%D1%80%D0%BE%D0%B2_%D1%81%D0%BE%D0%BA%D1%80%D0%BE%D0%B2%D0%B8%D1%89_(%D0%A1%D1%82%D0%B8%D0%B2%D0%B5%D0%BD%D1%81%D0%BE%D0%BD%3B_%D0%9F%D0%B8%D0%BC%D0%B5%D0%BD%D0%BE%D0%B2%D0%B0)/%D0%94%D0%9E",
            "https://ru.wikisource.org/wiki/%D0%9E%D1%81%D1%82%D1%80%D0%BE%D0%B2_%D1%81%D0%BE%D0%BA%D1%80%D0%BE%D0%B2%D0%B8%D1%89_(%D0%A1%D1%82%D0%B8%D0%B2%D0%B5%D0%BD%D1%81%D0%BE%D0%BD%3B_%D0%9F%D0%B8%D0%BC%D0%B5%D0%BD%D0%BE%D0%B2%D0%B0)/%D0%94%D0%9E",
            "treasure_ru",
            "treasure-island-ru",
        ),
        pg(120, "treasure_en", "treasure-island-en"),
        "Russian translation by Emilia Pimenova (1916); spelling modernized for comfortable reading.",
        "intermediate",
        True,
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
        "intermediate",
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
        "intermediate",
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
        "advanced",
    ),
]


class ReadingHTMLParser(HTMLParser):
    """Collect headings and paragraphs in document order."""

    TAGS = {"h1", "h2", "h3", "h4", "p", "dd"}

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
    value = re.sub(r"\s+Printed in Great Britain.*$", "", value, flags=re.I | re.S)
    for marker in (
        "Источник текста:",
        "Transcriber's Note",
        "Transcriber’s Note",
        "Anmerkungen zur Transkription",
        "Folgende Inkonsistenzen",
        "Im Text wurden folgende Änderungen",
    ):
        if marker in value:
            value = value.split(marker, 1)[0]
    return value.strip()


def fetch(source: Source) -> list[tuple[str, str]]:
    cache_root = os.environ.get("PARALLEL_SOURCE_CACHE")
    cache_path = Path(cache_root) / f"{source.cache_name}.html" if cache_root and source.cache_name else None
    if cache_path and cache_path.exists():
        document = cache_path.read_text(encoding="utf-8")
    else:
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
            if tag == "p" and is_reading_paragraph(text):
                current["paragraphs"].append(text)
        return [chapter for chapter in chapters if chapter["paragraphs"]]

    return parse


LICENSE = lambda tag, text: tag.startswith("h") and "FULL PROJECT GUTENBERG" in text.upper()
ROMAN = r"[IVXLCDM]+"
SOURCE_BOILERPLATE_PREFIXES = (
    "Если произведение является переводом",
    "Исключительное право на это произведение",
    "Поскольку Российская Федерация",
    "Это произведение находится также в общественном достоянии",
)


def is_reading_paragraph(text: str) -> bool:
    return (
        text not in {"Image", "* * *"}
        and not re.fullmatch(r"\[?\d+\]?", text)
        and not re.fullmatch(r"[-=_* ]{3,}", text)
        and not text.startswith(SOURCE_BOILERPLATE_PREFIXES)
    )


GERMAN_ORDINAL = (
    r"(?:Erstes|Zweites|Drittes|Viertes|Fünftes|Sechstes|Siebentes|Achtes|Neuntes|"
    r"Zehntes|Elftes|Zwölftes|Dreizehntes|Vierzehntes|Fünfzehntes|Sechzehntes|"
    r"Siebzehntes|Achtzehntes|Neunzehntes|Zwanzigstes|Einundzwanzigstes|"
    r"Zweiundzwanzigstes|Dreiundzwanzigstes|Vierundzwanzigstes|Fünfundzwanzigstes|"
    r"Sechsundzwanzigstes|Siebenundzwanzigstes|Achtundzwanzigstes|Neunundzwanzigstes|"
    r"Dreißigstes|Einunddreißigstes|Zweiunddreißigstes|Dreiunddreißigstes|"
    r"Vierunddreißigstes|Fünfunddreißigstes|Sechsunddreißigstes)"
)


def parse_robinson_ru(items: list[tuple[str, str]]) -> list[dict]:
    paragraphs = [
        text for tag, text in items
        if tag == "p" and is_reading_paragraph(text)
    ]
    first = next(
        (index for index, text in enumerate(paragraphs) if text.startswith("Я родился в 1632 году")),
        None,
    )
    if first is None:
        return []
    return [{"title": "Робинзон Крузо", "paragraphs": paragraphs[first:]}]


def parse_princess_ru_complete(items: list[tuple[str, str]]) -> list[dict]:
    chapters: list[dict] = []
    current: dict | None = None
    for tag, text in items:
        normalized = text.replace("ХVIII", "XVIII")
        if tag == "dd" and re.match(rf"^{ROMAN}\n", normalized):
            current = {"title": normalized, "paragraphs": []}
            chapters.append(current)
        elif current and tag == "dd" and is_reading_paragraph(text):
            current["paragraphs"].append(text)
    return [chapter for chapter in chapters if chapter["paragraphs"]]


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
    "call_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.match(rf"^Chapter {ROMAN}\.\s", text)),
        stop=LICENSE,
    ),
    "call_ru": make_chapter_parser(
        lambda tag, text: tag == "h3" and bool(re.match(rf"^{ROMAN}\.\s", text)),
    ),
    "sea_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.fullmatch(rf"CHAPTER {ROMAN}\.", text)),
        stop=LICENSE,
    ),
    "sea_ru": make_chapter_parser(
        lambda tag, text: tag == "h3" and bool(re.fullmatch(rf"Глава {ROMAN}", text)),
    ),
    "war_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.match(rf"^{ROMAN}\.\n", text)),
        stop=LICENSE,
    ),
    "war_ru": make_chapter_parser(
        lambda tag, text: tag == "h3" and (bool(re.fullmatch(ROMAN, text)) or text == "Эпилог"),
        following_title=lambda tag, text: tag == "h3" and not bool(re.fullmatch(ROMAN, text)),
    ),
    "princess_en": make_chapter_parser(
        lambda tag, text: tag == "h3" and bool(re.fullmatch(r"\d+", text)),
        stop=LICENSE,
        following_title=lambda tag, text: tag == "h3",
    ),
    "princess_ru": make_chapter_parser(
        lambda tag, text: tag == "h3" and bool(re.match(rf"^{ROMAN}\.\s", text)),
    ),
    "princess_ru_complete": parse_princess_ru_complete,
    "robinson_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.match(rf"^CHAPTER {ROMAN}\.\s", text)),
        stop=LICENSE,
    ),
    "robinson_ru": parse_robinson_ru,
    "treasure_en": make_chapter_parser(
        lambda tag, text: tag == "h2" and bool(re.match(rf"^{ROMAN}\s", text)),
        stop=LICENSE,
    ),
    "treasure_de": make_chapter_parser(
        lambda tag, text: tag == "h3" and "Kapitel" in text,
        stop=LICENSE,
    ),
    "treasure_ru": make_chapter_parser(
        lambda tag, text: tag == "h4" and bool(re.match(r"^Глава [IVXLCDM]+\.?", text)),
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
    operations = [(1, 1, 0.0), (2, 2, 0.22), (2, 3, 0.34), (3, 2, 0.34)]
    operations.extend((1, size, 0.13 * (size - 1)) for size in range(2, 13))
    operations.extend((size, 1, 0.13 * (size - 1)) for size in range(2, 13))
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
    protected = re.sub(
        r"\b(?:Mr|Mrs|Ms|Dr|Prof|St|Jr|Sr|vs|etc)\.",
        lambda match: match.group(0).replace(".", "∯"),
        paragraph,
        flags=re.I,
    )
    protected = re.sub(
        r"\b([A-ZА-ЯЁÄÖÜ])\.(?=\s*[A-ZА-ЯЁÄÖÜ])",
        lambda match: f"{match.group(1)}∯",
        protected,
    )
    pieces = [piece.replace("∯", ".").strip() for piece in SENTENCE_BOUNDARY.split(protected) if piece.strip()]
    return pieces or [paragraph]


def split_target_by_english_chapters(paragraphs: list[str], english: list[dict]) -> list[dict]:
    """Reconstruct missing target chapter markers from the English length profile."""
    target_total = sequence_length(paragraphs)
    english_lengths = [sequence_length(chapter["paragraphs"]) for chapter in english]
    english_total = max(1, sum(english_lengths))
    output: list[dict] = []
    start = 0
    consumed_english = 0
    consumed_target = 0
    for index, english_length in enumerate(english_lengths):
        consumed_english += english_length
        if index == len(english_lengths) - 1:
            end = len(paragraphs)
        else:
            target_boundary = target_total * consumed_english / english_total
            end = start
            while end < len(paragraphs) - (len(english_lengths) - index - 1):
                next_length = len(paragraphs[end])
                if end > start and consumed_target + next_length > target_boundary:
                    break
                consumed_target += next_length
                end += 1
            end = max(start + 1, end)
        output.append({"title": f"Глава {index + 1}", "paragraphs": paragraphs[start:end]})
        if end > start and consumed_target < sum(len(value) for value in paragraphs[:end]):
            consumed_target = sum(len(value) for value in paragraphs[:end])
        start = end
    return output


def modernize_russian_text(value: str) -> str:
    translation = str.maketrans({"ѣ": "е", "Ѣ": "Е", "і": "и", "І": "И", "ѳ": "ф", "Ѳ": "Ф", "ѵ": "и", "Ѵ": "И"})
    value = value.translate(translation)
    return re.sub(r"([А-Яа-яЁё])ъ\b", r"\1", value)


def modernize_chapters(chapters: list[dict]) -> list[dict]:
    for chapter in chapters:
        chapter["title"] = modernize_russian_text(chapter["title"])
        chapter["paragraphs"] = [modernize_russian_text(value) for value in chapter["paragraphs"]]
    return chapters


def align_chapters(target: list[dict], english: list[dict]) -> list[dict]:
    if len(target) == len(english):
        chapter_groups = [(index, index + 1, index, index + 1) for index in range(len(target))]
        return build_aligned_chapters(target, english, chapter_groups)

    target_lengths = [str(sequence_length(chapter["paragraphs"])) for chapter in target]
    english_lengths = [str(sequence_length(chapter["paragraphs"])) for chapter in english]

    # Reuse the alignment path, but retain chapter indexes rather than its strings.
    ratio = sum(map(int, target_lengths)) / max(1, sum(map(int, english_lengths)))
    rows, columns = len(target), len(english)
    if rows <= columns <= rows * 2:
        operations = [(1, 1, 0.0), (1, 2, 0.2)]
    elif columns < rows <= columns * 2:
        operations = [(1, 1, 0.0), (2, 1, 0.2)]
    else:
        operations = [(1, 1, 0.0), (1, 2, 0.2), (2, 1, 0.2), (2, 2, 0.3)]
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

    return build_aligned_chapters(target, english, chapter_groups)


def merge_speaker_labels(chapters: list[dict]) -> list[dict]:
    """Join standalone dramatic speaker labels to the speech that follows."""
    for chapter in chapters:
        merged: list[str] = []
        paragraphs = chapter["paragraphs"]
        index = 0
        while index < len(paragraphs):
            paragraph = paragraphs[index]
            if index + 1 < len(paragraphs) and re.fullmatch(r"[A-Z][A-Z .’'\-]{1,45}", paragraph):
                merged.append(f"{paragraph}. {paragraphs[index + 1]}")
                index += 2
            else:
                merged.append(paragraph)
                index += 1
        chapter["paragraphs"] = merged
    return chapters


def build_aligned_chapters(
    target: list[dict],
    english: list[dict],
    chapter_groups: list[tuple[int, int, int, int]],
) -> list[dict]:
    output: list[dict] = []
    for target_start, target_end, english_start, english_end in chapter_groups:
        target_group = target[target_start:target_end]
        english_group = english[english_start:english_end]
        target_paragraphs = [paragraph for chapter in target_group for paragraph in chapter["paragraphs"]]
        english_paragraphs = [paragraph for chapter in english_group for paragraph in chapter["paragraphs"]]
        paragraph_pairs = align_sequences(target_paragraphs, english_paragraphs)
        paragraphs: list[list[list[str]]] = []
        for target_paragraph, english_paragraph in paragraph_pairs:
            paragraphs.append([
                list(pair) for pair in align_sequences(sentences(target_paragraph), sentences(english_paragraph))
            ])
        output.append({
            "title": " / ".join(chapter["title"] for chapter in target_group),
            "englishTitle": " / ".join(chapter["title"] for chapter in english_group),
            "paragraphs": paragraphs,
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
    if book.english.parser == "faust_en":
        english_chapters = merge_speaker_labels(english_chapters)
    if not target_chapters or not english_chapters:
        raise RuntimeError(f"No chapters parsed for {book.id}")
    if book.target.parser == "robinson_ru":
        target_chapters = split_target_by_english_chapters(target_chapters[0]["paragraphs"], english_chapters)
    if book.normalize_russian_spelling:
        target_chapters = modernize_chapters(target_chapters)
    chapters = align_chapters(target_chapters, english_chapters)
    segment_count = sum(
        len(paragraph)
        for chapter in chapters
        for paragraph in chapter["paragraphs"]
    )
    if segment_count < 100:
        raise RuntimeError(f"Suspiciously small book {book.id}: {segment_count} aligned segments")
    print(
        f"  {len(target_chapters)} target + {len(english_chapters)} English chapters "
        f"→ {len(chapters)} reading chapters, {segment_count} aligned segments",
        flush=True,
    )
    document = {
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
    return enrich_document(document, book)


DIFFICULTY_LABELS = {
    "accessible": "Accessible",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}


def enrich_document(document: dict, book: Book) -> dict:
    target_text = " ".join(
        pair[0]
        for chapter in document["chapters"]
        for paragraph in chapter["paragraphs"]
        for pair in paragraph
    )
    word_count = len(re.findall(r"[^\W\d_]+(?:[’'-][^\W\d_]+)*", target_text, flags=re.UNICODE))
    if word_count < 35_000:
        length, length_label = "short", "Short"
    elif word_count < 70_000:
        length, length_label = "medium", "Medium"
    else:
        length, length_label = "long", "Long"
    document.update({
        "difficulty": book.difficulty,
        "difficultyLabel": DIFFICULTY_LABELS[book.difficulty],
        "wordCount": word_count,
        "length": length,
        "lengthLabel": length_label,
    })
    return document


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cache: dict[str, list[tuple[str, str]]] = {}
    requested = set(sys.argv[1:])
    known_ids = {book.id for book in BOOKS}
    unknown = requested - known_ids
    if unknown:
        raise SystemExit(f"Unknown book id(s): {', '.join(sorted(unknown))}")
    catalog = []
    for book in BOOKS:
        path = OUTPUT / f"{book.id}.json"
        if not requested or book.id in requested:
            document = build_book(book, cache)
        elif path.exists():
            document = enrich_document(json.loads(path.read_text(encoding="utf-8")), book)
        else:
            raise RuntimeError(f"Missing generated book {book.id}; include it in this build")
        path.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        catalog.append({key: document[key] for key in (
            "id", "title", "targetTitle", "author", "language", "languageName", "flag", "cover", "editionNote",
            "difficulty", "difficultyLabel", "wordCount", "length", "lengthLabel",
        )} | {"chapterCount": len(document["chapters"]), "path": f"./books/{book.id}.json"})
    (OUTPUT / "catalog.json").write_text(
        json.dumps({"books": catalog}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(catalog)} complete books to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
