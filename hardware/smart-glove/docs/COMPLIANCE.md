# SignSpeak Smart Glove — Compliance & Certification Guide

Company: **Man Who Embed** · Product: **SignSpeak Smart Glove** · PCB Rev H

This package makes the design **certification-ready**. Formal **CE / FCC / UL marks** are issued only by accredited labs after testing a finished product (glove + battery + enclosure + firmware). The PCB alone cannot be “CE certified.”

## 1. Radio (FCC / CE RED)

| Item | Approach |
|------|----------|
| Radio module | **ESP32-WROOM-32E** (Espressif modular grant) |
| Integrator duty | Follow Espressif module integration notes: antenna keep-out, no metal over antenna, host labeling |
| US (FCC) | Modular transmitter approval — end product may use module grant if conditions met; otherwise permissive change / full test |
| EU (RED) | Module helps; finished product still needs RF + EMC + safety assessment for placing on market |
| Labeling | Include Espressif FCC ID / CE module info on packaging + e-label as required |

**Design controls on Rev H**

- Antenna keep-out zone at finger edge (no copper pour in keep-out).
- USB / battery connectors placed at wrist edge, away from antenna.
- Mounting guidance: non-metal glove plate under antenna (see `RF_MOUNTING.md`).

**Next step for sale:** book a lab for host-product RF/EMC (and RED Article 3.1a/3.1b/3.2 as applicable).

## 2. USB

Rev H routes USB-C **D+/D−** to an onboard **CH340C** (USB 2.0 Full-Speed device for programming/serial only).

- Not a USB battery pack / BC1.2 dedicated charging port claim unless retested.
- Use for **data + 5 V power** to the glove electronics / TP4056 input.
- ESD: handle with care; add TVS (e.g. USBLC6) in next spin if lab requires.

## 3. Battery safety (UN38.3 / IEC 62133 / UL)

Rev H includes **DW01A + FS8205A** pack protection (over-charge / over-discharge / over-current) in addition to **TP4056** charge management.

| Control | Part |
|---------|------|
| Charge | TP4056 (~1 A with 1.2 k PROG) |
| Pack protect | DW01A + FS8205A |
| Cell | Use **1S LiPo** with correct polarity on J3 |

Still required for commercial sale:

- Use cells with **UN38.3** documentation from the cell vendor.
- Follow shipping rules for Li-ion.
- Consider UL/IEC system evaluation if marketed as a wearable with battery.

## 4. Electrical safety / EMC

- 5 V USB powered; no hazardous mains voltages on PCB.
- 2-layer FR4 1.55 mm · 0.15 mm min track/clearance (fab capability class).
- EMC: keep cable lengths short; ferrite on USB cable if lab asks.

## 5. Documents to give a lab

1. Schematic + PCB Gerbers (this repo `fab/`)
2. BOM with manufacturer PNs (`BOM-JLCPCB.csv`)
3. Firmware version hash
4. Photos of glove assembly + antenna clearance
5. This compliance note + Espressif module certificates (download from Espressif)

## 6. Honest status

| Claim | Status |
|-------|--------|
| PCB DRC / fab rules | Pass (prototype production) |
| Modular RF design practice | Implemented |
| USB serial for field programming | Implemented (CH340) |
| LiPo hardware protection | Implemented (DW01+8205) |
| CE/FCC/UL **certificate on file** | **Not issued here** — obtain via lab on finished glove |
