import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../dist/index.html", import.meta.url), "utf8");
const app = readFileSync(new URL("../dist/app.js", import.meta.url), "utf8");
const worker = readFileSync(new URL("../dist/sw.js", import.meta.url), "utf8");

const styleVersion = html.match(/styles\.css\?v=(\d+)/)?.[1];
const scriptVersion = html.match(/app\.js\?v=(\d+)/)?.[1];

assert.ok(styleVersion, "The stylesheet URL must carry a cache-busting version.");
assert.equal(scriptVersion, styleVersion, "CSS and JavaScript must ship with the same asset version.");
assert.match(worker, new RegExp(`styles\\.css\\?v=${styleVersion}`), "The service worker must cache the versioned stylesheet.");
assert.match(worker, new RegExp(`app\\.js\\?v=${scriptVersion}`), "The service worker must cache the versioned JavaScript.");
assert.equal((html.match(/data-theme-toggle/g) || []).length, 2, "Theme controls must exist in the library and reader.");
assert.match(app, /\$\$\('\[data-theme-toggle\]'\).*addEventListener\('click'/, "Theme controls must have a click handler.");

console.log(`Static contract passed for asset version ${scriptVersion}.`);
