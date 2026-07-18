# Production Netlist — SignSpeak Smart Glove Rev E

Company: Man Who Embed

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

## Flex channels (5 sensors)

```
J2-1 3V3 ──► all flex sensor HI (shared)
J2-2 FLEX1 ──► ESP32 GPIO36 (pin 4)  + R1 10k ── GND
J2-3 FLEX2 ──► ESP32 GPIO39 (pin 5)  + R2 10k ── GND
J2-4 FLEX3 ──► ESP32 GPIO34 (pin 6)  + R3 10k ── GND
J2-5 FLEX4 ──► ESP32 GPIO35 (pin 7)  + R4 10k ── GND
J2-6 FLEX5 ──► ESP32 GPIO32 (pin 8)  + R11 10k ── GND
J2-7 GND
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
SW1 BOOT ── IO0 to GND, R10 10k pullup to 3V3
SW2 EN/RST ── EN to GND, R9 10k pullup to 3V3
D1 power LED via R5 from 3V3
D2 CHRG from TP4056 CHRG
D3 status on IO2
```
