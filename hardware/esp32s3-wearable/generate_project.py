#!/usr/bin/env python3
"""
Generate KiCad 8 project for ESP32-S3 wearable field device.

Outputs:
  - esp32s3-wearable.kicad_pro
  - esp32s3-wearable.kicad_sch (root hierarchical sheet)
  - sheets/*.kicad_sch (power, mcu, usb, display, keypad)
  - esp32s3-wearable.kicad_pcb
  - sym-lib-table / fp-lib-table
  - exports/bom.csv
  - firmware/pins.h
"""

from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHEETS = ROOT / "sheets"


def uid() -> str:
    return str(uuid.uuid4())


def esc(s: str) -> str:
    return s.replace('"', '\\"')


# ---------------------------------------------------------------------------
# Schematic helpers
# ---------------------------------------------------------------------------

def sch_header(title: str) -> str:
    return f"""(kicad_sch
\t(version 20231120)
\t(generator "esp32s3-wearable-generator")
\t(uuid "{uid()}")
\t(paper "A3")
\t(title_block
\t\t(title "{esc(title)}")
\t\t(date "2026-07-06")
\t\t(rev "A")
\t\t(company "Field Device Prototype")
\t\t(comment 1 "ESP32-S3 + Sharp Memory LCD + 6-Key Keypad")
\t\t(comment 2 "Low-power wearable / field terminal")
\t)
\t(lib_symbols
"""


def sch_footer(sheet_instances: str = "") -> str:
    inst = sheet_instances or f"""\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)"""
    return f"""{inst}
\t(embedded_fonts no)
)
"""


def sym_property(name: str, value: str, pos: tuple[int, int], show: int = 0) -> str:
    x, y = pos
    return f"""\t\t(property "{name}" "{esc(value)}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left bottom)
\t\t\t)
\t\t)
\t\t(show "{name}" {show})
"""


def schematic_symbol(
    lib_id: str,
    ref: str,
    value: str,
    footprint: str,
    at: tuple[float, float, float],
    properties: dict[str, str] | None = None,
) -> str:
    x, y, rot = at
    props = properties or {}
    prop_lines = ""
    prop_lines += sym_property("Reference", ref, (x, y - 3.81), 1)
    prop_lines += sym_property("Value", value, (x, y + 3.81), 1)
    prop_lines += sym_property("Footprint", footprint, (x, y + 7.62))
    for k, v in props.items():
        prop_lines += sym_property(k, v, (x, y + 11.43))

    return f"""
\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} {rot})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
{prop_lines}
\t\t(pin "1" (uuid "{uid()}"))
\t)
"""


def global_label(name: str, x: float, y: float, rot: int = 0) -> str:
    return f"""
\t(global_label "{esc(name)}"
\t\t(shape input)
\t\t(at {x} {y} {rot})
\t\t(fields_autoplaced yes)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify left)
\t\t)
\t\t(uuid "{uid()}")
\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t)
"""


def hierarchical_pin(name: str, x: float, y: float, direction: str, rot: int = 0) -> str:
    return f"""
\t(pin "{esc(name)}" {direction}
\t\t(at {x} {y} {rot})
\t\t(uuid "{uid()}")
\t)
"""


def hierarchical_sheet(name: str, filename: str, x: float, y: float, w: float, h: float, pins: list[tuple[str, float, float, str]]) -> str:
    pin_block = ""
    for pname, px, py, pdir in pins:
        pin_block += hierarchical_pin(pname, px, py, pdir)
    return f"""
\t(sheet
\t\t(at {x} {y})
\t\t(size {w} {h})
\t\t(fields_autoplaced yes)
\t\t(stroke
\t\t\t(width 0.1524)
\t\t\t(type solid)
\t\t)
\t\t(fill
\t\t\t(color 0 0 0 0.0000)
\t\t)
\t\t(uuid "{uid()}")
\t\t(property "Sheetname" "{esc(name)}"
\t\t\t(at {x} {y - 2.54} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left bottom)
\t\t\t)
\t\t)
\t\t(property "Sheetfile" "{esc(filename)}"
\t\t\t(at {x} {y + h + 2.54} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left top)
\t\t\t)
\t\t)
{pin_block}
\t)
"""


