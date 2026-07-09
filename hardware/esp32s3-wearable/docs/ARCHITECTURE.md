# System Architecture

## Block diagram

```
                    ┌─────────────────────────────────────┐
                    │           USB-C (J4)                │
                    │     VBUS + D+ + D- + CC             │
                    └──────────┬──────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────────┐
        │ MCP73831 │    │ USBLC6-2 │    │  ESP32-S3    │
        │ Charger  │    │   ESD    │    │  WROOM-1     │
        └────┬─────┘    └──────────┘    │              │
             │                            │  WiFi/BT     │
    ┌────────┴────────┐                  │  Native USB  │
    │  Li-Po 3.7V     │                  │              │
    │  (JST J1)       │                  └───┬────┬─────┘
    └────────┬────────┘                      │    │
             │                          SPI  │    │ GPIO
        ┌────┴─────┐                        │    │
        │ DW01A    │                        ▼    ▼
        │ Protect  │              ┌─────────┐ ┌────────┐
        └────┬─────┘              │ LS013   │ │ 6-Key  │
             │                    │ Memory  │ │ Keypad │
        ┌────┴─────┐              │  LCD    │ │        │
        │ AP2112K  │              └─────────┘ └────────┘
        │ 3.3V LDO │
        └────┬─────┘
             │
           +3V3 rail
```

## Power domains

| Rail | Source | Loads |
|------|--------|-------|
| VBAT | Li-Po cell | Charger, LDO input |
| VSYS | Charger output / battery | LDO, charge path |
| +3V3 | AP2112K LDO | ESP32-S3, LCD, keys, USB IC |

## Low-power strategy

1. **Memory LCD** holds image without refresh — near-zero static display power
2. **EXTCOM** toggled only when display is active (~1 Hz inversion)
3. **ESP32-S3 deep sleep** between user interactions
4. **Keys on RTC GPIO** wake MCU from sleep
5. **Backlight omitted** — reflective LCD needs no LED power

## Schematic sheets

| Sheet | Responsibility |
|-------|----------------|
| power.kicad_sch | Battery, protection, charging, regulation |
| mcu.kicad_sch | ESP32-S3, decoupling, reset/boot |
| usb.kicad_sch | USB-C connector, CC, ESD |
| display.kicad_sch | LCD connector, SPI, EXTCOM |
| keypad.kicad_sch | Six tactile switches with pull-ups |

## Mechanical integration

| PCB feature | Enclosure requirement |
|-------------|----------------------|
| J4 USB-C at left edge | Side slot cutout |
| J3 LCD connector at top | Display cavity above PCB |
| SW1–SW6 row | Button holes in overlay |
| H1–H4 M2 holes | Screw bosses in case |
| J1 battery at rear | Battery compartment |

Export PCB as STEP (**File → Export → STEP**) for Fusion 360 / FreeCAD case design.
