# GetFly Smart Glove — MCU PCB (Rev D)

ESP32-WROOM-32E · 4× flex · MPU-6050 · TP4056 · AMS1117-3.3 · USB-C

## Schematic (complete)

Full KiCad schematic with all production parts, nets, and power flags:

```bash
python3 build_complete_schematic.py
```

Writes `smart-glove.kicad_sch` + `fab/smart-glove.kicad_sch.template`.  
**ERC gate:** 0 errors (embedded custom symbols may warn as “not found in Device”).

## Rebuild PCB + fab package

```bash
python3 build_production_v2.py
```

Fab package: [`fab/`](fab/) (95×72 mm, 2-layer).

**Production gate (Rev D):** ERC 0 · DRC 0 · unconnected 0 — see [`fab/FABRICATION.md`](fab/FABRICATION.md).

Rebuild runs complete schematic → placement → Freerouting → GND pours → Gerbers/BOM/CPL → ERC/DRC.  
Requires `/tmp/freerouting.jar` (or set path in `build_production_v2.py`).

## Net highlights

- ESP32 IO22 (pin 36) → SCL; pin 37 NC  
- MPU REGOUT → C10 2.2 µF → GND  
- USB-C SBU (A8/B8) left unconnected  