def wire(x1: float, y1: float, x2: float, y2: float) -> str:
    return f"""
\t(wire
\t\t(pts
\t\t\t(xy {x1} {y1}) (xy {x2} {y2})
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{uid()}")
\t)
"""


def text_note(content: str, x: float, y: float) -> str:
    return f"""
\t(text "{esc(content)}"
\t\t(exclude_from_sim no)
\t\t(at {x} {y} 0)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify left top)
\t\t)
\t\t(uuid "{uid()}")
\t)
"""


def power_symbol(name: str, x: float, y: float) -> str:
    return f"""
\t(power "{esc(name)}"
\t\t(at {x} {y} 0)
\t\t(uuid "{uid()}")
\t)
"""


def no_connect(x: float, y: float) -> str:
    return f"""
\t(no_connect
\t\t(at {x} {y})
\t\t(uuid "{uid()}")
\t)
"""


# ---------------------------------------------------------------------------
# Sheet content builders
# ---------------------------------------------------------------------------

def build_power_sheet() -> str:
    """Battery, protection, charger, LDO."""
    body = sch_header("Power - Battery & Regulation")
    body += "\t)\n"  # empty lib_symbols close - KiCad will resolve from libraries

    notes = text_note(
        "POWER SHEET\\n"
        "VBAT -> DW01+8205A protection -> MCP73831 charger\\n"
        "VSYS -> AP2112K-3.3 -> +3V3 rail\\n"
        "R1=2k sets ~500mA charge (MCP73831 PROG)\\n"
        "R2/R3=100k battery divider -> VBAT_ADC",
        25.4, 25.4,
    )
    body += notes

    parts = [
        ("Connector_JST:JST_PH_B2B-PH-K-S_Leads", "J1", "BAT_CONN", "Connector_JST:JST_PH_B2B-PH-K-S_Leads", (50.8, 76.2, 0)),
        ("Power_Protection:DW01", "U4", "DW01A", "Package_TO_SOT_SMD:SOT-23-6", (101.6, 50.8, 0)),
        ("Battery_Management:MCP73831-2-AC", "U2", "MCP73831", "Package_TO_SOT_SMD:SOT-23-5", (152.4, 50.8, 0)),
        ("Regulator_Linear:AP2112K-3.3", "U3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5", (203.2, 50.8, 0)),
        ("Device:R", "R1", "2k", "Resistor_SMD:R_0402_1005Metric", (127.0, 88.9, 0)),
        ("Device:R", "R2", "100k", "Resistor_SMD:R_0402_1005Metric", (177.8, 88.9, 0)),
        ("Device:R", "R3", "100k", "Resistor_SMD:R_0402_1005Metric", (190.5, 88.9, 0)),
        ("Device:C", "C1", "10uF", "Capacitor_SMD:C_0603_1608Metric", (228.6, 76.2, 0)),
        ("Device:C", "C2", "10uF", "Capacitor_SMD:C_0603_1608Metric", (241.3, 76.2, 0)),
        ("Device:C", "C3", "100nF", "Capacitor_SMD:C_0402_1005Metric", (254.0, 76.2, 0)),
        ("Device:LED", "D1", "CHG_LED", "LED_SMD:LED_0603_1608Metric", (139.7, 88.9, 90)),
        ("Device:R", "R4", "1k", "Resistor_SMD:R_0402_1005Metric", (139.7, 76.2, 90)),
    ]
    for p in parts:
        body += schematic_symbol(*p)

    # Hierarchical pins on sheet edge
    sheet_x, sheet_y = 0, 0
    pins = [
        ("VBUS", 0, 40, "input"),
        ("+3V3", 0, 60, "output"),
        ("VBAT+", 0, 80, "bidirectional"),
        ("GND", 0, 100, "passive"),
        ("VBAT_ADC", 0, 120, "output"),
    ]
    # Global labels for inter-sheet connectivity
    for i, (name, _, y, _) in enumerate(pins):
        body += global_label(name, 279.4, 50.8 + i * 12.7, 0)

    body += power_symbol("GND", 50.8, 101.6)
    body += power_symbol("+3V3", 228.6, 50.8)

    body += sch_footer(
        f"""\t(sheet_instances
\t\t(path "/power"
\t\t\t(page "2")
\t\t)
\t)"""
    )
    return body


