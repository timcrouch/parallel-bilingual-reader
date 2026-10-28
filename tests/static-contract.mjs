import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../dist/index.html", import.meta.url), "utf8");
const app = readFileSync(new URL("../dist/app.js", import.meta.url), "utf8");
const worker = readFileSync(new URL("../dist/sw.js", import.meta.url), "utf8");
const css = readFileSync(new URL("../dist/styles.css", import.meta.url), "utf8");
const manifest = JSON.parse(readFileSync(new URL("../dist/manifest.webmanifest", import.meta.url), "utf8"));

const styleVersion = html.match(/styles\.css\?v=(\d+)/)?.[1];
const scriptVersion = html.match(/app\.js\?v=(\d+)/)?.[1];

assert.ok(styleVersion, "The stylesheet URL must carry a cache-busting version.");
assert.equal(scriptVersion, styleVersion, "CSS and JavaScript must ship with the same asset version.");
assert.match(worker, new RegExp(`styles\\.css\\?v=${styleVersion}`), "The service worker must cache the versioned stylesheet.");
assert.match(worker, new RegExp(`app\\.js\\?v=${scriptVersion}`), "The service worker must cache the versioned JavaScript.");
assert.equal((html.match(/data-theme-toggle/g) || []).length, 2, "Theme controls must exist in the library and reader.");
assert.match(app, /\$\$\('\[data-theme-toggle\]'\).*addEventListener\('click'/, "Theme controls must have a click handler.");
assert.match(app, /function changeChapter\(direction\)/, "Complete editions must support chapter navigation.");
assert.match(app, /parallel-progress:/, "Reading position must be saved per book.");
assert.match(app, /let sentenceTapTimer/, "Sentence taps must wait for word selection to settle.");
assert.match(app, /if \(!selectedText && element\) element\.classList\.add\("active"\)/, "A word selection must not highlight the whole sentence.");
assert.match(app, /selectionKind.*"WORD"/, "Single-word selections must be identified separately from full sentences.");
assert.match(css, /\.sentence:hover, \.sentence:focus-visible/, "Touch focus must not make a word selection look like the whole sentence is selected.");
assert.match(html, /id="lengthFilter"/, "The library must provide a length filter.");
assert.match(html, /id="difficultyFilter"/, "The library must provide a difficulty filter.");
assert.match(html, /id="sortBooks"/, "The library must provide sorting controls.");
assert.match(app, /beforeinstallprompt/, "The install control must support browser PWA installation.");
assert.match(html, /apple-mobile-web-app-capable/, "iPhone and iPad home-screen mode must be enabled.");
assert.match(html, /Press and hold a word/, "The reader must explain how to select a single word on touch devices.");
assert.match(html, /id="installModal"/, "Install help must use a readable modal instead of a transient toast.");
assert.match(app, /Open Parallel from its https address before adding it to your Home Screen\./, "iPhone and iPad install help must warn when offline support is unavailable over HTTP.");
assert.equal(manifest.display, "standalone", "The installed app must launch without browser chrome.");
assert.ok(manifest.icons.some((icon) => icon.sizes === "512x512"), "The PWA must provide a 512px app icon.");
assert.match(worker, /key\.startsWith\(CACHE_PREFIX\)/, "The service worker must only delete old Parallel caches.");
assert.match(worker, /catalog\.books\.map/, "The service worker must pre-cache every bundled book for offline reading.");

const nightBodyRule = css.match(/body\[data-theme="night"\]\s*\{([\s\S]*?)\}/)?.[1] || "";
assert.match(nightBodyRule, /color\s*:\s*var\(--ink\)/, "Dark mode must explicitly apply its ink colour to the whole page.");

const catalog = JSON.parse(readFileSync(new URL("../dist/books/catalog.json", import.meta.url), "utf8"));
assert.equal(catalog.books.length, 12, "The starter library must contain twelve complete classics.");
assert.equal(catalog.books.filter((book) => book.flag === "RU").length, 9, "The library must contain nine Russian editions.");
assert.equal(catalog.books.filter((book) => book.flag === "DE").length, 3, "The library must contain three German editions.");
for (const id of ["call-wild-ru", "sea-wolf-ru", "war-worlds-ru", "little-princess-ru", "robinson-crusoe-ru", "treasure-ru"]) {
  assert.ok(catalog.books.some((book) => book.id === id), `${id} must be bundled in the library.`);
}

for (const metadata of catalog.books) {
  assert.ok(["short", "medium", "long"].includes(metadata.length), `${metadata.id} must have a length category.`);
  assert.ok(["accessible", "intermediate", "advanced"].includes(metadata.difficulty), `${metadata.id} must have a difficulty category.`);
  assert.ok(metadata.wordCount > 10_000, `${metadata.id} must report a credible target-language word count.`);
  const book = JSON.parse(readFileSync(new URL(`../dist/books/${metadata.id}.json`, import.meta.url), "utf8"));
  assert.equal(book.chapters.length, metadata.chapterCount, `${metadata.id} chapter metadata must match its reading file.`);
  const segments = book.chapters.flatMap((chapter) => chapter.paragraphs.flat());
  assert.ok(segments.length > 800, `${metadata.id} must contain a complete edition, not a short sample.`);
  assert.ok(segments.every(([target, english]) => target.trim() && english.trim()), `${metadata.id} passages must contain both languages.`);
  assert.ok(segments.every(([target]) => !/^(Если произведение является переводом|Исключительное право на это произведение|Поскольку Российская Федерация)/.test(target)), `${metadata.id} must not include source-site copyright boilerplate.`);
}

assert.equal(catalog.books.find((book) => book.id === "little-princess-ru").chapterCount, 19, "A Little Princess must use the complete 19-chapter Russian edition.");

console.log(`Static contract passed for asset version ${scriptVersion}.`);
