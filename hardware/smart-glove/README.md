# GetFly Smart Glove — MCU PCB (Rev D)

ESP32-WROOM-32E · 4× flex · MPU-6050 · TP4056 · AMS1117-3.3 · USB-C

## Schematic (complete)

```bash
python3 build_complete_schematic.py
```

Full schematic with all production parts. ERC gate: 0 errors.

## Rebuild PCB + fab package

```bash
python3 build_production_v2.py
```

Fab package: [`fab/`](fab/) (95×72 mm, 2-layer).  
Production gate documented in [`fab/FABRICATION.md`](fab/FABRICATION.md).

Net parity: ESP32 pin 36 = SCL · MPU REGOUT → C10 2.2 µF · USB SBU NC.