def build_mcu_sheet() -> str:
    body = sch_header("MCU - ESP32-S3-WROOM-1")
    body += "\t)\n"
    body += text_note(
        "MCU SHEET\\n"
        "ESP32-S3-WROOM-1-N8\\n"
        "Native USB: GPIO19/20\\n"
        "Review strapping pins before fab",
        25.4, 25.4,
    )

    parts = [
        ("RF_Module:ESP32-S3-WROOM-1", "U1", "ESP32-S3-WROOM-1-N8", "RF_Module:ESP32-S3-WROOM-1", (127.0, 101.6, 0)),
        ("Device:C", "C10", "100nF", "Capacitor_SMD:C_0402_1005Metric", (101.6, 76.2, 0)),
        ("Device:C", "C11", "100nF", "Capacitor_SMD:C_0402_1005Metric", (114.3, 76.2, 0)),
        ("Device:C", "C12", "100nF", "Capacitor_SMD:C_0402_1005Metric", (127.0, 76.2, 0)),
        ("Device:C", "C13", "10uF", "Capacitor_SMD:C_0603_1608Metric", (139.7, 76.2, 0)),
        ("Device:SW_Push", "SW7", "RESET", "Button_Switch_SMD:SW_SPST_TL3342", (177.8, 127.0, 0)),
        ("Device:SW_Push", "SW8", "BOOT", "Button_Switch_SMD:SW_SPST_TL3342", (190.5, 127.0, 0)),
        ("Device:R", "R10", "10k", "Resistor_SMD:R_0402_1005Metric", (165.1, 114.3, 0)),
        ("Device:R", "R11", "10k", "Resistor_SMD:R_0402_1005Metric", (203.2, 114.3, 0)),
    ]
    for p in parts:
        body += schematic_symbol(*p)

    nets = [
        "+3V3", "GND", "LCD_SCK", "LCD_MOSI", "LCD_CS", "LCD_DISP", "LCD_EXTCOM",
        "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_ENTER", "KEY_BACK",
        "VBAT_ADC", "USB_D+", "USB_D-",
    ]
    for i, net in enumerate(nets):
        body += global_label(net, 254.0, 50.8 + i * 10.0, 0)

    body += sch_footer(
        """\t(sheet_instances
\t\t(path "/mcu"
\t\t\t(page "3")
\t\t)
\t)"""
    )
    return body


def build_usb_sheet() -> str:
    body = sch_header("USB - USB-C Receptacle")
    body += "\t)\n"
    body += text_note("USB SHEET\\nUSB-C UFP 5.1k CC\\nESD on D+/D-", 25.4, 25.4)

    parts = [
        ("Connector_USB:USB_C_Receptacle_USB2.0", "J4", "USB-C", "Connector_USB:USB_C_Receptacle_USB2.0", (101.6, 76.2, 0)),
        ("Device:R", "R20", "5.1k", "Resistor_SMD:R_0402_1005Metric", (127.0, 101.6, 0)),
        ("Device:R", "R21", "5.1k", "Resistor_SMD:R_0402_1005Metric", (139.7, 101.6, 0)),
        ("Device:USBLC6-2SC6", "U5", "USBLC6-2", "Package_TO_SOT_SMD:SOT-23-6", (165.1, 76.2, 0)),
    ]
    for p in parts:
        body += schematic_symbol(*p)

    for i, net in enumerate(["VBUS", "GND", "USB_D+", "USB_D-"]):
        body += global_label(net, 203.2, 63.5 + i * 12.7, 0)

    body += sch_footer(
        """\t(sheet_instances
\t\t(path "/usb"
\t\t\t(page "4")
\t\t)
\t)"""
    )
    return body


