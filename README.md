# Parallel

Parallel is a mobile-first bilingual e-reader for reading English works in Russian or German. The target-language text stays central, while the original English and pronunciation are available on demand.

## Current prototype

- Twelve ready-to-read public-domain classics: nine Russian and three German editions
- Library filtering and sorting by language, length, and reading difficulty
- Chapter navigation and saved reading position
- Sentence-level English reveal
- Word-level online translation with an on-device cache
- Device text-to-speech playback
- E-paper, light, and app-wide dark themes
- Responsive phone and tablet layouts
- EPUB/TXT import flow ready for a translation backend
- Installable phone/tablet web app with app icons, standalone launch, and offline caching

## Run locally

```bash
python3 -m http.server 4173 --bind 0.0.0.0 --directory dist
```

Open `http://localhost:4173` on the computer, or use the computer's LAN IP from another device on the same network.

On iPhone or iPad, open the app in Safari, tap Share, then **Add to Home Screen**. On supported Android browsers, use the in-app **Install** button.

## Verify

```bash
node tests/static-contract.mjs
node --check dist/app.js
node --check dist/sw.js
```

The bundled classics and their sentence translations are stored locally in `dist/books/` and remain readable without contacting their source sites. Individual word lookups use the MyMemory translation API and are cached on the device after the first lookup. Automated translation for newly imported books and durable private library storage are not connected yet.

## Refresh the classics library

The generated reading files are committed to the repository. To rebuild them from their source editions:

```bash
python3 scripts/import_classics.py
```

Pass one or more book IDs to rebuild only those editions. `PARALLEL_SOURCE_CACHE=/path/to/html` can be used with the cache names recorded in the importer during offline development.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for edition sources and reuse notes.
