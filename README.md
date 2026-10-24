# Parallel

Parallel is a mobile-first bilingual e-reader for reading English works in Russian or German. The target-language text stays central, while the original English and pronunciation are available on demand.

## Current prototype

- Russian and German reading editions
- Sentence-level English reveal
- Device text-to-speech playback
- E-paper, light, and app-wide dark themes
- Responsive phone and tablet layouts
- EPUB/TXT import flow ready for a translation backend
- Installable web-app foundation with offline caching

## Run locally

```bash
python3 -m http.server 4173 --bind 0.0.0.0 --directory dist
```

Open `http://localhost:4173` on the computer, or use the computer's LAN IP from another device on the same network.

## Verify

```bash
node tests/static-contract.mjs
node --check dist/app.js
node --check dist/sw.js
```

Automated whole-book translation and durable private library storage are not connected in this prototype.
