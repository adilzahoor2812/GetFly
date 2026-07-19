# SignSpeak Smart Glove — Bill of Materials (Rev H)

Company: **Man Who Embed**  
Upload for JLCPCB: `fab/BOM-JLCPCB.csv` + `fab/CPL-top.csv`

| Ref | Part | Footprint | Qty | LCSC | Assemble |
|-----|------|-----------|-----|------|----------|
| U1 | ESP32-WROOM-32E | ESP32-WROOM-32 | 1 | C2934560 | Yes |
| U2 | TP4056 | SOIC-8 | 1 | C16581 | Yes |
| U3 | AMS1117-3.3 | SOT-223 | 1 | C6186 | Yes |
| U4 | MPU-6050 | QFN-24 4×4 | 1 | C24112 | Yes |
| U5 | CH340C | SOIC-16 | 1 | C84681 | Yes |
| U6 | DW01A | SOT-23-6 | 1 | C351558 | Yes |
| U7 | FS8205A | TSSOP-8 | 1 | C351546 | Yes |
| J1 | USB-C 16P | HRO TYPE-C-31-M-12 | 1 | C165948 | Yes |
| J2 | Header 1×7 (flex) | 2.54 mm vertical | 1 | C492406 | Yes (THT) |
| J3 | JST-PH 2P (LiPo) | B2B-PH-K | 1 | C160402 | Yes |
| J4 | Header 1×4 (UART) | 2.54 mm vertical | 1 | C124378 | Yes (THT) |
| R1–R4, R9–R11 | 10 kΩ 0603 | R_0603 | 7 | C25804 | Yes |
| R5, R12 | 1 kΩ 0603 | R_0603 | 2 | C21190 | Yes |
| R6, R7 | 5.1 kΩ 0603 | R_0603 | 2 | C23186 | Yes |
| R8 | 1.2 kΩ 0603 | R_0603 | 1 | C22949 | Yes |
| C1, C2, C7, C9, C11–C15 | 100 nF 0603 | C_0603 | 9 | C14663 | Yes |
| C5 | 10 µF 0805 | C_0805 | 1 | C15850 | Yes |
| C6 | 22 µF 0805 | C_0805 | 1 | C45783 | Yes |
| C10 | 2.2 µF 0805 | C_0805 | 1 | C23629 | Yes |
| D1, D3 | LED 0603 | LED_0603 | 2 | C2290 | Yes |
| D2 | LED-CHRG 0603 | LED_0603 | 1 | C2297 | Yes |
| SW1, SW2 | Tactile B3U-1000P | SMD switch | 2 | C318884 | Yes |
| H1–H4 | M2 hole | 2.2 mm | 4 | — | No (holes only) |
| FS1–FS5 | Flex sensor | off-board | 5 | — | No |
| BT1 | LiPo 3.7 V 1S | off-board | 1 | — | No |

**Flex J2:** 3V3 · FLEX1…FLEX5 · GND  

**JLCPCB note:** J2/J4 are through-hole — enable **through-hole assembly** (or hand-solder if SMT-only). All other listed parts are SMD.
