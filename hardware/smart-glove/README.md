# SignSpeak Smart Glove — MCU PCB (Rev H)

**Man Who Embed** · **72×52 mm** · ESP32 · **USB-C+CH340** · **DW01 protect** · 5× flex · MPU-6050 · 1.55 mm FR4

## Schematic
Open [`smart-glove.kicad_sch`](smart-glove.kicad_sch) — reference-style **labeled blocks** (USB-C, CH340, power, ESP32, flex, IMU, charge/protect).  
Preview: [`docs/schematic_preview.png`](docs/schematic_preview.png)  
Rebuild: `python3 build_complete_schematic.py`

## Rebuild

```bash
python3 build_complete_schematic.py
python3 build_production_v2.py
```

Fab: [`fab/SignSpeak_SmartGlove_RevH_Gerbers.zip`](fab/SignSpeak_SmartGlove_RevH_Gerbers.zip)

Firmware: [`../../firmware/signspeak_glove/`](../../firmware/signspeak_glove/)

### Docs
- [COMPLIANCE](docs/COMPLIANCE.md) · [ASSEMBLY](docs/ASSEMBLY.md) · [RF_MOUNTING](docs/RF_MOUNTING.md) · [BOM](BOM.md)

### Upload
Laptop → **USB-C** (CH340) → Arduino upload + Serial Monitor @ 115200  
Backup: **J4** UART header
