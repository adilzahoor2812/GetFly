# Smart Glove — Schematic & PCB

Recreated from the project collage (poster + glove hardware + schematic + PCB photos).

## Important limitation

The collage images are **too low-resolution to recover exact** net names, resistor values, or every copper trace. This package rebuilds the **same architecture** visible in the photos:

- Central MCU block (implemented as **ESP32-WROOM-32E**)
- **Four identical** flex-sensor interface channels
- Power / charge / 3.3 V regulation
- IMU block (MPU-6050)
- Dual-layer PCB (top red / bottom blue style)
- Edge connector for finger sensors + USB

If you can share a **higher-resolution** photo of the schematic or the KiCad/EasyEDA source, the design can be matched component-for-component.

## Files

| File | Description |
|------|-------------|
| `docs/smart_glove_schematic.png` | Annotated schematic diagram |
| `docs/smart_glove_pcb.png` | Dual-layer PCB preview |
| `smart-glove.kicad_pro` | KiCad 8 project |
| `smart-glove.kicad_sch` | Schematic stub / title sheet |
| `smart-glove.kicad_pcb` | 50×40 mm 2-layer board |
| `BOM.md` | Bill of materials |

## Board outline

- Size: **50 × 40 mm**
- Thickness: **1.6 mm**
- Layers: **F.Cu + B.Cu** with bottom GND pour
- Mounting: 4× M2 holes
- RF keep-out at ESP32 antenna end

## Open in KiCad

1. Install [KiCad 8+](https://www.kicad.org/)
2. Open `smart-glove.kicad_pro`
3. Assign official footprints from KiCad libraries (ESP32 module, USB-C, TP4056, etc.)
4. Finish routing / DRC, then **File → Fabrication Outputs → Gerbers**

## Flex sensor wiring

```
3V3 ── flex sensor ──●── ADC (GPIO36/39/34/35)
                     │
                   10k to GND
```

## Next steps for a 1:1 match

1. Photograph the original schematic at high resolution (or export from CAD)
2. Measure the physical PCB (outer dimensions, hole spacing)
3. Identify ICs from package markings under a loupe
4. Continuity-map flex connector pinout
