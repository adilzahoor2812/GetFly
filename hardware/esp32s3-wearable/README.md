# ESP32-S3 Wearable Field Device — KiCad PCB Project

Compact **ESP32-S3** embedded device with **sunlight-readable Sharp memory LCD**, **Li-ion battery management**, **USB-C**, **6-key keypad**, and **low-power** architecture.

| Spec | Value |
|------|-------|
| MCU | ESP32-S3-WROOM-1-N8 |
| Display | Sharp LS013B7DH03 (128×128 memory LCD) |
| Battery | 3.7 V Li-Po (~1200 mAh) via JST PH-2.0 |
| Charger | MCP73831 (~500 mA via 2 kΩ PROG) |
| Regulator | AP2112K-3.3 |
| USB | USB-C (native ESP32-S3 USB) |
| Board size | 42 × 34 mm, 2-layer, 1.6 mm |
| Keys | UP, DOWN, LEFT, RIGHT, ENTER, BACK |

---

## Project structure

```
esp32s3-wearable/
├── esp32s3-wearable.kicad_pro    ← Open this in KiCad
├── esp32s3-wearable.kicad_sch    ← Root schematic (5 sub-sheets)
├── esp32s3-wearable.kicad_pcb    ← PCB layout (placement starter)
├── sheets/
│   ├── power.kicad_sch
│   ├── mcu.kicad_sch
│   ├── usb.kicad_sch
│   ├── display.kicad_sch
│   └── keypad.kicad_sch
├── generate_project.py           ← Regenerate files if needed
├── exports/bom.csv               ← Bill of materials
├── firmware/pins.h               ← GPIO map for firmware
└── docs/
    ├── GPIO.md
    └── ARCHITECTURE.md
```

---

## Step 1 — Open in KiCad

1. Install **KiCad 8** from https://www.kicad.org/download/
2. Open **KiCad Project Manager**
3. **File → Open Project**
4. Select `esp32s3-wearable.kicad_pro`

---

## Step 2 — Review schematic

1. Click **Schematic Editor**
2. Double-click each sheet box to open sub-sheets:
   - **Power** — battery, charger, LDO
   - **MCU** — ESP32-S3
   - **USB** — USB-C + ESD
   - **Display** — memory LCD connector
   - **Keypad** — 6 switches
3. If KiCad asks to **rescue/assign symbols**, accept and map to default KiCad libraries
4. **Wire any unconnected pins** using the reference GPIO map in `docs/GPIO.md`
5. Run **Inspect → Electrical Rules Checker (ERC)** and fix errors

---

## Step 3 — Assign / verify footprints

1. **Tools → Assign Footprints**
2. Confirm footprints match `exports/bom.csv`
3. **Save**

---

## Step 4 — Update PCB

1. Open **PCB Editor**
2. **Tools → Update PCB from Schematic** (F8)
3. Click **Update PCB**
4. Components appear on board (starter placement included)

---

## Step 5 — Complete PCB layout

The included PCB has **board outline**, **mounting holes**, **antenna keep-out**, and **starter placement**. You still need to:

- [ ] Route all nets (especially **USB D+/D−** as short pair)
- [ ] Place remaining passives (0402/0603 caps and resistors)
- [ ] Add **GND copper pour** on bottom layer
- [ ] Keep **clear zone** under ESP32-S3 antenna (marked on `Cmts.User` layer)
- [ ] Run **Inspect → Design Rules Checker (DRC)** until clean
- [ ] Check **3D View** (Alt+3) for connector heights

### Placement guide

```
+------------------------------------------+
|  [LCD J3]              [ESP32-S3 antenna→]|
|  SW1  SW2  SW3  SW4  SW5  SW6             |
| [USB-C]                                   |
|                          [JST BAT] [PWR]  |
+------------------------------------------+
  H1                                    H2
  H3                                    H4
```

---

## Step 6 — Export Gerbers

1. PCB Editor → **File → Plot**
2. Output folder: `exports/gerbers/`
3. Layers: F.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts
4. Click **Plot**
5. **File → Fabrication Outputs → Drill Files**
6. **File → Fabrication Outputs → Footprint Positions** (for assembly)
7. Upload Gerbers + `exports/bom.csv` to **JLCPCB** or **PCBWay**

---

## Step 7 — Order parts

Use `exports/bom.csv`. Order separately:

- **LCD**: Sharp LS013B7DH03 (or LCSC equivalent)
- **Battery**: 3.7 V Li-Po 1200 mAh with JST PH-2.0 connector
- **PCB + SMT parts**: JLCPCB PCBA recommended for 0402 passives

---

## Step 8 — Bring-up

1. Current-limit bench supply on battery input first
2. Verify **+3.3 V** rail
3. Connect USB-C → check charging
4. Flash firmware using `firmware/pins.h` GPIO definitions
5. Test keys → display → sleep current

---

## Regenerate project files

```bash
cd hardware/esp32s3-wearable
python3 generate_project.py
```

---

## Important notes before fabrication

1. **Verify LCD connector pinout** against LS013B7DH03 datasheet — update `J3` if using FPC instead of pin header
2. **Check ESP32-S3 strapping pins** (GPIO0, 3, 45, 46) — see Espressif datasheet
3. **USB-C footprint** must match your exact connector part number
4. This is **Rev A starter** — run ERC/DRC and review before ordering

---

## Related docs

- [GPIO mapping](docs/GPIO.md)
- [System architecture](docs/ARCHITECTURE.md)
