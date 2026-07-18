# Smart Glove Controller — Bill of Materials (Rev A)

| Ref | Part | Value / Spec | Qty | Notes |
|-----|------|--------------|-----|-------|
| U1 | ESP32-WROOM-32E | Wi-Fi/BLE MCU module | 1 | Central MCU (collage) |
| U2 | TP4056 | LiPo charger IC / module | 1 | USB charge path |
| U3 | AMS1117-3.3 | 3.3 V LDO | 1 | Regulated rail |
| U4 | MPU-6050 | 6-axis IMU | 1 | Gesture / orientation |
| J1 | USB-C receptacle | 16-pin mid-mount | 1 | Charge + program |
| J2 | Pin header 1×6 | 2.54 mm | 1 | Flex sensor cable |
| BT1 | LiPo cell | 3.7 V 300–500 mAh | 1 | JST-PH |
| FS1–FS4 | Flex sensor | 2.2" ~10k–40k | 4 | Index/Middle/Ring/Pinky |
| R1–R4 | Resistor 0603 | 10 kΩ | 4 | Voltage dividers |
| R5 | Resistor 0603 | 1 kΩ | 1 | Power LED |
| R6–R7 | Resistor 0603 | 5.1 kΩ | 2 | USB-C CC |
| C1–C4 | Cap 0603 | 100 nF | 4 | Decoupling |
| C5 | Cap 1206 | 10 µF | 1 | LDO input |
| C6 | Cap 1206 | 22 µF | 1 | LDO output |
| D1–D3 | LED 0603 | Power / CHRG / Status | 3 | Indicators |
| SW1 | Tactile switch | BOOT | 1 | Download mode |
| H1–H4 | M2 hardware | 2.2 mm holes | 4 | Case mount |

> Photo labels in the collage were not readable. Values above are standard defaults for this architecture — adjust after measuring your original board.
