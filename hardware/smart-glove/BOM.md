# Smart Glove MCU — Bill of Materials (Rev A)

See also `fab/BOM-JLCPCB.csv` for SMT assembly upload.

| Ref | Part | Footprint | Qty | LCSC | Assemble |
|-----|------|-----------|-----|------|----------|
| U1 | ESP32-WROOM-32E | RF_Module:ESP32-WROOM-32 | 1 | C701341 | Yes |
| U2 | TP4056 | SOIC-8_3.9x4.9mm | 1 | C16581 | Yes |
| U3 | AMS1117-3.3 | SOT-223 | 1 | C6186 | Yes |
| U4 | MPU-6050 | QFN-24 4×4 | 1 | C24112 | Yes |
| J1 | USB-C 16P | HRO TYPE-C-31-M-12 | 1 | C165948 | Yes |
| J2 | Header 1×6 | 2.54 mm vertical | 1 | — | No |
| J3 | JST-PH 2P | B2B-PH-K | 1 | C160404 | Yes |
| R1–R4,R9,R10 | 10 kΩ 0603 | R_0603 | 6 | C25804 | Yes |
| R5 | 1 kΩ 0603 | R_0603 | 1 | C21190 | Yes |
| R6,R7 | 5.1 kΩ 0603 | R_0603 | 2 | C23162 | Yes |
| R8 | 1.2 kΩ 0603 | R_0603 | 1 | C22955 | Yes |
| C1–C4,C7–C9 | 100 nF 0603 | C_0603 | 7 | C14663 | Yes |
| C5 | 10 µF 0805 | C_0805 | 1 | C15850 | Yes |
| C6 | 22 µF 0805 | C_0805 | 1 | C45783 | Yes |
| C10 | 2.2 µF 0805 | C_0805 | 1 | C1779 | Yes |
| D1–D3 | LED 0603 | LED_0603 | 3 | C2286 | Yes |
| SW1,SW2 | Tactile B3U-1000P | SMD switch | 2 | C318884 | Yes |
| H1–H4 | M2 hole | 2.2 mm | 4 | — | No |
| FS1–FS4 | Flex sensor 2.2\" | off-board | 4 | — | No |
| BT1 | LiPo 3.7 V ~400 mAh | off-board | 1 | — | No |

**Charge current note:** R8 = 1.2 kΩ ≈ 1 A. For a 400 mAh cell use ~4.7 kΩ (~250 mA).