def build_display_sheet() -> str:
    body = sch_header("Display - Sharp LS013B7DH03 Memory LCD")
    body += "\t)\n"
    body += text_note(
        "DISPLAY SHEET\\n"
        "Sharp LS013B7DH03 (128x128 memory LCD)\\n"
        "SPI + EXTCOMIN (GPIO13 PWM ~1Hz)\\n"
        "Verify FPC pinout against datasheet",
        25.4, 25.4,
    )

    parts = [
        ("Connector:Conn_01x08", "J3", "LCD_FPC", "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", (127.0, 76.2, 0)),
        ("Device:R", "R40", "10k", "Resistor_SMD:R_0402_1005Metric", (152.4, 101.6, 0)),
        ("Device:C", "C40", "100nF", "Capacitor_SMD:C_0402_1005Metric", (165.1, 101.6, 0)),
    ]
    for p in parts:
        body += schematic_symbol(*p)

    nets = ["LCD_SCK", "LCD_MOSI", "LCD_CS", "LCD_DISP", "LCD_EXTCOM", "+3V3", "GND"]
    for i, net in enumerate(nets):
        body += global_label(net, 50.8, 50.8 + i * 12.7, 180)

    body += sch_footer(
        """\t(sheet_instances
\t\t(path "/display"
\t\t\t(page "5")
\t\t)
\t)"""
    )
    return body


def build_keypad_sheet() -> str:
    body = sch_header("Keypad - 6 Keys")
    body += "\t)\n"
    body += text_note(
        "KEYPAD\\n"
        "UP DOWN LEFT RIGHT ENTER BACK\\n"
        "Active low + 10k pull-up",
        25.4, 25.4,
    )

    keys = [
        ("SW1", "UP", "KEY_UP"),
        ("SW2", "DOWN", "KEY_DOWN"),
        ("SW3", "LEFT", "KEY_LEFT"),
        ("SW4", "RIGHT", "KEY_RIGHT"),
        ("SW5", "ENTER", "KEY_ENTER"),
        ("SW6", "BACK", "KEY_BACK"),
    ]
    y = 76.2
    for ref, label, _ in keys:
        body += schematic_symbol(
            "Switch:SW_Push", ref, label,
            "Button_Switch_SMD:SW_SPST_TL3342",
            (101.6, y, 0),
        )
        body += schematic_symbol(
            "Device:R", f"R{ref[2:]}", "10k",
            "Resistor_SMD:R_0402_1005Metric",
            (127.0, y, 0),
        )
        y += 25.4

    for i, net in enumerate(["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_ENTER", "KEY_BACK", "+3V3", "GND"]):
        body += global_label(net, 177.8, 50.8 + i * 12.7, 0)

    body += sch_footer(
        """\t(sheet_instances
\t\t(path "/keypad"
\t\t\t(page "6")
\t\t)
\t)"""
    )
    return body


