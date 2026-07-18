# SignSpeak Smart Glove — MCU PCB (Rev G)

**Man Who Embed** · **60×45 mm** glove-back · ESP32 · **5× flex** · MPU-6050 · TP4056 · AMS1117 · USB-C · **UART prog**

## Rebuild

```bash
python3 build_complete_schematic.py
python3 build_production_v2.py
```

Fab: [`fab/SignSpeak_SmartGlove_RevG_Gerbers.zip`](fab/SignSpeak_SmartGlove_RevG_Gerbers.zip)

### Mounting
- Top edge → toward fingers (antenna keep-out)
- Bottom edge → toward wrist (USB-C + LiPo + UART + flex)

### Flex J2 (1×7)
`3V3 · FLEX1 · FLEX2 · FLEX3 · FLEX4 · FLEX5 · GND`

### UART J4 (1×4) — code upload
`3V3 · TX · RX · GND` → USB–UART dongle (cross TX/RX)
