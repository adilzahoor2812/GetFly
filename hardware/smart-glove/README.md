# SignSpeak Smart Glove — MCU PCB (Rev F)

**Man Who Embed** · **75×52 mm** glove-back · ESP32 · **5× flex** · MPU-6050 · TP4056 · AMS1117 · USB-C

## Rebuild

```bash
python3 build_complete_schematic.py
python3 build_production_v2.py
```

Fab: [`fab/SignSpeak_SmartGlove_RevF_Gerbers.zip`](fab/SignSpeak_SmartGlove_RevF_Gerbers.zip)

### Mounting
- Top edge → toward fingers (flex cable + antenna keep-out)
- Bottom edge → toward wrist (USB-C + LiPo JST)

### Flex J2 (1×7)
`3V3 · FLEX1 · FLEX2 · FLEX3 · FLEX4 · FLEX5 · GND`
