#!/usr/bin/env python3
"""Generate a complete KiCad 8 schematic matching Smart Glove MCU Rev D."""

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
    libs.append(extract_symbol(SYM / "Connector_Generic.kicad_sym", "Conn_01x02"))
    libs.append(extract_symbol(SYM / "Connector.kicad_sym", "USB_C_Receptacle"))
    libs.append(extract_symbol(SYM / "RF_Module.kicad_sym", "ESP32-WROOM-32E"))
    # Embed under Device: to avoid "modified in library" warnings against Regulator_Linear
    ams = extract_symbol(SYM / "Regulator_Linear.kicad_sym", "AP1117-15")
    ams = ams.replace("Regulator_Linear:AP1117-15", "Device:AMS1117-3.3")
    ams = ams.replace('Value" "AP1117-15"', 'Value" "AMS1117-3.3"')
    ams = ams.replace("AP1117-15_0_1", "AMS1117-3.3_0_1").replace("AP1117-15_1_1", "AMS1117-3.3_1_1")
    libs.append(ams)
    libs.append(extract_symbol(SYM / "Sensor_Motion.kicad_sym", "MPU-6050"))
    # Avoid missing-lib warning: embed as Device:TP4056
    libs.append(tp4056_symbol().replace("GetFly:TP4056", "Device:TP4056"))

    s = Sch()
    s.text("SignSpeak Smart Glove — Complete Schematic (Rev F)", 25.4, 12.7, 2.54)
    s.text("Man Who Embed · USB-C · TP4056 · AMS1117 · ESP32 · MPU-6050 · 5× Flex", 25.4, 16.51, 1.27)

    # ---- USB-C ----
    s.text("1) USB-C Power/CC", 25.4, 25.4, 1.8)
    j1x, j1y = g(55.88), g(60.96)
    s.inst("Connector:USB_C_Receptacle", "J1", "USB-C", j1x, j1y,
           "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12")
    usb = pin_map(SYM / "Connector.kicad_sym", "USB_C_Receptacle", j1x, j1y)
    s.glabel_on_pins(usb, {
        "A4": "+5V", "A9": "+5V", "B4": "+5V", "B9": "+5V",
        "A5": "CC1", "B5": "CC2",
        "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
        "S1": "GND",
    })
    # Leave SBU (A8/B8) and unused USB data/SSTX/SSRX pins unconnected
    s.nc_pins(usb, [
        "A2", "A3", "A6", "A7", "A8", "A10", "A11",
        "B2", "B3", "B6", "B7", "B8", "B10", "B11",
    ])

    s.resistor_to_gnd("R6", "5.1k", 95.25, 40.64, "CC1")
    s.resistor_to_gnd("R7", "5.1k", 106.68, 40.64, "CC2")

    # ---- TP4056 ----
    s.text("2) LiPo Charger (TP4056)", 130.0, 25.4, 1.8)
    u2x, u2y = g(152.4), g(50.8)
    s.inst("Device:TP4056", "U2", "TP4056", u2x, u2y, "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
    # Custom symbol pins — apply same Y flip as library symbols (oy - py)
    s.label("GND", u2x - 10.16, u2y - 2.54, 0)        # TEMP local y=+2.54
    s.label("TP_PROG", u2x - 10.16, u2y - 0.0, 0)     # PROG
    s.label("GND", u2x - 10.16, u2y + 2.54, 0)        # GND local y=-2.54
    s.label("+5V", u2x - 10.16, u2y + 5.08, 0)        # VCC local y=-5.08
    s.label("+BAT", u2x + 10.16, u2y + 2.54, 180)     # BAT local y=-2.54
    s.nc(u2x + 10.16, u2y - 0.0)                       # STDBY
    s.label("CHRG", u2x + 10.16, u2y - 2.54, 180)     # CHRG local y=+2.54
    s.label("+5V", u2x + 10.16, u2y - 5.08, 180)      # CE local y=+5.08

    s.resistor_to_gnd("R8", "1.2k", 180.0, 50.8, "TP_PROG")
    s.led_series("D2", "LED-CHRG", 195.58, 45.72, "+5V", "CHRG")

    j3x, j3y = g(215.9), g(55.88)
    s.inst("Connector_Generic:Conn_01x02", "J3", "LiPo", j3x, j3y,
           "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical")
    s.label("+BAT", j3x - 5.08, j3y - 0.0, 0)          # local y=0
    s.label("GND", j3x - 5.08, j3y - (-2.54), 0)       # local y=-2.54 → oy-py

    # ---- AMS1117 ----
    s.text("3) 3.3V Regulator (AMS1117)", 25.4, 110.0, 1.8)
    u3x, u3y = g(50.8), g(130.0)
    s.inst("Device:AMS1117-3.3", "U3", "AMS1117-3.3", u3x, u3y, "Package_TO_SOT_SMD:SOT-223")
    amsp = pin_map(SYM / "Regulator_Linear.kicad_sym", "AP1117-15", u3x, u3y)
    s.glabel_on_pins(amsp, {"1": "GND", "2": "3V3", "3": "+BAT"})
    s.cap_to_gnd("C5", "10uF", 75.0, 130.0, "+BAT", "Capacitor_SMD:C_0805_2012Metric")
    s.cap_to_gnd("C6", "22uF", 90.0, 130.0, "3V3", "Capacitor_SMD:C_0805_2012Metric")
    s.cap_to_gnd("C7", "100nF", 105.0, 130.0, "3V3")

    # ---- ESP32 ----
    s.text("4) ESP32-WROOM-32E", 130.0, 110.0, 1.8)
    u1x, u1y = g(180.0), g(145.0)
    s.inst("RF_Module:ESP32-WROOM-32E", "U1", "ESP32-WROOM-32E", u1x, u1y, "RF_Module:ESP32-WROOM-32")
    esp = pin_map(SYM / "RF_Module.kicad_sym", "ESP32-WROOM-32E", u1x, u1y)
    s.glabel_on_pins(esp, {
        "1": "GND", "2": "3V3", "3": "EN",
        "4": "FLEX1", "5": "FLEX2", "6": "FLEX3", "7": "FLEX4", "8": "FLEX5",
        "15": "GND", "24": "STAT_LED", "25": "BOOT",
        "31": "IMU_INT", "33": "SDA", "36": "SCL", "38": "GND", "39": "GND",
    })
    # Only flag unused pins that are NOT already electrical type no_connect
    s.nc_pins(esp, [
        "9", "10", "11", "12", "13", "14", "16", "23",
        "26", "27", "28", "29", "30", "34", "35", "37",
    ])
    s.cap_to_gnd("C1", "100nF", 230.0, 120.0, "3V3")
    s.cap_to_gnd("C2", "100nF", 245.0, 120.0, "3V3")

    # ---- Controls ----
    s.text("5) BOOT / EN / Status LEDs", 25.4, 175.0, 1.8)
    # R9 EN pullup: top 3V3, bottom EN
    x, y = s.inst("Device:R", "R9", "10k", 40.64, 195.58, "Resistor_SMD:R_0603_1608Metric")
    s.label("3V3", x, y - 3.81, 90)
    s.label("EN", x, y + 3.81, 270)
    x, y = s.inst("Device:R", "R10", "10k", 55.88, 195.58, "Resistor_SMD:R_0603_1608Metric")
    s.label("3V3", x, y - 3.81, 90)
    s.label("BOOT", x, y + 3.81, 270)

    x, y = s.inst("Switch:SW_Push", "SW2", "EN", 75.0, 195.58, "Button_Switch_SMD:SW_SPST_B3U-1000P")
    s.label("EN", x - 5.08, y, 0)
    s.power("power:GND", "#PWR_SW2", "GND", x + 5.08, y)
    x, y = s.inst("Switch:SW_Push", "SW1", "BOOT", 100.0, 195.58, "Button_Switch_SMD:SW_SPST_B3U-1000P")
    s.label("BOOT", x - 5.08, y, 0)
    s.power("power:GND", "#PWR_SW1", "GND", x + 5.08, y)

    x, y = s.inst("Device:R", "R5", "1k", 125.0, 195.58, "Resistor_SMD:R_0603_1608Metric")
    s.label("3V3", x, y - 3.81, 90)
    s.label("PWR_LED", x, y + 3.81, 270)
    s.led_series("D1", "LED-PWR", 145.0, 195.58, "PWR_LED", "GND")
    # D1 cathode GND via label — also need power flag path; label GND is enough with power symbols
    s.led_series("D3", "LED-STAT", 165.0, 195.58, "STAT_LED", "GND")

    # ---- Flex (5 sensors: thumb + 4 fingers) ----
    s.text("6) Flex Sensor Header + Dividers (5×)", 25.4, 220.0, 1.8)
    j2x, j2y = g(50.8), g(245.0)
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
        s.resistor_to_gnd(ref, "10k", 80.0 + i * 15.24, 245.0, net)

    # ---- MPU ----
    s.text("7) IMU MPU-6050", 160.0, 220.0, 1.8)
    u4x, u4y = g(210.0), g(250.0)
    s.inst("Sensor_Motion:MPU-6050", "U4", "MPU-6050", u4x, u4y,
           "Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm")
    mpu = pin_map(SYM / "Sensor_Motion.kicad_sym", "MPU-6050", u4x, u4y)
    s.glabel_on_pins(mpu, {
        "8": "3V3", "9": "GND", "10": "REGOUT", "12": "IMU_INT", "13": "3V3",
        "18": "GND", "23": "SCL", "24": "SDA",
    })
    # Leave library no_connect pins alone; NC only active unused pins
    s.nc_pins(mpu, ["1", "6", "7", "11", "20"])
    s.cap_to_gnd("C10", "2.2uF", 255.0, 245.0, "REGOUT")
    s.cap_to_gnd("C9", "100nF", 270.0, 245.0, "3V3")

    # ---- Power flags (only on nets without an IC power_out driver) ----
    # +5V: USB receptacle pins are passive/power_in — needs PWR_FLAG
    # +BAT: driven by U2 BAT (power_out) — no flag
    # 3V3: driven by U3 VO (power_out) — no flag
    # GND: needs PWR_FLAG for ERC
    s.text("Power flags (ERC)", 25.4, 279.4, 1.8)
    s.power("power:+5V", "#PWR5V", "+5V", 40.64, 289.56)
    s.power("power:PWR_FLAG", "#FLG5V", "PWR_FLAG", 48.26, 289.56)
    s.wire(40.64, 289.56, 48.26, 289.56)

    s.power("power:GND", "#PWRGND", "GND", 69.85, 289.56)
    s.power("power:PWR_FLAG", "#FLGGND", "PWR_FLAG", 77.47, 289.56)
    s.wire(69.85, 289.56, 77.47, 289.56)

    lib_block = "\n".join(libs)
    return f'''(kicad_sch
  (version 20231120)
  (generator "eeschema")
  (generator_version "8.0")
  (uuid "{uid()}")
  (paper "A2")
  (title_block
    (title "SignSpeak Smart Glove")
    (date "2026-07-18")
    (rev "F")
    (company "Man Who Embed")
    (comment 1 "5× flex · ESP32 · TP4056 · AMS1117 · MPU-6050 · USB-C")
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
