# GetFly Smart Glove — MCU PCB (Rev D)

ESP32-WROOM-32E · 4× flex · MPU-6050 · TP4056 · AMS1117-3.3 · USB-C

## Rebuild

```bash
python3 build_production_v2.py
```

Fab package: [`fab/`](fab/) (95×72 mm, 2-layer).

**Production gate (Rev D):** ERC 0 · DRC 0 · unconnected 0 — see [`fab/FABRICATION.md`](fab/FABRICATION.md).

Rebuild runs placement → Freerouting → GND pours → Gerbers/BOM/CPL → ERC/DRC.
Requires `/tmp/freerouting.jar` (or set path in `build_production_v2.py`).
