# Satellite Flyover Finder

Single-file aerospace intelligence web app: find which Earth-observation satellites passed over any place on Earth.

## Open

```bash
cd satellite-flyover-finder
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8765/` in Chrome.

You can also open `index.html` directly, but some browsers restrict network calls from `file://`.

## What it does

- Geocode any place (Nominatim + Open-Meteo fallback) or paste coordinates
- Download CelesTrak TLEs (resource + weather groups), cache 2 hours
- SGP4 propagation via satellite.js
- 7-day pass scan with mission-specific ground distances
- Historical replay labelled as **approximate** (latest TLE — not verified history)
- Sentinel-2 / Landsat STAC imagery catalogue search (footprint match ≠ orbital proof)

## Data honesty

Orbital passes are geometric predictions. Imagery cards come from public STAC catalogues. Missing historical TLEs are never presented as verified observations.
