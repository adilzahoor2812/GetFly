#!/usr/bin/env python3
"""
Generate Smart Glove schematic + dual-layer PCB previews and KiCad sources.

Architecture reconstructed from project collage (low-res; labels illegible):
  - Central ESP32-WROOM-32 MCU
  - 4 identical flex-sensor voltage-divider channels
  - LiPo charge + 3.3 V regulation
  - MPU-6050 IMU on I2C
  - USB programming / charge connector
  - Edge headers for finger flex sensors
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
DOCS.mkdir(parents=True, exist_ok=True)

# Colors matching typical KiCad / collage PCB (red top, blue bottom)
TOP_CU = (220, 48, 48)
BOT_CU = (40, 90, 200)
FR4 = (34, 92, 58)
SILK = (230, 230, 230)
PAD = (200, 170, 60)
BG = (18, 22, 28)
PANEL = (28, 34, 44)
LINE = (180, 190, 210)
ACCENT = (0, 192, 255)
TEXT = (240, 244, 250)
MUTED = (140, 150, 170)


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def font_bold(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return font(size)


def rounded_rect(draw, xy, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def box(draw, x, y, w, h, title, lines, fill=PANEL):
    rounded_rect(draw, (x, y, x + w, y + h), 10, fill=fill, outline=LINE, width=2)
    draw.text((x + 12, y + 8), title, fill=ACCENT, font=font_bold(15))
    ty = y + 32
    for line in lines:
        draw.text((x + 12, ty), line, fill=TEXT, font=font(12))
        ty += 16
    return x + w // 2, y + h // 2


def wire(draw, points, color=LINE, width=2):
    draw.line(points, fill=color, width=width)


def junction(draw, x, y):
    draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=ACCENT)


def generate_schematic() -> Path:
    W, H = 1600, 1100
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((40, 24), "Smart Glove Controller — Schematic", fill=TEXT, font=font_bold(28))
    d.text(
        (40, 60),
        "ESP32-WROOM-32  |  4× Flex Sensors  |  MPU-6050  |  TP4056 LiPo  |  AMS1117-3.3",
        fill=MUTED,
        font=font(14),
    )
    d.text((40, 82), "Reconstructed from project collage architecture (component values: design defaults)", fill=MUTED, font=font(12))

    # Power section (top)
    box(d, 60, 120, 220, 150, "J1 USB-C", ["VBUS 5V", "D+/D− → ESP32 USB", "GND", "CC 5.1k"])
    box(d, 320, 120, 220, 150, "U2 TP4056", ["BAT+ → LiPo", "PROG ≈ 1.2k → ~1A", "CHRG / STDBY LEDs", "OUT → VIN"])
    box(d, 580, 120, 220, 150, "U3 AMS1117-3.3", ["VIN from TP4056", "VOUT = 3V3", "Cin 10uF / Cout 22uF", "GND"])
    box(d, 840, 120, 200, 150, "BT1 LiPo 3.7V", ["JST 2-pin", "300–500 mAh", "Protection DW01"])
    box(d, 1080, 120, 200, 150, "PWR NETS", ["+5V (USB)", "+BAT", "3V3", "GND"])

    wire(d, [(280, 195), (320, 195)], ACCENT, 3)
    wire(d, [(540, 195), (580, 195)], ACCENT, 3)
    wire(d, [(800, 195), (840, 195)], (255, 180, 60), 3)
    wire(d, [(1040, 195), (1080, 195)], ACCENT, 3)

    # MCU center
    mcu_x, mcu_y = 620, 380
    box(
        d,
        mcu_x,
        mcu_y,
        360,
        320,
        "U1 ESP32-WROOM-32E",
        [
            "3V3 / EN / GND",
            "GPIO36  FLEX1 (ADC1_CH0)",
            "GPIO39  FLEX2 (ADC1_CH3)",
            "GPIO34  FLEX3 (ADC1_CH6)",
            "GPIO35  FLEX4 (ADC1_CH7)",
            "GPIO21  SDA  (IMU)",
            "GPIO22  SCL  (IMU)",
            "GPIO0 / GPIO2  BOOT / LED",
            "UART0 TX/RX  USB-UART",
            "Antenna: onboard PCB",
        ],
        fill=(32, 48, 64),
    )

    # Four identical flex channels (as in collage)
    flex_specs = [
        (60, 340, "CH1 Index", "GPIO36", "R1 10k"),
        (60, 520, "CH2 Middle", "GPIO39", "R2 10k"),
        (1220, 340, "CH3 Ring", "GPIO34", "R3 10k"),
        (1220, 520, "CH4 Pinky", "GPIO35", "R4 10k"),
    ]
    for x, y, title, gpio, rfix in flex_specs:
        box(
            d,
            x,
            y,
            260,
            150,
            f"Flex {title}",
            [
                "Flex sensor 2.2\" 10k–40k",
                f"Divider {rfix} to GND",
                f"Sense → {gpio}",
                "3V3 → sensor HI",
                "Decouple 100nF",
            ],
            fill=(40, 36, 52),
        )

    # Wires MCU ↔ flex
    wire(d, [(320, 415), (620, 460)], LINE, 2)
    wire(d, [(320, 595), (620, 520)], LINE, 2)
    wire(d, [(980, 460), (1220, 415)], LINE, 2)
    wire(d, [(980, 520), (1220, 595)], LINE, 2)

    # IMU
    box(
        d,
        620,
        740,
        360,
        140,
        "U4 MPU-6050",
        [
            "VCC 3V3 / GND",
            "SDA ← GPIO21   SCL ← GPIO22",
            "INT → GPIO19 (optional)",
            "AD0 → GND (addr 0x68)",
        ],
        fill=(36, 52, 44),
    )
    wire(d, [(800, 700), (800, 740)], LINE, 2)

    # Headers / misc
    box(d, 60, 740, 260, 140, "J2 Flex Header 1×6", ["1 3V3", "2 FLEX1", "3 FLEX2", "4 FLEX3", "5 FLEX4", "6 GND"])
    box(d, 1280, 740, 250, 140, "Indicators", ["D1 Power LED + R5 1k", "D2 CHRG (TP4056)", "D3 Status GPIO2", "SW1 BOOT"])

    # Title block
    rounded_rect(d, (1180, 920, 1560, 1060), 8, fill=PANEL, outline=LINE, width=2)
    d.text((1200, 935), "TITLE: Smart Glove MCU Board", fill=TEXT, font=font_bold(14))
    d.text((1200, 960), "REV: A   DATE: 2026-07-18", fill=MUTED, font=font(12))
    d.text((1200, 982), "SHEET: 1/1   SIZE: A3 landscape", fill=MUTED, font=font(12))
    d.text((1200, 1004), "NOTES: 4 flex channels as collage;", fill=MUTED, font=font(11))
    d.text((1200, 1022), "exact R/C values not readable in photo", fill=MUTED, font=font(11))

    # Legend matching collage style
    d.text((60, 920), "Legend", fill=ACCENT, font=font_bold(14))
    d.line([(60, 950), (120, 950)], fill=ACCENT, width=3)
    d.text((130, 942), "Power / 3V3", fill=TEXT, font=font(12))
    d.line([(60, 975), (120, 975)], fill=LINE, width=2)
    d.text((130, 967), "Signal", fill=TEXT, font=font(12))
    d.line([(60, 1000), (120, 1000)], fill=(255, 180, 60), width=3)
    d.text((130, 992), "Battery", fill=TEXT, font=font(12))

    out = DOCS / "smart_glove_schematic.png"
    img.save(out, "PNG", optimize=True)
    return out


def pad(draw, x, y, w=1.2, h=1.2, drill=0.6, scale=10, ox=0, oy=0):
    """Draw an SMD/through pad in mm coords."""
    sx, sy = ox + x * scale, oy + y * scale
    sw, sh = w * scale, h * scale
    draw.rectangle((sx - sw / 2, sy - sh / 2, sx + sw / 2, sy + sh / 2), fill=PAD)
    if drill:
        dr = drill * scale / 2
        draw.ellipse((sx - dr, sy - dr, sx + dr, sy + dr), fill=FR4)


def track(draw, pts_mm, color, width_mm, scale, ox, oy):
    pts = [(ox + x * scale, oy + y * scale) for x, y in pts_mm]
    draw.line(pts, fill=color, width=max(1, int(width_mm * scale)))


def generate_pcb() -> Path:
    # Board 50 × 40 mm — fits back-of-hand enclosure from collage
    board_w, board_h = 50.0, 40.0
    scale = 16  # px per mm
    margin = 80
    W = int(board_w * scale + margin * 2)
    H = int(board_h * scale + margin * 2 + 120)
    img = Image.new("RGB", (W, H), (12, 14, 18))
    d = ImageDraw.Draw(img)
    ox, oy = margin, margin + 70

    d.text((40, 24), "Smart Glove Controller — PCB Layout (2-layer)", fill=TEXT, font=font_bold(26))
    d.text((40, 58), "Top copper = RED   |   Bottom copper = BLUE   |   Pads = GOLD   |   Board = FR4", fill=MUTED, font=font(13))

    # Board outline
    bw, bh = board_w * scale, board_h * scale
    rounded_rect(d, (ox, oy, ox + bw, oy + bh), 12, fill=FR4, outline=(200, 210, 220), width=2)

    # Mounting holes (4 corners)
    for mx, my in [(3, 3), (47, 3), (3, 37), (47, 37)]:
        sx, sy = ox + mx * scale, oy + my * scale
        d.ellipse((sx - 8, sy - 8, sx + 8, sy + 8), fill=PAD)
        d.ellipse((sx - 4, sy - 4, sx + 4, sy + 4), fill=(20, 20, 20))

    # Bottom layer pour / traces (draw first)
    # Ground pour hint
    for i in range(6):
        track(d, [(4, 6 + i * 5), (46, 6 + i * 5)], (*BOT_CU, ), 0.25, scale, ox, oy)

    # Bottom: USB D+/D− stubs and GND returns
    track(d, [(8, 20), (12, 20), (12, 28), (18, 28)], BOT_CU, 0.35, scale, ox, oy)
    track(d, [(42, 12), (42, 30), (35, 30)], BOT_CU, 0.4, scale, ox, oy)

    # ESP32 module footprint center (typical 18×25.5 mm)
    esp_x, esp_y = 25, 18
    esp_w, esp_h = 18, 25.5
    ex = ox + (esp_x - esp_w / 2) * scale
    ey = oy + (esp_y - esp_h / 2) * scale
    d.rectangle((ex, ey, ex + esp_w * scale, ey + esp_h * scale), outline=SILK, width=2)
    d.text((ex + 8, ey + esp_h * scale / 2 - 8), "U1 ESP32-WROOM-32", fill=SILK, font=font(11))

    # ESP32 side pads (simplified castellation rows)
    for i in range(19):
        pad(d, esp_x - esp_w / 2, esp_y - esp_h / 2 + 1.27 * (i + 0.5), 1.5, 0.9, 0, scale, ox, oy)
        pad(d, esp_x + esp_w / 2, esp_y - esp_h / 2 + 1.27 * (i + 0.5), 1.5, 0.9, 0, scale, ox, oy)

    # Top traces from MCU to flex header (left edge)
    for i, gy in enumerate([10, 14, 18, 22]):
        track(
            d,
            [(esp_x - esp_w / 2, esp_y - 8 + i * 3), (6, esp_y - 8 + i * 3), (4, gy)],
            TOP_CU,
            0.3,
            scale,
            ox,
            oy,
        )
        pad(d, 2.5, gy, 1.8, 1.2, 0.8, scale, ox, oy)

    # Flex header silkscreen
    d.text((ox + 4, oy + 4 * scale), "J2 FLEX", fill=SILK, font=font(10))

    # Right side: TP4056 + AMS1117 region
    box_x, box_y = 40, 8
    for i in range(8):
        pad(d, box_x, box_y + i * 1.5, 1.2, 0.8, 0, scale, ox, oy)
    track(d, [(esp_x + esp_w / 2, 12), (38, 12), (38, 8), (40, 8)], TOP_CU, 0.5, scale, ox, oy)
    track(d, [(40, 14), (36, 14), (36, 20), (esp_x + esp_w / 2, 20)], TOP_CU, 0.4, scale, ox, oy)
    d.text((ox + 36 * scale, oy + 4 * scale), "U2/U3", fill=SILK, font=font(10))
    d.text((ox + 35 * scale, oy + 6 * scale), "CHG+LDO", fill=SILK, font=font(9))

    # USB-C on bottom edge
    usb_y = 38
    for ux in [20, 22, 24, 26, 28, 30]:
        pad(d, ux, usb_y, 0.6, 1.4, 0, scale, ox, oy)
    track(d, [(25, usb_y), (25, esp_y + esp_h / 2)], TOP_CU, 0.35, scale, ox, oy)
    d.text((ox + 19 * scale, oy + 35.5 * scale), "J1 USB-C", fill=SILK, font=font(10))

    # IMU footprint top-right of ESP
    imu_x, imu_y = 38, 28
    for dx in [-1.27, 0, 1.27]:
        for dy in [-1.27, 1.27]:
            pad(d, imu_x + dx, imu_y + dy, 0.9, 0.6, 0, scale, ox, oy)
    track(d, [(esp_x + esp_w / 2, 24), (imu_x - 2, 24), (imu_x - 2, imu_y)], TOP_CU, 0.25, scale, ox, oy)
    d.text((ox + 34 * scale, oy + 30 * scale), "U4 IMU", fill=SILK, font=font(9))

    # Decoupling caps near ESP
    for cx, cy in [(14, 8), (36, 8), (14, 30)]:
        pad(d, cx, cy, 1.0, 0.8, 0, scale, ox, oy)
        pad(d, cx + 1.6, cy, 1.0, 0.8, 0, scale, ox, oy)
        track(d, [(cx, cy), (cx + 1.6, cy)], TOP_CU, 0.2, scale, ox, oy)

    # Antenna keepout zone (ESP RF end)
    ax = ox + (esp_x - 4) * scale
    ay = oy + (esp_y - esp_h / 2 - 1) * scale
    d.rectangle((ax, ay - 10, ax + 8 * scale, ay + 4), outline=(255, 200, 80), width=1)
    d.text((ax, ay - 22), "RF KEEP-OUT", fill=(255, 200, 80), font=font(9))

    # Dimensions
    d.line([(ox, oy + bh + 20), (ox + bw, oy + bh + 20)], fill=MUTED, width=1)
    d.text((ox + bw / 2 - 30, oy + bh + 28), "50.0 mm", fill=MUTED, font=font(12))
    d.line([(ox + bw + 20, oy), (ox + bw + 20, oy + bh)], fill=MUTED, width=1)
    d.text((ox + bw + 28, oy + bh / 2), "40", fill=MUTED, font=font(12))

    # Layer legend
    ly = oy + bh + 55
    d.rectangle((ox, ly, ox + 20, ly + 12), fill=TOP_CU)
    d.text((ox + 28, ly), "F.Cu Top", fill=TEXT, font=font(12))
    d.rectangle((ox + 140, ly, ox + 160, ly + 12), fill=BOT_CU)
    d.text((ox + 168, ly), "B.Cu Bottom", fill=TEXT, font=font(12))
    d.rectangle((ox + 300, ly, ox + 320, ly + 12), fill=PAD)
    d.text((ox + 328, ly), "Pads / vias", fill=TEXT, font=font(12))

    out = DOCS / "smart_glove_pcb.png"
    img.save(out, "PNG", optimize=True)
    return out


def write_kicad_sch() -> Path:
    """Minimal but valid KiCad 8 schematic describing the design."""
    path = ROOT / "smart-glove.kicad_sch"
    content = r'''(kicad_sch
  (version 20231120)
  (generator "eeschema")
  (generator_version "8.0")
  (uuid "a1000001-0000-4000-8000-000000000001")
  (paper "A3")
  (title_block
    (title "Smart Glove Controller")
    (date "2026-07-18")
    (rev "A")
    (company "GetFly / Smart Glove")
    (comment 1 "ESP32 + 4 flex channels + MPU6050 + TP4056")
    (comment 2 "Reconstructed from project collage; photo labels illegible")
  )
  (lib_symbols)
  (text "Smart Glove Schematic — see docs/smart_glove_schematic.png for annotated diagram"
    (exclude_from_sim no) (exclude_from_bom no) (exclude_from_board no)
    (at 50 20 0)
    (effects (font (size 2 2)) (justify left))
    (uuid "a1000001-0000-4000-8000-000000000010")
  )
  (text "NETS: +5V +BAT 3V3 GND | FLEX1..4 | SDA SCL | USB_D+ USB_D-"
    (exclude_from_sim no) (exclude_from_bom no) (exclude_from_board no)
    (at 50 30 0)
    (effects (font (size 1.5 1.5)) (justify left))
    (uuid "a1000001-0000-4000-8000-000000000011")
  )
  (text "U1 ESP32-WROOM-32E | U2 TP4056 | U3 AMS1117-3.3 | U4 MPU-6050 | J1 USB-C | J2 1x6 flex | BT1 LiPo"
    (exclude_from_sim no) (exclude_from_bom no) (exclude_from_board no)
    (at 50 40 0)
    (effects (font (size 1.5 1.5)) (justify left))
    (uuid "a1000001-0000-4000-8000-000000000012")
  )
  (sheet_instances
    (path "/" (page "1"))
  )
)
'''
    path.write_text(content)
    return path


def write_kicad_pcb() -> Path:
    """KiCad 8 PCB with board outline, ESP32 courtyard, headers, USB zone."""
    path = ROOT / "smart-glove.kicad_pcb"
    # Coordinates in mm; KiCad uses nm in older formats but mm in sexpr with units
    content = r'''(kicad_pcb
  (version 20240108)
  (generator "pcbnew")
  (generator_version "8.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (title_block
    (title "Smart Glove Controller PCB")
    (date "2026-07-18")
    (rev "A")
    (company "GetFly / Smart Glove")
  )
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
      (plotfptext yes)
      (plotinvisibletext no)
      (sketchpadsonfab no)
      (subtractmaskfromsilk no)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "gerbers/")
    )
  )
  (net 0 "")
  (net 1 "GND")
  (net 2 "3V3")
  (net 3 "+5V")
  (net 4 "+BAT")
  (net 5 "FLEX1")
  (net 6 "FLEX2")
  (net 7 "FLEX3")
  (net 8 "FLEX4")
  (net 9 "SDA")
  (net 10 "SCL")
  (net 11 "USB_D+")
  (net 12 "USB_D-")

  (gr_rect
    (start 0 0)
    (end 50 40)
    (stroke (width 0.1) (type solid))
    (fill none)
    (layer "Edge.Cuts")
    (uuid "b2000001-0000-4000-8000-000000000001")
  )

  (gr_text "Smart Glove MCU Rev A"
    (at 25 2)
    (layer "F.SilkS")
    (uuid "b2000001-0000-4000-8000-000000000002")
    (effects (font (size 1.2 1.2) (thickness 0.15)) (justify center))
  )
  (gr_text "J2 FLEX 1-6"
    (at 4 8)
    (layer "F.SilkS")
    (uuid "b2000001-0000-4000-8000-000000000003")
    (effects (font (size 0.8 0.8) (thickness 0.12)) (justify left))
  )
  (gr_text "J1 USB-C"
    (at 25 38)
    (layer "F.SilkS")
    (uuid "b2000001-0000-4000-8000-000000000004")
    (effects (font (size 0.8 0.8) (thickness 0.12)) (justify center))
  )
  (gr_text "U1 ESP32-WROOM-32"
    (at 25 18)
    (layer "F.SilkS")
    (uuid "b2000001-0000-4000-8000-000000000005")
    (effects (font (size 1 1) (thickness 0.15)) (justify center))
  )
  (gr_text "RF KEEP-OUT"
    (at 25 4.5)
    (layer "Dwgs.User")
    (uuid "b2000001-0000-4000-8000-000000000006")
    (effects (font (size 0.7 0.7) (thickness 0.1)) (justify center))
  )

  (footprint "MountingHole:MountingHole_2.2mm_M2"
    (layer "F.Cu")
    (uuid "b2000001-0000-4000-8000-000000000010")
    (at 3 3)
    (property "Reference" "H1" (at 0 0) (layer "F.SilkS") (uuid "b2000001-0000-4000-8000-000000000011")
      (effects (font (size 0.8 0.8)))
    )
    (property "Value" "M2" (at 0 1.5) (layer "F.Fab") (uuid "b2000001-0000-4000-8000-000000000012")
      (effects (font (size 0.8 0.8)))
    )
    (pad "" np_thru_hole circle (at 0 0) (size 2.2 2.2) (drill 2.2) (layers "*.Cu" "*.Mask"))
  )
  (footprint "MountingHole:MountingHole_2.2mm_M2"
    (layer "F.Cu")
    (uuid "b2000001-0000-4000-8000-000000000020")
    (at 47 3)
    (property "Reference" "H2" (at 0 0) (layer "F.SilkS") (uuid "b2000001-0000-4000-8000-000000000021")
      (effects (font (size 0.8 0.8)))
    )
    (property "Value" "M2" (at 0 1.5) (layer "F.Fab") (uuid "b2000001-0000-4000-8000-000000000022")
      (effects (font (size 0.8 0.8)))
    )
    (pad "" np_thru_hole circle (at 0 0) (size 2.2 2.2) (drill 2.2) (layers "*.Cu" "*.Mask"))
  )
  (footprint "MountingHole:MountingHole_2.2mm_M2"
    (layer "F.Cu")
    (uuid "b2000001-0000-4000-8000-000000000030")
    (at 3 37)
    (property "Reference" "H3" (at 0 0) (layer "F.SilkS") (uuid "b2000001-0000-4000-8000-000000000031")
      (effects (font (size 0.8 0.8)))
    )
    (property "Value" "M2" (at 0 1.5) (layer "F.Fab") (uuid "b2000001-0000-4000-8000-000000000032")
      (effects (font (size 0.8 0.8)))
    )
    (pad "" np_thru_hole circle (at 0 0) (size 2.2 2.2) (drill 2.2) (layers "*.Cu" "*.Mask"))
  )
  (footprint "MountingHole:MountingHole_2.2mm_M2"
    (layer "F.Cu")
    (uuid "b2000001-0000-4000-8000-000000000040")
    (at 47 37)
    (property "Reference" "H4" (at 0 0) (layer "F.SilkS") (uuid "b2000001-0000-4000-8000-000000000041")
      (effects (font (size 0.8 0.8)))
    )
    (property "Value" "M2" (at 0 1.5) (layer "F.Fab") (uuid "b2000001-0000-4000-8000-000000000042")
      (effects (font (size 0.8 0.8)))
    )
    (pad "" np_thru_hole circle (at 0 0) (size 2.2 2.2) (drill 2.2) (layers "*.Cu" "*.Mask"))
  )

  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
    (layer "F.Cu")
    (uuid "b2000001-0000-4000-8000-000000000050")
    (at 2.5 10 270)
    (property "Reference" "J2" (at 0 -2) (layer "F.SilkS") (uuid "b2000001-0000-4000-8000-000000000051")
      (effects (font (size 0.8 0.8)))
    )
    (property "Value" "FLEX" (at 0 2) (layer "F.Fab") (uuid "b2000001-0000-4000-8000-000000000052")
      (effects (font (size 0.8 0.8)))
    )
    (pad "1" thru_hole rect (at 0 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (net 2 "3V3"))
    (pad "2" thru_hole circle (at 2.54 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (net 5 "FLEX1"))
    (pad "3" thru_hole circle (at 5.08 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (net 6 "FLEX2"))
    (pad "4" thru_hole circle (at 7.62 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (net 7 "FLEX3"))
    (pad "5" thru_hole circle (at 10.16 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (net 8 "FLEX4"))
    (pad "6" thru_hole circle (at 12.7 0) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (net 1 "GND"))
  )

  (segment (start 16 12) (end 8 12) (width 0.3) (layer "F.Cu") (net 5) (uuid "b2000001-0000-4000-8000-000000000060"))
  (segment (start 16 15) (end 8 15) (width 0.3) (layer "F.Cu") (net 6) (uuid "b2000001-0000-4000-8000-000000000061"))
  (segment (start 16 18) (end 8 18) (width 0.3) (layer "F.Cu") (net 7) (uuid "b2000001-0000-4000-8000-000000000062"))
  (segment (start 16 21) (end 8 21) (width 0.3) (layer "F.Cu") (net 8) (uuid "b2000001-0000-4000-8000-000000000063"))
  (segment (start 34 14) (end 42 14) (width 0.4) (layer "F.Cu") (net 2) (uuid "b2000001-0000-4000-8000-000000000064"))
  (segment (start 34 20) (end 42 20) (width 0.4) (layer "F.Cu") (net 1) (uuid "b2000001-0000-4000-8000-000000000065"))
  (segment (start 25 30) (end 25 36) (width 0.35) (layer "F.Cu") (net 3) (uuid "b2000001-0000-4000-8000-000000000066"))
  (segment (start 38 24) (end 38 28) (width 0.25) (layer "F.Cu") (net 9) (uuid "b2000001-0000-4000-8000-000000000067"))
  (segment (start 40 24) (end 40 28) (width 0.25) (layer "B.Cu") (net 10) (uuid "b2000001-0000-4000-8000-000000000068"))
  (segment (start 10 28) (end 20 28) (width 0.4) (layer "B.Cu") (net 1) (uuid "b2000001-0000-4000-8000-000000000069"))
  (segment (start 20 28) (end 40 28) (width 0.4) (layer "B.Cu") (net 1) (uuid "b2000001-0000-4000-8000-000000000070"))

  (via (at 8 12) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 5) (uuid "b2000001-0000-4000-8000-000000000080"))
  (via (at 8 15) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 6) (uuid "b2000001-0000-4000-8000-000000000081"))
  (via (at 34 20) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1) (uuid "b2000001-0000-4000-8000-000000000082"))

  (zone
    (net 1)
    (net_name "GND")
    (layer "B.Cu")
    (uuid "b2000001-0000-4000-8000-000000000090")
    (hatch edge 0.5)
    (connect_pads (clearance 0.3))
    (min_thickness 0.2)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon
      (pts
        (xy 1 1) (xy 49 1) (xy 49 39) (xy 1 39)
      )
    )
  )
)
'''
    path.write_text(content)
    return path


def write_project() -> Path:
    path = ROOT / "smart-glove.kicad_pro"
    path.write_text(
        """{
  "board": {
    "design_settings": {
      "defaults": {
        "board_outline_line_width": 0.1,
        "copper_line_width": 0.2,
        "copper_text_size_h": 1.5,
        "copper_text_size_v": 1.5,
        "copper_text_thickness": 0.3
      },
      "rules": {
        "min_copper_edge_clearance": 0.3,
        "min_hole_clearance": 0.25,
        "min_via_diameter": 0.6,
        "min_track_width": 0.2
      }
    }
  },
  "meta": {
    "filename": "smart-glove.kicad_pro",
    "version": 1
  },
  "sheets": [
    ["smart-glove.kicad_sch", "Root"]
  ],
  "text_variables": {}
}
"""
    )
    return path


def write_bom() -> Path:
    path = ROOT / "BOM.md"
    path.write_text(
        """# Smart Glove Controller — Bill of Materials (Rev A)

