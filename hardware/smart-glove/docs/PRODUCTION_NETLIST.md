# Production Netlist — Smart Glove MCU Rev A

## Power

```
USB-C VBUS ──► U2 TP4056 VCC
                ├─ CE pulled to VCC
                ├─ PROG ── R8 1.2k ── GND
                └─ BAT ──► +BAT ──► J3-1 LiPo+
                             └─► U3 AMS1117 VIN
                                   └─ VOUT ──► 3V3 rail
USB-C GND / LiPo- / U2 GND / U3 GND ──► GND pour
```

## Flex channels

```
J2-1 3V3 ──► Flex sensor HI (off-board)
Flex sense node ──► J2-2..5 (FLEX1..4) ──► ESP32 GPIO36/39/34/35
                 └─► R1..R4 10k ──► GND
```

## IMU

```
U4 MPU-6050
  VDD/VLOGIC ── 3V3
  GND/AD0 ── GND (addr 0x68)
  SDA ── ESP32 IO21
  SCL ── ESP32 IO22
  INT ── ESP32 IO19
  REGOUT ── C10 2.2uF ── GND
```

## Controls / LEDs

```
SW1 BOOT ── IO0 to GND (momentary), R10 10k pullup to 3V3
SW2 EN/RST ── EN to GND (momentary), R9 10k pullup to 3V3
D1 power LED via R5 from 3V3
D2 CHRG from TP4056 CHRG
D3 status on IO2
```
