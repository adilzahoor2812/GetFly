#!/usr/bin/env python3
"""Generate SignSpeak Smart Glove Rev H schematic (reference-style block layout).

Style inspired by professional single-sheet ESP32 boards:
  dashed section boxes, titled zones, net labels between blocks.
Content is SignSpeak-only (USB-C+CH340, TP4056+DW01, flex, MPU-6050).
"""

from __future__ import annotations

import re
import subprocess
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SYM = Path("/usr/share/kicad/symbols")
OUT = ROOT / "smart-glove.kicad_sch"
TEMPLATE = ROOT / "fab" / "smart-glove.kicad_sch.template"
G = 1.27  # connection grid


def uid() -> str:
    return str(uuid.uuid4())


def g(n: float) -> float:
    """Snap to 1.27 mm grid."""
    return round(round(n / G) * G, 2)


def extract_symbol(lib_file: Path, name: str) -> str:
    text = lib_file.read_text()
    key = f'(symbol "{name}"'
    start = text.find(key)
    if start < 0:
        raise RuntimeError(f"Missing symbol {name} in {lib_file.name}")
    depth = 0
    for j in range(start, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                block = text[start : j + 1]
                lib = lib_file.stem
                return re.sub(
                    rf'^\(symbol "{re.escape(name)}"',
                    f'(symbol "{lib}:{name}"',
                    block,
                    count=1,
                )
    raise RuntimeError(f"Unbalanced symbol {name}")


def pin_map(lib_file: Path, name: str, ox: float, oy: float) -> dict[str, tuple[float, float, int]]:
    text = lib_file.read_text()
    cur = name
    while True:
        key = f'(symbol "{cur}"'
        start = text.find(key)
        if start < 0:
            raise RuntimeError(cur)
        depth = 0
        for j in range(start, len(text)):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    block = text[start : j + 1]
                    break
        m = re.search(r'\(extends "([^"]+)"\)', block)
        if not m:
            break
        cur = m.group(1)
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\)', block):
        px, py, rot = float(m.group(1)), float(m.group(2)), int(m.group(3)) % 360
        window = block[m.start() : m.start() + 500]
        nm = re.search(r'\(number "([^"]+)"', window)
        if not nm:
            continue
        lr = {0: 0, 90: 90, 180: 180, 270: 270}[rot]
        # Schematic Y is flipped vs symbol-lib local Y when placing instances
        pins[nm.group(1)] = (round(ox + px, 2), round(oy - py, 2), lr)
    return pins


def dw01_symbol() -> str:
    return '''(symbol "Device:DW01A" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
    (property "Reference" "U" (at -5.08 6.35 0) (effects (font (size 1.27 1.27))))
    (property "Value" "DW01A" (at -5.08 3.81 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_TO_SOT_SMD:SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "DW01A_0_1"
      (rectangle (start -5.08 3.81) (end 5.08 -3.81)
        (stroke (width 0.254) (type default)) (fill (type background)))
    )
    (symbol "DW01A_1_1"
      (pin passive line (at -7.62 2.54 0) (length 2.54) (name "OD" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      (pin passive line (at -7.62 0 0) (length 2.54) (name "CS" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      (pin passive line (at -7.62 -2.54 0) (length 2.54) (name "OC" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 7.62 -2.54 180) (length 2.54) (name "TD" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 7.62 0 180) (length 2.54) (name "VCC" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 7.62 2.54 180) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
    )
  )'''


