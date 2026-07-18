# Smart Glove MCU — Fabrication Package (Rev A)

## Board specs (JLCPCB / PCBWay ready)

| Parameter | Value |
|-----------|-------|
| Dimensions | 50.0 × 42.0 mm |
| Layers | 2 (F.Cu + B.Cu) |
| Thickness | 1.6 mm |
| Copper | 1 oz (35 µm) |
| Min track / clearance | 0.15 mm / 0.15 mm |
| Min via | 0.45 mm / 0.3 mm drill |
| Surface finish | ENIG or HASL Lead-Free |
| Solder mask | Green (or black) |
| Silkscreen | White |
| Edge | Contour rout from Edge.Cuts |

## Upload to JLCPCB

1. Zip contents of `gerbers/`
2. Upload zip → confirm layer mapping
3. Optional SMT assembly: upload `BOM-JLCPCB.csv` + `CPL-top.csv`
4. Order **5 pcs** prototype first

## Included manufacturing outputs

- Gerbers: F.Cu, B.Cu, F.Mask, B.Mask, F.Paste, F.SilkS, B.SilkS, Edge.Cuts
- Excellon drill
- Pick-and-place (CPL) for top side
- BOM with LCSC part numbers

## Bring-up checklist

1. Visual inspect / shorts on 5V, BAT, 3V3
2. USB 5V present on TP4056 VCC
3. Battery charge LED works
4. 3V3 rail ≈ 3.3 V with AMS1117
5. ESP32 USB-serial boot (hold BOOT)
6. ADC read on FLEX1–4
7. `i2cdetect` shows MPU-6050 at 0x68

## Electrical notes

- Flex sensors are **off-board**, wired to J2
- USB data nets named USB_DP/USB_DN; for native ESP32 programming use an external USB-UART or ESP32-S3 redesign if you need native USB
- Charge current ≈ 1000 mA with Rprog 1.2 kΩ — reduce for small LiPo (e.g. 4.7k ≈ 250 mA)
