# SignSpeak Smart Glove — Fabrication (Rev F)

Company: **Man Who Embed**

## Status
- ERC: ERC messages: 2  Errors 0  Warnings 2
- DRC violations: 1 (errors: 0)
- Unconnected items: 0
- Production gate: PASS — OK to order 5 pcs prototype

## Board
- Name: SignSpeak Smart Glove
- Size: **75 × 52 mm** (compact glove-back) · 2-layer · 1.6 mm FR4
- Orientation: top/finger edge = flex + antenna · bottom/wrist = USB-C + LiPo
- Finish: ENIG or HASL (JLCPCB)
- Min track/clearance: 0.15 mm · Min drill: 0.20 mm
- 5× flex on J2 (1×7): 3V3, FLEX1…FLEX5, GND
- Rebuild: `python3 build_production_v2.py`

## Files
- `SignSpeak_SmartGlove_RevF_Gerbers.zip`
- `BOM-JLCPCB.csv` / `CPL-top.csv`

## Flex connector J2
1=3V3 · 2=FLEX1 · 3=FLEX2 · 4=FLEX3 · 5=FLEX4 · 6=FLEX5 · 7=GND

## Bring-up
1. Continuity: no shorts on GND / 3V3 / +5V / +BAT
2. USB → TP4056 → battery → AMS1117 → 3V3
3. Flash ESP32 via USB-UART (BOOT/EN)
4. 5× flex ADC + MPU-6050 I2C

USB-C is power/charge oriented (CC 5.1k). Keep metal clear of antenna keep-out band.