def fs8205_symbol() -> str:
    return '''(symbol "Device:FS8205A" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
    (property "Reference" "U" (at -5.08 7.62 0) (effects (font (size 1.27 1.27))))
    (property "Value" "FS8205A" (at -5.08 5.08 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:TSSOP-8_3x3mm_P0.65mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "FS8205A_0_1"
      (rectangle (start -5.08 5.08) (end 5.08 -5.08)
        (stroke (width 0.254) (type default)) (fill (type background)))
    )
    (symbol "FS8205A_1_1"
      (pin passive line (at -7.62 3.81 0) (length 2.54) (name "S1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      (pin passive line (at -7.62 1.27 0) (length 2.54) (name "G1" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      (pin passive line (at -7.62 -1.27 0) (length 2.54) (name "D1" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      (pin passive line (at -7.62 -3.81 0) (length 2.54) (name "D2" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 7.62 -3.81 180) (length 2.54) (name "D2" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 7.62 -1.27 180) (length 2.54) (name "D1" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 7.62 1.27 180) (length 2.54) (name "G2" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 7.62 3.81 180) (length 2.54) (name "S2" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
    )
  )'''


def tp4056_symbol() -> str:
    return '''(symbol "GetFly:TP4056" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
    (property "Reference" "U" (at -7.62 8.89 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TP4056" (at -7.62 6.35 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "TP4056_0_1"
      (rectangle (start -7.62 5.08) (end 7.62 -5.08)
        (stroke (width 0.254) (type default)) (fill (type background)))
    )
    (symbol "TP4056_1_1"
      (pin passive line (at -10.16 2.54 0) (length 2.54) (name "TEMP" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      (pin passive line (at -10.16 0 0) (length 2.54) (name "PROG" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at -10.16 -2.54 0) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at -10.16 -5.08 0) (length 2.54) (name "VCC" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      (pin power_out line (at 10.16 -2.54 180) (length 2.54) (name "BAT" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 10.16 0 180) (length 2.54) (name "STDBY" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 10.16 2.54 180) (length 2.54) (name "CHRG" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 10.16 5.08 180) (length 2.54) (name "CE" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
    )
  )'''


class Sch:
    def __init__(self):
        self.parts: list[str] = []

    def add(self, s: str):
        self.parts.append(s)

    def inst(self, lib_id, ref, value, x, y, footprint=""):
        x, y = g(x), g(y)
        self.add(
            f'  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit 1)'
            f' (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {x} {g(y + 5.08)} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Value" "{value}" (at {x} {g(y + 2.54)} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f"  )\n"
        )
        return x, y

    def power(self, lib_id, ref, value, x, y):
        x, y = g(x), g(y)
        self.add(
            f'  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit 1)'
            f' (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {x} {g(y + 2.54)} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Value" "{value}" (at {x} {g(y - 2.54)} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f"  )\n"
        )

    def label(self, name, x, y, rot=0, shape="passive"):
        x, y = round(x, 2), round(y, 2)
        just = "right" if rot == 180 else "left"
        if rot in (90, 270):
            just = "left"
        self.add(
            f'  (global_label "{name}" (shape {shape}) (at {x} {y} {rot})'
            f' (effects (font (size 1.27 1.27)) (justify {just}))\n'
            f'    (uuid "{uid()}")\n  )\n'
        )

    def nc(self, x, y):
        self.add(f'  (no_connect (at {round(x, 2)} {round(y, 2)}) (uuid "{uid()}"))\n')

    def wire(self, x1, y1, x2, y2):
        self.add(
            f'  (wire (pts (xy {round(x1, 2)} {round(y1, 2)}) (xy {round(x2, 2)} {round(y2, 2)}))'
            f' (stroke (width 0) (type default)) (uuid "{uid()}"))\n'
        )

    def text(self, s, x, y, size=1.27):
        self.add(
            f'  (text "{s}" (exclude_from_sim no) (at {g(x)} {g(y)} 0)'
            f' (effects (font (size {size} {size})) (justify left))\n'
            f'    (uuid "{uid()}")\n  )\n'
        )

    def section(self, title: str, x1: float, y1: float, x2: float, y2: float):
        """Dashed zone box + reference-style section title (top-left)."""
        x1, y1, x2, y2 = g(x1), g(y1), g(x2), g(y2)
        self.add(
            f"  (rectangle (start {x1} {y1}) (end {x2} {y2})\n"
            f"    (stroke (width 0.254) (type dash)) (fill (type none))\n"
            f'    (uuid "{uid()}")\n  )\n'
        )
        self.text(title, x1 + 2.54, y1 + 5.08, 2.032)

    def pwr_flag(self, net_lib: str, net_val: str, x: float, y: float, tag: str):
        """Power symbol + PWR_FLAG on a short wire (ERC)."""
        x, y = g(x), g(y)
        self.power(net_lib, f"#PWR_{tag}", net_val, x, y)
        self.power("power:PWR_FLAG", f"#FLG_{tag}", "PWR_FLAG", x + 7.62, y)
        self.wire(x, y, x + 7.62, y)

    def glabel_on_pins(self, pins: dict, mapping: dict[str, str]):
        for num, net in mapping.items():
            x, y, rot = pins[num]
            self.label(net, x, y, rot)

    def nc_pins(self, pins: dict, nums: list[str]):
        for num in nums:
            if num in pins:
                x, y, _ = pins[num]
                self.nc(x, y)

    def resistor_to_gnd(self, ref, value, x, y, top_net, fp="Resistor_SMD:R_0603_1608Metric"):
        """Vertical R with Y-flip: pin1 local+3.81 -> world y-3.81; pin2 -> y+3.81."""
        x, y = self.inst("Device:R", ref, value, x, y, fp)
        self.label(top_net, x, y - 3.81, 90)
        self.power("power:GND", f"#PWR_{ref}", "GND", x, y + 3.81)

    def cap_to_gnd(self, ref, value, x, y, top_net, fp="Capacitor_SMD:C_0603_1608Metric"):
        x, y = self.inst("Device:C", ref, value, x, y, fp)
        self.label(top_net, x, y - 3.81, 90)
        self.power("power:GND", f"#PWR_{ref}", "GND", x, y + 3.81)

    def led_series(self, ref, value, x, y, anode_net, cathode_net, fp="LED_SMD:LED_0603_1608Metric"):
        """Horizontal LED: pin1 K at x-3.81, pin2 A at x+3.81."""
        x, y = self.inst("Device:LED", ref, value, x, y, fp)
        self.label(cathode_net, x - 3.81, y, 0)
        self.label(anode_net, x + 3.81, y, 180)


