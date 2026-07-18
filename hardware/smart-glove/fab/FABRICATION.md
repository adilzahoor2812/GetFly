# SignSpeak Smart Glove — Fabrication (Rev G)

Company: **Man Who Embed**

## Status
- ERC: ERC messages: 2  Errors 0  Warnings 2
- DRC violations: 9 (errors: 0)
- Unconnected items: 0
- Production gate: PASS — OK to order 5 pcs prototype

## Board
- Name: SignSpeak Smart Glove
- Size: **60 × 45 mm** (compact glove-back) · 2-layer · 1.6 mm FR4
- Note: 40×30 mm is not possible with ESP32-WROOM-32E (~25.5 mm) + USB-C (~9.5 mm) + charger/IMU; 60×45 is the compact production size
- Orientation: top/finger = antenna · bottom/wrist = USB-C + LiPo + UART + flex
- Finish: ENIG or HASL (JLCPCB)
- Min track/clearance: 0.15 mm · Min drill: 0.20 mm
- 5× flex on J2 (1×7) · UART prog on J4 (1×4)
- Rebuild: `python3 build_production_v2.py`

## Files
- `SignSpeak_SmartGlove_RevG_Gerbers.zip`
- `BOM-JLCPCB.csv` / `CPL-top.csv`

## Flex connector J2
1=3V3 · 2=FLEX1 · 3=FLEX2 · 4=FLEX3 · 5=FLEX4 · 6=FLEX5 · 7=GND

## UART programming J4 (USB–UART dongle)
1=3V3 · 2=TX (ESP TXD0) · 3=RX (ESP RXD0) · 4=GND  
Dongle RX→board TX, dongle TX→board RX. Hold BOOT, tap EN, then upload.

## Bring-up
1. Continuity: no shorts on GND / 3V3 / +5V / +BAT
2. USB-C → TP4056 → battery → AMS1117 → 3V3 (power only)
3. Flash via **J4 UART** + BOOT/EN
4. 5× flex ADC + MPU-6050 I2C

USB-C is power/charge oriented (CC 5.1k). Keep metal clear of antenna keep-out band.
