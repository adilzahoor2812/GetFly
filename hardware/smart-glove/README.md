# Smart Glove MCU — Production Package (Rev A)

ESP32-based smart-glove controller: **4 flex-sensor channels**, **MPU-6050**, **USB-C charge**, **LiPo + 3.3 V LDO**.

## Status

| Item | Status |
|------|--------|
| Footprints placed (36) | Done |
| Nets + critical routing | Done |
| Gerbers + Excellon drill | Done |
| JLCPCB BOM + CPL | Done |
| Automated design checks | Passed |
| KiCad GUI zone refill / visual DRC | Do once before volume run |
| Hardware bring-up | Order **5 pcs** prototype first |

This package is **fab-ready for prototype manufacturing** (JLCPCB / PCBWay).  
Treat the first lot as validation boards before mass production.

## Quick start — order PCBs

1. Upload `fab/SmartGlove_MCU_RevA_Gerbers.zip` to JLCPCB
2. Settings: **2 layers**, **1.6 mm**, **1 oz**, ENIG or HASL-LF
3. Optional SMT: `fab/BOM-JLCPCB.csv` + `fab/CPL-top.csv`
4. Qty: **5**

## Board specs

- Outline: **50 × 42 mm**
- Layers: **2**
- Min track/clearance: **0.15 mm**
- Via: **0.6 / 0.3 mm**
- Mounting: 4× M2

## Files

```
hardware/smart-glove/
├── smart-glove.kicad_pro      # KiCad 7 project
├── smart-glove.kicad_pcb      # Production PCB
├── smart-glove.kicad_sch      # Companion schematic sheet
├── build_production_board.py  # Regenerates board + fab outputs
├── docs/
│   ├── smart_glove_schematic.png
│   ├── pcb_production.png     # Rendered production board
│   ├── pcb_production.pdf
│   └── PRODUCTION_NETLIST.md
├── gerbers/                   # Individual Gerber/drill files
└── fab/
    ├── SmartGlove_MCU_RevA_Gerbers.zip
    ├── BOM-JLCPCB.csv
    ├── CPL-top.csv
    ├── FABRICATION.md
    └── drc_report.txt
```

## Rebuild

```bash
python3 build_production_board.py
```

Requires KiCad 7 (`kicad-cli`, `python3-pcbnew`).

## Architecture note

Rebuilt from the project collage architecture. Original photo labels were illegible; pinout follows Espressif ESP32-WROOM-32 + standard TP4056 / AMS1117 / MPU-6050 wiring.