def build() -> str:
    libs: list[str] = []
    for name in ("GND", "+3V3", "+5V", "PWR_FLAG"):
        libs.append(extract_symbol(SYM / "power.kicad_sym", name))
    # +BAT is a global net name only (driven by U2 BAT); no custom power symbol needed.
    for name in ("R", "C", "LED"):
        libs.append(extract_symbol(SYM / "Device.kicad_sym", name))
    libs.append(extract_symbol(SYM / "Switch.kicad_sym", "SW_Push"))
    libs.append(extract_symbol(SYM / "Connector_Generic.kicad_sym", "Conn_01x07"))
    libs.append(extract_symbol(SYM / "Connector_Generic.kicad_sym", "Conn_01x04"))
    libs.append(extract_symbol(SYM / "Connector_Generic.kicad_sym", "Conn_01x02"))
    libs.append(extract_symbol(SYM / "Connector.kicad_sym", "USB_C_Receptacle"))
    libs.append(extract_symbol(SYM / "RF_Module.kicad_sym", "ESP32-WROOM-32E"))
    libs.append(extract_symbol(SYM / "Interface_USB.kicad_sym", "CH340C"))
    # Embed under Device: to avoid "modified in library" warnings against Regulator_Linear
    ams = extract_symbol(SYM / "Regulator_Linear.kicad_sym", "AP1117-15")
    ams = ams.replace("Regulator_Linear:AP1117-15", "Device:AMS1117-3.3")
    ams = ams.replace('Value" "AP1117-15"', 'Value" "AMS1117-3.3"')
    ams = ams.replace("AP1117-15_0_1", "AMS1117-3.3_0_1").replace("AP1117-15_1_1", "AMS1117-3.3_1_1")
    libs.append(ams)
    libs.append(extract_symbol(SYM / "Sensor_Motion.kicad_sym", "MPU-6050"))
    # Avoid missing-lib warning: embed as Device:TP4056
    libs.append(tp4056_symbol().replace("GetFly:TP4056", "Device:TP4056"))
    libs.append(dw01_symbol())
    libs.append(fs8205_symbol())

    s = Sch()

    # =====================================================================
    # Reference-style layout (SignSpeak content — not a copy of the PDF)
    # Flow: USB/power left → MCU center → charge/protect/IMU right → I/O bottom
    # =====================================================================

    # ---- USB-C Connector & CC ----
    s.section("USB-C Connector & CC:", 12.7, 12.7, 127.0, 95.25)
    j1x, j1y = g(50.8), g(55.88)
    s.inst("Connector:USB_C_Receptacle", "J1", "USB-C", j1x, j1y,
           "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12")
    usb = pin_map(SYM / "Connector.kicad_sym", "USB_C_Receptacle", j1x, j1y)
    s.glabel_on_pins(usb, {
        "A4": "+5V", "A9": "+5V", "B4": "+5V", "B9": "+5V",
        "A5": "CC1", "B5": "CC2",
        "A6": "USB_DP", "B6": "USB_DP",
        "A7": "USB_DM", "B7": "USB_DM",
        "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
        "S1": "GND",
    })
    s.nc_pins(usb, [
        "A2", "A3", "A8", "A10", "A11",
        "B2", "B3", "B8", "B10", "B11",
    ])
    s.resistor_to_gnd("R6", "5.1k", 95.25, 40.64, "CC1")
    s.resistor_to_gnd("R7", "5.1k", 110.49, 40.64, "CC2")
    s.pwr_flag("power:+5V", "+5V", 88.9, 82.55, "5V")

    # ---- USB TO UART BRIDGE ----
    s.section("USB TO UART BRIDGE (CH340C):", 12.7, 101.6, 152.4, 203.2)
    u5x, u5y = g(50.8), g(140.0)
    s.inst("Interface_USB:CH340C", "U5", "CH340C", u5x, u5y,
           "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm")
    ch = pin_map(SYM / "Interface_USB.kicad_sym", "CH340C", u5x, u5y)
    s.glabel_on_pins(ch, {
        "1": "GND", "2": "UART_RX", "3": "UART_TX", "4": "CH340_3V3",
        "5": "USB_DP", "6": "USB_DM", "13": "DTR", "14": "RTS", "16": "+5V",
    })
    s.nc_pins(ch, ["8", "9", "10", "11", "12", "15"])
    s.cap_to_gnd("C13", "100nF", 95.25, 127.0, "CH340_3V3")
    s.cap_to_gnd("C14", "100nF", 110.49, 127.0, "+5V")
    # Auto-program: DTR/RTS AC-coupled into EN/BOOT
    x, y = s.inst("Device:C", "C11", "100nF", 95.25, 165.1, "Capacitor_SMD:C_0603_1608Metric")
    s.label("DTR", x, y - 3.81, 90)
    s.label("EN", x, y + 3.81, 270)
    x, y = s.inst("Device:C", "C12", "100nF", 110.49, 165.1, "Capacitor_SMD:C_0603_1608Metric")
    s.label("RTS", x, y - 3.81, 90)
    s.label("BOOT", x, y + 3.81, 270)
    s.text("Auto-program caps → EN / BOOT", 88.9, 182.88, 1.27)

    # ---- POWER SUPPLY ----
    s.section("POWER SUPPLY (BAT to 3V3):", 12.7, 209.55, 152.4, 292.1)
    u3x, u3y = g(50.8), g(241.3)
    s.inst("Device:AMS1117-3.3", "U3", "AMS1117-3.3", u3x, u3y, "Package_TO_SOT_SMD:SOT-223")
    amsp = pin_map(SYM / "Regulator_Linear.kicad_sym", "AP1117-15", u3x, u3y)
    s.glabel_on_pins(amsp, {"1": "GND", "2": "3V3", "3": "+BAT"})
    s.cap_to_gnd("C5", "10uF", 88.9, 241.3, "+BAT", "Capacitor_SMD:C_0805_2012Metric")
    s.cap_to_gnd("C6", "22uF", 106.68, 241.3, "3V3", "Capacitor_SMD:C_0805_2012Metric")
    s.cap_to_gnd("C7", "100nF", 124.46, 241.3, "3V3")
    # 3V3 driven by U3 power_out — only flag USB +5V and GND for ERC
    s.pwr_flag("power:GND", "GND", 88.9, 269.24, "GND")

    # ---- ESP32 Reset & Boot ----
    s.section("ESP32 Reset & Boot circuit:", 160.02, 12.7, 292.1, 95.25)
    x, y = s.inst("Device:R", "R9", "10k", 180.34, 40.64, "Resistor_SMD:R_0603_1608Metric")
    s.label("3V3", x, y - 3.81, 90)
    s.label("EN", x, y + 3.81, 270)
    x, y = s.inst("Device:R", "R10", "10k", 200.66, 40.64, "Resistor_SMD:R_0603_1608Metric")
    s.label("3V3", x, y - 3.81, 90)
    s.label("BOOT", x, y + 3.81, 270)
    x, y = s.inst("Switch:SW_Push", "SW2", "EN", 228.6, 40.64, "Button_Switch_SMD:SW_SPST_B3U-1000P")
    s.label("EN", x - 5.08, y, 0)
    s.power("power:GND", "#PWR_SW2", "GND", x + 5.08, y)
    x, y = s.inst("Switch:SW_Push", "SW1", "BOOT", 261.62, 40.64, "Button_Switch_SMD:SW_SPST_B3U-1000P")
    s.label("BOOT", x - 5.08, y, 0)
    s.power("power:GND", "#PWR_SW1", "GND", x + 5.08, y)
    s.cap_to_gnd("C1", "100nF", 180.34, 71.12, "3V3")
    s.cap_to_gnd("C2", "100nF", 200.66, 71.12, "3V3")

    # ---- POWER AND STATUS LEDs ----
    s.section("POWER AND STATUS LED's:", 160.02, 101.6, 292.1, 165.1)
    x, y = s.inst("Device:R", "R5", "1k", 180.34, 127.0, "Resistor_SMD:R_0603_1608Metric")
    s.label("3V3", x, y - 3.81, 90)
    s.label("PWR_LED", x, y + 3.81, 270)
    s.led_series("D1", "LED-PWR", 210.82, 127.0, "PWR_LED", "GND")
    s.led_series("D3", "LED-STAT", 248.92, 127.0, "STAT_LED", "GND")
    s.text("D1 = power · D3 = ESP32 IO2 status", 170.18, 152.4, 1.27)

    # ---- LiPo Charger ----
    s.section("LiPo Charger (TP4056):", 300.0, 12.7, 431.8, 101.6)
    u2x, u2y = g(335.28), g(50.8)
    s.inst("Device:TP4056", "U2", "TP4056", u2x, u2y, "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
    s.label("GND", u2x - 10.16, u2y - 2.54, 0)
    s.label("TP_PROG", u2x - 10.16, u2y - 0.0, 0)
    s.label("GND", u2x - 10.16, u2y + 2.54, 0)
    s.label("+5V", u2x - 10.16, u2y + 5.08, 0)
    s.label("+BAT", u2x + 10.16, u2y + 2.54, 180)
    s.nc(u2x + 10.16, u2y - 0.0)
    s.label("CHRG", u2x + 10.16, u2y - 2.54, 180)
    s.label("+5V", u2x + 10.16, u2y - 5.08, 180)
    s.resistor_to_gnd("R8", "1.2k", 373.38, 45.72, "TP_PROG")
    s.led_series("D2", "LED-CHRG", 398.78, 45.72, "+5V", "CHRG")
    j3x, j3y = g(398.78), g(78.74)
    s.inst("Connector_Generic:Conn_01x02", "J3", "LiPo", j3x, j3y,
           "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical")
    s.label("+BAT", j3x - 5.08, j3y - 0.0, 0)
    s.label("BAT_N", j3x - 5.08, j3y + 2.54, 0)

    # ---- Battery Protection ----
    s.section("Battery Pack Protect (DW01A + FS8205A):", 300.0, 109.22, 431.8, 215.9)
    u6x, u6y = g(335.28), g(140.0)
    s.inst("Device:DW01A", "U6", "DW01A", u6x, u6y, "Package_TO_SOT_SMD:SOT-23-6")
    s.label("GATE_P", u6x - 7.62, u6y - 2.54, 0)
    s.label("BAT_N", u6x - 7.62, u6y - 0.0, 0)
    s.label("GATE_P", u6x - 7.62, u6y + 2.54, 0)
    s.nc(u6x + 7.62, u6y + 2.54)
    s.label("DW01_VCC", u6x + 7.62, u6y - 0.0, 180)
    s.label("BAT_N", u6x + 7.62, u6y - 2.54, 180)
    x, y = s.inst("Device:R", "R12", "1k", 373.38, 130.0, "Resistor_SMD:R_0603_1608Metric")
    s.label("+BAT", x, y - 3.81, 90)
    s.label("DW01_VCC", x, y + 3.81, 270)
    s.cap_to_gnd("C15", "100nF", 393.7, 130.0, "DW01_VCC")
    u7x, u7y = g(335.28), g(180.0)
    s.inst("Device:FS8205A", "U7", "FS8205A", u7x, u7y, "Package_SO:TSSOP-8_3x3mm_P0.65mm")
    s.label("BAT_N", u7x - 7.62, u7y - 3.81, 0)
    s.label("GATE_P", u7x - 7.62, u7y - 1.27, 0)
    s.label("GND", u7x - 7.62, u7y + 1.27, 0)
    s.label("GND", u7x - 7.62, u7y + 3.81, 0)
    s.label("GND", u7x + 7.62, u7y + 3.81, 180)
    s.label("GND", u7x + 7.62, u7y + 1.27, 180)
    s.label("GATE_P", u7x + 7.62, u7y - 1.27, 180)
    s.label("BAT_N", u7x + 7.62, u7y - 3.81, 180)

    # ---- ESP32 MCU (center) ----
    s.section("ESP32-WROOM-32E:", 160.02, 175.26, 292.1, 330.2)
    u1x, u1y = g(215.9), g(250.0)
    s.inst("RF_Module:ESP32-WROOM-32E", "U1", "ESP32-WROOM-32E", u1x, u1y, "RF_Module:ESP32-WROOM-32")
    esp = pin_map(SYM / "RF_Module.kicad_sym", "ESP32-WROOM-32E", u1x, u1y)
    s.glabel_on_pins(esp, {
        "1": "GND", "2": "3V3", "3": "EN",
        "4": "FLEX1", "5": "FLEX2", "6": "FLEX3", "7": "FLEX4", "8": "FLEX5",
        "15": "GND", "24": "STAT_LED", "25": "BOOT",
        "31": "IMU_INT", "33": "SDA", "34": "UART_RX", "35": "UART_TX",
        "36": "SCL", "38": "GND", "39": "GND",
    })
    s.nc_pins(esp, [
        "9", "10", "11", "12", "13", "14", "16", "23",
        "26", "27", "28", "29", "30", "37",
    ])

    # ---- UART backup header ----
    s.section("UART Program Header:", 300.0, 221.0, 368.3, 292.1)
    j4x, j4y = g(330.2), g(255.0)
    s.inst("Connector_Generic:Conn_01x04", "J4", "UART", j4x, j4y,
           "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical")
    j4 = pin_map(SYM / "Connector_Generic.kicad_sym", "Conn_01x04", j4x, j4y)
    s.glabel_on_pins(j4, {
        "1": "3V3", "2": "UART_TX", "3": "UART_RX", "4": "GND",
    })
    s.text("1=3V3 2=TX 3=RX 4=GND", 307.34, 281.94, 1.27)

    # ---- Flex sensors ----
    s.section("Flex Sensors (5×) + Dividers:", 12.7, 300.0, 203.2, 393.7)
    j2x, j2y = g(45.72), g(340.0)
    s.inst("Connector_Generic:Conn_01x07", "J2", "FLEX", j2x, j2y,
           "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical")
    j2 = pin_map(SYM / "Connector_Generic.kicad_sym", "Conn_01x07", j2x, j2y)
    s.glabel_on_pins(j2, {
        "1": "3V3", "2": "FLEX1", "3": "FLEX2", "4": "FLEX3",
        "5": "FLEX4", "6": "FLEX5", "7": "GND",
    })
    for i, (ref, net) in enumerate((
        ("R1", "FLEX1"), ("R2", "FLEX2"), ("R3", "FLEX3"),
        ("R4", "FLEX4"), ("R11", "FLEX5"),
    )):
        s.resistor_to_gnd(ref, "10k", 81.28 + i * 20.32, 340.0, net)
    s.text("J2: 3V3 · FLEX1..5 · GND", 25.4, 378.46, 1.27)

    # ---- IMU ----
    s.section("IMU (MPU-6050) I2C:", 215.9, 300.0, 368.3, 393.7)
    u4x, u4y = g(266.7), g(345.0)
    s.inst("Sensor_Motion:MPU-6050", "U4", "MPU-6050", u4x, u4y,
           "Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm")
    mpu = pin_map(SYM / "Sensor_Motion.kicad_sym", "MPU-6050", u4x, u4y)
    s.glabel_on_pins(mpu, {
        "8": "3V3", "9": "GND", "10": "REGOUT", "12": "IMU_INT", "13": "3V3",
        "18": "GND", "23": "SCL", "24": "SDA",
    })
    s.nc_pins(mpu, ["1", "6", "7", "11", "20"])
    s.cap_to_gnd("C10", "2.2uF", 330.2, 330.2, "REGOUT", "Capacitor_SMD:C_0805_2012Metric")
    s.cap_to_gnd("C9", "100nF", 348.0, 330.2, "3V3")
    s.text("Addr 0x68 · SDA=IO21 · SCL=IO22", 228.6, 378.46, 1.27)

    lib_block = "\n".join(libs)
    return f'''(kicad_sch
  (version 20231120)
  (generator "eeschema")
  (generator_version "8.0")
  (uuid "{uid()}")
  (paper "A2")
  (title_block
    (title "SignSpeak Smart Glove")
    (date "2026-07-19")
    (rev "H")
    (company "Man Who Embed")
    (comment 1 "USB-C+CH340 · TP4056+DW01 · ESP32 · MPU-6050 · 5× Flex")
  )
  (lib_symbols
{lib_block}
  )
{''.join(s.parts)}
  (sheet_instances
    (path "/" (page "1"))
  )
)
'''


def main():
    print("Generating complete schematic…")
    doc = build()
    OUT.write_text(doc)
    TEMPLATE.write_text(doc)
    print("Wrote", OUT, "bytes", OUT.stat().st_size)
    erc = ROOT / "fab" / "ERC_report.txt"
    r = subprocess.run(
        ["kicad-cli", "sch", "erc", "-o", str(erc), "--format", "report",
         "--severity-all", "--units", "mm", str(OUT)],
        capture_output=True, text=True,
    )
    print(r.stderr[:300] if r.stderr else "")
    print(erc.read_text()[:2500])
    # summarize
    text = erc.read_text()
    errors = text.count("; error")
    warns = text.count("; warning")
    print("SUMMARY errors=%d warnings=%d" % (errors, warns))


if __name__ == "__main__":
    main()
