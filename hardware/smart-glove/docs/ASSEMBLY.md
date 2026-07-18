# SMT / assembly notes — SignSpeak Rev H

## Files

| File | Use |
|------|-----|
| `fab/SignSpeak_SmartGlove_RevH_Gerbers.zip` | JLCPCB / PCBWay gerbers |
| `fab/BOM-JLCPCB.csv` | BOM with **LCSC** part numbers |
| `fab/CPL-top.csv` | Pick-and-place (top) |

## Fab options (recommended prototype)

- Layers: **2**
- Thickness: **1.55 mm** (or 1.6 mm if 1.55 unavailable)
- Finish: **ENIG** preferred (USB-C + fine pitch)
- Min track/space: **0.15 / 0.15 mm**
- Min drill: **0.2 mm**
- Quantity: **5** first build

## Critical orientation

| Ref | Note |
|-----|------|
| U1 ESP32 | Antenna toward **top** board edge |
| J1 USB-C | Tongue toward board edge (wrist) |
| U2 TP4056 | Pin 1 mark |
| U5 CH340C | Pin 1 mark |
| U4 MPU-6050 | Pin 1 / polarity |
| U6 DW01 / U7 FS8205 | Match silkscreen |

## Post-assembly bring-up

1. No-battery: USB-C → measure **3V3** ≈ 3.3 V, **+5V** ≈ 5 V.
2. PC shows **CH340** serial port.
3. Flash `firmware/signspeak_glove`.
4. Connect protected 1S LiPo to **J3** (check polarity).
5. Confirm charge LED **D2** behavior.
6. Serial Monitor CSV stream at 115200.
