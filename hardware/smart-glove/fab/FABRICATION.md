# SignSpeak Smart Glove — Fabrication (Rev H)

Company: **Man Who Embed**

## Status
- ERC: ERC messages: 6  Errors 0  Warnings 6
- DRC violations: 7 (errors: 0)
- Unconnected items: 0
- Production gate: PASS — OK to order 5 pcs prototype

## Board
- Name: SignSpeak Smart Glove
- Size: **72 × 52 mm** · 2-layer · **1.55 mm** FR4
- USB-C **data + power** via onboard **CH340C** (laptop flash / Serial Monitor)
- LiPo pack protect: **DW01A + FS8205A**
- Orientation: top/finger = antenna · bottom/wrist = USB-C + LiPo + UART + flex
- Finish: **ENIG** preferred
- Min track/clearance: 0.15 mm · Min drill: 0.20 mm
- Rebuild: `python3 build_production_v2.py`

## Files
- `SignSpeak_SmartGlove_RevH_Gerbers.zip`
- `BOM-JLCPCB.csv` (LCSC filled) / `CPL-top.csv`
- Docs: `docs/COMPLIANCE.md` · `docs/ASSEMBLY.md` · `docs/RF_MOUNTING.md`
- Firmware: `firmware/signspeak_glove/`

## Flex J2
1=3V3 · 2=FLEX1 · 3=FLEX2 · 4=FLEX3 · 5=FLEX4 · 6=FLEX5 · 7=GND

## Upload / serial
1. Prefer **USB-C** → CH340 (auto DTR/RTS). Serial Monitor **115200**.
2. Backup **J4**: 3V3 · TX · RX · GND (cross TX/RX on dongle).

## Bring-up
1. USB-C → 5V / 3V3 present · CH340 port appears
2. Flash `firmware/signspeak_glove`
3. Connect 1S LiPo on J3 (observe polarity) · charge LED
4. Serial CSV: flex×5 + IMU
