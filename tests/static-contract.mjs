import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../dist/index.html", import.meta.url), "utf8");
const app = readFileSync(new URL("../dist/app.js", import.meta.url), "utf8");
const worker = readFileSync(new URL("../dist/sw.js", import.meta.url), "utf8");
const css = readFileSync(new URL("../dist/styles.css", import.meta.url), "utf8");

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

const nightBodyRule = css.match(/body\[data-theme="night"\]\s*\{([\s\S]*?)\}/)?.[1] || "";
assert.match(nightBodyRule, /color\s*:\s*var\(--ink\)/, "Dark mode must explicitly apply its ink colour to the whole page.");

const catalog = JSON.parse(readFileSync(new URL("../dist/books/catalog.json", import.meta.url), "utf8"));
assert.equal(catalog.books.length, 6, "The starter library must contain six complete classics.");
assert.equal(catalog.books.filter((book) => book.flag === "RU").length, 3, "The library must contain three Russian editions.");
assert.equal(catalog.books.filter((book) => book.flag === "DE").length, 3, "The library must contain three German editions.");

for (const metadata of catalog.books) {
  const book = JSON.parse(readFileSync(new URL(`../dist/books/${metadata.id}.json`, import.meta.url), "utf8"));
  assert.equal(book.chapters.length, metadata.chapterCount, `${metadata.id} chapter metadata must match its reading file.`);
  const segments = book.chapters.flatMap((chapter) => chapter.paragraphs.flat());
  assert.ok(segments.length > 800, `${metadata.id} must contain a complete edition, not a short sample.`);
  assert.ok(segments.every(([target, english]) => target.trim() && english.trim()), `${metadata.id} passages must contain both languages.`);
}

console.log(`Static contract passed for asset version ${scriptVersion}.`);