def build_root_sheet() -> str:
    body = sch_header("ESP32-S3 Wearable - Root")
    body += "\t)\n"
    body += text_note(
        "ROOT SHEET\\n"
        "Open each sub-sheet by double-clicking.\\n"
        "After edits: Tools > Update PCB from Schematic (F8)",
        25.4, 25.4,
    )

    # Hierarchical sheets with pins
    sheets = [
        ("Power", "sheets/power.kicad_sch", 30, 40, 40, 30, [
            ("VBUS", "input"), ("+3V3", "output"), ("VBAT+", "bidirectional"),
            ("GND", "passive"), ("VBAT_ADC", "output"),
        ]),
        ("MCU", "sheets/mcu.kicad_sch", 90, 40, 50, 35, [
            ("+3V3", "input"), ("GND", "passive"),
            ("LCD_SCK", "output"), ("LCD_MOSI", "output"), ("LCD_CS", "output"),
            ("LCD_DISP", "output"), ("LCD_EXTCOM", "output"),
            ("KEY_UP", "input"), ("KEY_DOWN", "input"), ("KEY_LEFT", "input"),
            ("KEY_RIGHT", "input"), ("KEY_ENTER", "input"), ("KEY_BACK", "input"),
            ("VBAT_ADC", "input"), ("USB_D+", "bidirectional"), ("USB_D-", "bidirectional"),
        ]),
        ("USB", "sheets/usb.kicad_sch", 30, 90, 35, 25, [
            ("VBUS", "output"), ("GND", "passive"), ("USB_D+", "bidirectional"), ("USB_D-", "bidirectional"),
        ]),
        ("Display", "sheets/display.kicad_sch", 90, 90, 35, 25, [
            ("LCD_SCK", "input"), ("LCD_MOSI", "input"), ("LCD_CS", "input"),
            ("LCD_DISP", "input"), ("LCD_EXTCOM", "input"), ("+3V3", "input"), ("GND", "passive"),
        ]),
        ("Keypad", "sheets/keypad.kicad_sch", 150, 90, 35, 30, [
            ("KEY_UP", "output"), ("KEY_DOWN", "output"), ("KEY_LEFT", "output"),
            ("KEY_RIGHT", "output"), ("KEY_ENTER", "output"), ("KEY_BACK", "output"),
            ("+3V3", "input"), ("GND", "passive"),
        ]),
    ]

    for name, fname, sx, sy, sw, sh, pin_defs in sheets:
        pins = []
        for i, (pname, pdir) in enumerate(pin_defs):
            pins.append((pname, sx, sy + 5 + i * 2.5, pdir))
        body += hierarchical_sheet(name, fname, sx, sy, sw, sh, pins)

    # Inter-sheet net connections via global labels on root
    connect = [
        "VBUS", "+3V3", "GND", "VBAT+", "VBAT_ADC",
        "LCD_SCK", "LCD_MOSI", "LCD_CS", "LCD_DISP", "LCD_EXTCOM",
        "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_ENTER", "KEY_BACK",
        "USB_D+", "USB_D-",
    ]
    for i, net in enumerate(connect):
        body += global_label(net, 220 + (i % 3) * 15, 40 + (i // 3) * 10, 0)

    body += sch_footer()
    return body


# ---------------------------------------------------------------------------
# PCB generation (placement + outline)
# ---------------------------------------------------------------------------

def build_pcb() -> str:
    """PCB with board outline 42x34mm and component placements."""
    board_w = 42.0
    board_h = 34.0

    footprints = [
        # ref, lib_id, x, y, rot
        ("U1", "RF_Module:ESP32-S3-WROOM-1", 30.0, 17.0, 0),
        ("J4", "Connector_USB:USB_C_Receptacle_USB2.0", 3.0, 12.0, 270),
        ("J1", "Connector_JST:JST_PH_B2B-PH-K-S_Leads", 39.0, 28.0, 90),
        ("J3", "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 21.0, 3.0, 0),
        ("U2", "Package_TO_SOT_SMD:SOT-23-5", 12.0, 28.0, 0),
        ("U3", "Package_TO_SOT_SMD:SOT-23-5", 18.0, 28.0, 0),
        ("U5", "Package_TO_SOT_SMD:SOT-23-6", 8.0, 20.0, 0),
        ("SW1", "Button_Switch_SMD:SW_SPST_TL3342", 8.0, 8.0, 0),
        ("SW2", "Button_Switch_SMD:SW_SPST_TL3342", 13.0, 8.0, 0),
        ("SW3", "Button_Switch_SMD:SW_SPST_TL3342", 18.0, 8.0, 0),
        ("SW4", "Button_Switch_SMD:SW_SPST_TL3342", 23.0, 8.0, 0),
        ("SW5", "Button_Switch_SMD:SW_SPST_TL3342", 28.0, 8.0, 0),
        ("SW6", "Button_Switch_SMD:SW_SPST_TL3342", 33.0, 8.0, 0),
        ("H1", "MountingHole:MountingHole_2.2mm_M2", 2.5, 2.5, 0),
        ("H2", "MountingHole:MountingHole_2.2mm_M2", 39.5, 2.5, 0),
        ("H3", "MountingHole:MountingHole_2.2mm_M2", 2.5, 31.5, 0),
        ("H4", "MountingHole:MountingHole_2.2mm_M2", 39.5, 31.5, 0),
    ]

    fp_blocks = ""
    for ref, lib, x, y, rot in footprints:
        fp_blocks += f"""
  (footprint "{lib}"
    (layer "F.Cu")
    (uuid "{uid()}")
    (at {x} {y} {rot})
    (property "Reference" "{ref}"
      (at 0 -2 0)
      (layer "F.SilkS")
      (uuid "{uid()}")
      (effects
        (font
          (size 1 1)
          (thickness 0.15)
        )
      )
    )
    (property "Value" "{ref}"
      (at 0 2 0)
      (layer "F.Fab")
      (uuid "{uid()}")
      (effects
        (font
          (size 1 1)
          (thickness 0.15)
        )
      )
    )
    (property "Footprint" "{lib}"
      (at 0 0 0)
      (layer "F.Fab")
      (hide yes)
      (uuid "{uid()}")
      (effects
        (font
          (size 1 1)
          (thickness 0.15)
        )
      )
    )
    (path "/{uid()}")
    (attr smd)
  )
"""

    outline = f"""
  (gr_rect
    (start 0 0)
    (end {board_w} {board_h})
    (stroke
      (width 0.1)
      (type default)
    )
    (fill none)
    (layer "Edge.Cuts")
    (uuid "{uid()}")
  )
"""

    antenna_keepout = f"""
  (gr_rect
    (start 22 0)
    (end {board_w} 12)
    (stroke
      (width 0.12)
      (type dash)
    )
    (fill none)
    (layer "Cmts.User")
    (uuid "{uid()}")
  )
  (gr_text "ANTENNA KEEP-OUT"
    (at 32 6 0)
    (layer "Cmts.User")
    (uuid "{uid()}")
    (effects
      (font
        (size 1 1)
        (thickness 0.15)
      )
    )
  )
"""

    silk = f"""
  (gr_text "REV A"
    (at 2 32 0)
    (layer "F.SilkS")
    (uuid "{uid()}")
    (effects
      (font
        (size 0.8 0.8)
        (thickness 0.12)
      )
    )
  )
  (gr_text "BAT +"
    (at 36 26 90)
    (layer "F.SilkS")
    (uuid "{uid()}")
    (effects
      (font
        (size 0.8 0.8)
        (thickness 0.12)
      )
    )
  )
  (gr_text "USB"
    (at 1 16 90)
    (layer "F.SilkS")
    (uuid "{uid()}")
    (effects
      (font
        (size 0.8 0.8)
        (thickness 0.12)
      )
    )
  )
"""

    return f"""(kicad_pcb
  (version 20240108)
  (generator "esp32s3-wearable-generator")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )
  (setup
    (pad_to_mask_clearance 0)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros no)
      (usegerberextensions no)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref no)
      (viasonmask no)
      (mode 1)
      (useauxorigin no)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (pdf_front_fp_property_popups yes)
      (pdf_back_fp_property_popups yes)
      (dxfpolygonmode yes)
      (dxfimperialunits yes)
      (dxfusepcbnewfont yes)
      (psnegative no)
      (psa4output no)
      (plotreference yes)
      (plotvalue yes)
      (plotfingerprint no)
      (plotinvisibletext no)
      (sketchpadsonfab no)
      (subtractmaskfromsilk no)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "exports/gerbers")
    )
  )
  (net 0 "")
  (net 1 "+3V3")
  (net 2 "GND")
  (net 3 "VBAT+")
  (net 4 "VBUS")
  (net 5 "USB_D+")
  (net 6 "USB_D-")
  (net 7 "LCD_SCK")
  (net 8 "LCD_MOSI")
  (net 9 "LCD_CS")
  (net 10 "LCD_DISP")
  (net 11 "LCD_EXTCOM")
  (net 12 "KEY_UP")
  (net 13 "KEY_DOWN")
  (net 14 "KEY_LEFT")
  (net 15 "KEY_RIGHT")
  (net 16 "KEY_ENTER")
  (net 17 "KEY_BACK")
  (net 18 "VBAT_ADC")
{outline}
{antenna_keepout}
{silk}
{fp_blocks}
)
"""


def build_project_file() -> dict:
    return {
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {
                    "board_outline_line_width": 0.1,
                    "copper_line_width": 0.2,
                    "copper_text_italic": False,
                    "copper_text_size_h": 1.5,
                    "copper_text_size_v": 1.5,
                    "copper_text_thickness": 0.3,
                    "other_line_width": 0.15,
                    "silk_line_width": 0.15,
                    "silk_text_italic": False,
                    "silk_text_size_h": 1.0,
                    "silk_text_size_v": 1.0,
                    "silk_text_thickness": 0.15,
                },
                "diff_pair_dimensions": [],
                "drc_exclusions": [],
                "meta": {"version": 2},
                "rule_severities": {},
                "rules": {},
                "track_widths": [0.15, 0.2, 0.25, 0.4, 0.5],
                "via_dimensions": [],
            },
            "layer_presets": [],
            "viewports": [],
        },
        "meta": {"filename": "esp32s3-wearable.kicad_pro", "version": 1},
        "net_settings": {"classes": [{"bus_width": 12, "clearance": 0.15, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": "Default", "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647, "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3, "wire_width": 6}], "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None, "netclass_patterns": []},
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "exports/gerbers", "pos_files": "exports", "specctra_dsn": "", "step": "exports", "svg": "", "vrml": ""}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [["/", "Root"]],
        "text_variables": {},
    }


BOM = [
    ("Ref", "Value", "Footprint", "Qty", "Description", "LCSC"),
    ("U1", "ESP32-S3-WROOM-1-N8", "RF_Module:ESP32-S3-WROOM-1", "1", "WiFi/BT MCU module", "C2913202"),
    ("U2", "MCP73831-2-AC", "Package_TO_SOT_SMD:SOT-23-5", "1", "Li-ion charger IC", "C14879"),
    ("U3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5", "1", "3.3V LDO 600mA", "C23380830"),
    ("U4", "DW01A", "Package_TO_SOT_SMD:SOT-23-6", "1", "Battery protection", "C351410"),
    ("U5", "USBLC6-2", "Package_TO_SOT_SMD:SOT-23-6", "1", "USB ESD protection", "C7519"),
    ("J1", "BAT_CONN", "Connector_JST:JST_PH_B2B-PH-K-S_Leads", "1", "Battery JST PH 2.0", "C131337"),
    ("J3", "LCD_FPC", "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", "1", "LCD interface (verify)", ""),
    ("J4", "USB-C", "Connector_USB:USB_C_Receptacle_USB2.0", "1", "USB-C receptacle", "C2765186"),
    ("SW1-SW6", "KEY", "Button_Switch_SMD:SW_SPST_TL3342", "6", "Tactile switches 6x6", "C318884"),
    ("SW7", "RESET", "Button_Switch_SMD:SW_SPST_TL3342", "1", "EN reset button", "C318884"),
    ("SW8", "BOOT", "Button_Switch_SMD:SW_SPST_TL3342", "1", "GPIO0 boot button", "C318884"),
    ("R1", "2k", "Resistor_SMD:R_0402_1005Metric", "1", "Charge current set", "C25900"),
    ("R2,R3", "100k", "Resistor_SMD:R_0402_1005Metric", "2", "Battery divider", "C25741"),
    ("R4", "1k", "Resistor_SMD:R_0402_1005Metric", "1", "Charge LED", "C25752"),
    ("R10,R11", "10k", "Resistor_SMD:R_0402_1005Metric", "2", "EN/BOOT pull-up", "C25744"),
    ("R20,R21", "5.1k", "Resistor_SMD:R_0402_1005Metric", "2", "USB-C CC", "C25905"),
    ("R30-R35", "10k", "Resistor_SMD:R_0402_1005Metric", "6", "Key pull-ups", "C25744"),
    ("C1,C2,C13", "10uF", "Capacitor_SMD:C_0603_1608Metric", "3", "Bulk capacitors", "C19702"),
    ("C3,C10-C12,C40", "100nF", "Capacitor_SMD:C_0402_1005Metric", "5", "Decoupling", "C1525"),
    ("D1", "CHG_LED", "LED_SMD:LED_0603_1608Metric", "1", "Charge status LED", "C72043"),
    ("BAT1", "3.7V Li-Po", "-", "1", "1200mAh with JST", ""),
    ("LCD1", "LS013B7DH03", "-", "1", "128x128 memory LCD", ""),
    ("PCB1", "PCB", "42x34mm 2L", "1", "1.6mm ENIG", ""),
]


PINS_H = """/* Auto-generated pin map for ESP32-S3 wearable PCB Rev A */
#pragma once

// Sharp LS013B7DH03 memory LCD (SPI)
#define PIN_LCD_SCK     12
#define PIN_LCD_MOSI    11
#define PIN_LCD_CS      10
#define PIN_LCD_DISP    9
#define PIN_LCD_EXTCOM  13   // PWM ~1 Hz EXTCOMIN

// 6-key keypad (active low)
#define PIN_KEY_UP      1
#define PIN_KEY_DOWN    2
#define PIN_KEY_LEFT    3
#define PIN_KEY_RIGHT   4
#define PIN_KEY_ENTER   5
#define PIN_KEY_BACK    6

// Battery sense (ADC1)
#define PIN_VBAT_ADC    7

// Native USB (ESP32-S3)
#define PIN_USB_DM      19
#define PIN_USB_DP      20

// System
#define PIN_BOOT        0
#define PIN_EN          -1  // dedicated reset circuit
"""


def main() -> None:
    SHEETS.mkdir(parents=True, exist_ok=True)
    (ROOT / "exports").mkdir(exist_ok=True)

    sheets = {
        "sheets/power.kicad_sch": build_power_sheet(),
        "sheets/mcu.kicad_sch": build_mcu_sheet(),
        "sheets/usb.kicad_sch": build_usb_sheet(),
        "sheets/display.kicad_sch": build_display_sheet(),
        "sheets/keypad.kicad_sch": build_keypad_sheet(),
        "esp32s3-wearable.kicad_sch": build_root_sheet(),
        "esp32s3-wearable.kicad_pcb": build_pcb(),
    }

    for rel, content in sheets.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path}")

    pro = ROOT / "esp32s3-wearable.kicad_pro"
    pro.write_text(json.dumps(build_project_file(), indent=2), encoding="utf-8")
    print(f"Wrote {pro}")

    bom_path = ROOT / "exports" / "bom.csv"
    with bom_path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(BOM)
    print(f"Wrote {bom_path}")

    pins_path = ROOT / "firmware" / "pins.h"
    pins_path.parent.mkdir(exist_ok=True)
    pins_path.write_text(PINS_H, encoding="utf-8")
    print(f"Wrote {pins_path}")


if __name__ == "__main__":
    main()
