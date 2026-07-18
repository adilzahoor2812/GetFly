# SignSpeak Smart Glove — MCU PCB (Rev E)

**Man Who Embed** · ESP32-WROOM-32E · **5× flex** · MPU-6050 · TP4056 · AMS1117-3.3 · USB-C

## Schematic (complete)

```bash
python3 build_complete_schematic.py
```

## Rebuild PCB + fab package

```bash
python3 build_production_v2.py
```

Fab: [`fab/SignSpeak_SmartGlove_RevE_Gerbers.zip`](fab/SignSpeak_SmartGlove_RevE_Gerbers.zip)  
(95×72 mm, 2-layer). See [`fab/FABRICATION.md`](fab/FABRICATION.md).

### Flex J2 (1×7)
`3V3 · FLEX1 · FLEX2 · FLEX3 · FLEX4 · FLEX5 · GND`  
ESP32: FLEX1–4 → pins 4–7 (GPIO36/39/34/35), FLEX5 → pin 8 (GPIO32).