| Ref | Part | Value / Spec | Qty | Notes |
|-----|------|--------------|-----|-------|
| U1 | ESP32-WROOM-32E | Wi-Fi/BLE MCU module | 1 | Central MCU (collage) |
| U2 | TP4056 | LiPo charger IC / module | 1 | USB charge path |
| U3 | AMS1117-3.3 | 3.3 V LDO | 1 | Regulated rail |
| U4 | MPU-6050 | 6-axis IMU | 1 | Gesture / orientation |
| J1 | USB-C receptacle | 16-pin mid-mount | 1 | Charge + program |
| J2 | Pin header 1×6 | 2.54 mm | 1 | Flex sensor cable |
| BT1 | LiPo cell | 3.7 V 300–500 mAh | 1 | JST-PH |
| FS1–FS4 | Flex sensor | 2.2\" ~10k–40k | 4 | Index/Middle/Ring/Pinky |
| R1–R4 | Resistor 0603 | 10 kΩ | 4 | Voltage dividers |
| R5 | Resistor 0603 | 1 kΩ | 1 | Power LED |
| R6–R7 | Resistor 0603 | 5.1 kΩ | 2 | USB-C CC |
| C1–C4 | Cap 0603 | 100 nF | 4 | Decoupling |
| C5 | Cap 1206 | 10 µF | 1 | LDO input |
| C6 | Cap 1206 | 22 µF | 1 | LDO output |
| D1–D3 | LED 0603 | Power / CHRG / Status | 3 | Indicators |
| SW1 | Tactile switch | BOOT | 1 | Download mode |
| H1–H4 | M2 hardware | 2.2 mm holes | 4 | Case mount |

> Photo labels in the collage were not readable. Values above are standard defaults for this architecture — adjust after measuring your original board.
"""
    )
    return path


def write_readme() -> Path:
    path = ROOT / "README.md"
    path.write_text(
        """# Smart Glove — Schematic & PCB

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
"""
    )
    return path


def main():
    sch = generate_schematic()
    pcb = generate_pcb()
    write_kicad_sch()
    write_kicad_pcb()
    write_project()
    write_bom()
    write_readme()
    # Copy previews to artifacts for chat display
    art = Path("/opt/cursor/artifacts")
    art.mkdir(parents=True, exist_ok=True)
    Image.open(sch).save(art / "smart_glove_schematic.png")
    Image.open(pcb).save(art / "smart_glove_pcb.png")
    print("Wrote", sch)
    print("Wrote", pcb)
    print("KiCad project ready in", ROOT)


if __name__ == "__main__":
    main()
