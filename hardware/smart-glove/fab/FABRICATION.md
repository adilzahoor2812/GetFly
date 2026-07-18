# Smart Glove MCU — Fabrication (Rev D)

## Status
- ERC: ERC messages: 0  Errors 0  Warnings 0
- DRC violations: 0 (errors: 0)
- Unconnected items: 0
- Production gate: PASS — OK to order 5 pcs prototype

## Board
- Size: 95 × 72 mm · 2-layer · 1.6 mm FR4
- Finish: ENIG or HASL (JLCPCB)
- Min track/clearance: 0.15 mm · Min drill: 0.20 mm
- GND zones filled on F.Cu / B.Cu
- Signals/power autorouted (Freerouting) then zone-filled; rebuild via `python3 build_production_v2.py`

## Files
- `SmartGlove_MCU_RevD_Gerbers.zip`
- `BOM-JLCPCB.csv` / `CPL-top.csv`

## Bring-up
1. Continuity: no shorts on GND / 3V3 / +5V / +BAT
2. USB → TP4056 → battery → AMS1117 → 3V3
3. Flash ESP32 via USB-UART (BOOT/EN)
4. Flex ADC + MPU-6050 I2C

USB-C is power/charge oriented (CC 5.1k). Keep metal clear of antenna keep-out band.
