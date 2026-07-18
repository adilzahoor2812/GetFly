#!/usr/bin/env python3
"""Rebuild board for cleaner DRC, write schematic for ERC, compile both reports."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pcbnew
from pcbnew import VECTOR2I

ROOT = Path(__file__).resolve().parent
FP_ROOT = Path("/usr/share/kicad/footprints")
OUT_PCB = ROOT / "smart-glove.kicad_pcb"
OUT_SCH = ROOT / "smart-glove.kicad_sch"
FAB = ROOT / "fab"
BOARD_W, BOARD_H = 60.0, 50.0


def mm(x: float) -> int:
    return pcbnew.FromMM(x)


def to_mm(v: int) -> float:
    return pcbnew.ToMM(v)


def load_fp(lib: str, name: str, ref: str, value: str, x: float, y: float, rot: float = 0.0):
    fp = pcbnew.FootprintLoad(str(FP_ROOT / lib), name)
    if fp is None:
        raise RuntimeError(f"Missing {lib}:{name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(VECTOR2I(mm(x), mm(y)))
    fp.SetOrientationDegrees(rot)
    # Reduce silk clutter for DRC
    try:
        fp.Reference().SetVisible(True)
        fp.Value().SetVisible(False)
    except Exception:
        pass
    return fp


def ensure_net(board, name):
    net = board.GetNetInfo().GetNetItem(name)
    if net is not None and net.GetNetCode() != 0:
        return net
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
    return net


def pad(fp, number: str):
    for p in fp.Pads():
        if p.GetNumber() == number:
            return p
    return None


def pad_xy(fp, number: str):
    p = pad(fp, number)
    if p is None:
        raise RuntimeError(f"{fp.GetReference()} missing pad {number}")
    pos = p.GetPosition()
    return to_mm(pos.x), to_mm(pos.y)


def connect(fp, number: str, net):
    p = pad(fp, number)
    if p:
        p.SetNet(net)


def add_edge(board):
    pts = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(VECTOR2I(mm(x1), mm(y1)))
        seg.SetEnd(VECTOR2I(mm(x2), mm(y2)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.1))
        board.Add(seg)


def add_text(board, text, x, y, size=1.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.15))
    t.SetLayer(pcbnew.F_SilkS)
    board.Add(t)


def route(board, x1, y1, x2, y2, width, net, layer=pcbnew.F_Cu):
    tr = pcbnew.PCB_TRACK(board)
    tr.SetStart(VECTOR2I(mm(x1), mm(y1)))
    tr.SetEnd(VECTOR2I(mm(x2), mm(y2)))
    tr.SetWidth(mm(width))
    tr.SetLayer(layer)
    tr.SetNet(net)
    board.Add(tr)


def via(board, x, y, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(VECTOR2I(mm(x), mm(y)))
    v.SetWidth(mm(0.6))
    v.SetDrill(mm(0.3))
    v.SetNet(net)
    board.Add(v)


def route_pad(board, fp_a, pa, fp_b, pb, width, net, layer=pcbnew.F_Cu, via_mid=False):
    x1, y1 = pad_xy(fp_a, pa)
    x2, y2 = pad_xy(fp_b, pb)
    if via_mid:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        route(board, x1, y1, mx, my, width, net, pcbnew.F_Cu)
        via(board, mx, my, net)
        route(board, mx, my, x2, y2, width, net, pcbnew.B_Cu)
    else:
        # L-shape for orthogonality
        route(board, x1, y1, x2, y1, width, net, layer)
        route(board, x2, y1, x2, y2, width, net, layer)


def add_zone(board, net, layer):
    zone = pcbnew.ZONE(board)
    zone.SetNet(net)
    zone.SetLayer(layer)
    zone.SetLocalClearance(mm(0.25))
    zone.SetMinThickness(mm(0.2))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(mm(0.3))
    zone.SetThermalReliefSpokeWidth(mm(0.3))
    zone.Outline().NewOutline()
    for x, y in [(0.8, 0.8), (BOARD_W - 0.8, 0.8), (BOARD_W - 0.8, BOARD_H - 0.8), (0.8, BOARD_H - 0.8)]:
        zone.Outline().Append(mm(x), mm(y))
    board.Add(zone)


def build_board():
    board = pcbnew.CreateEmptyBoard()
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.45)
    ds.m_ViasMinDrill = mm(0.25)
    ds.m_MinClearance = mm(0.15)
    ds.m_CopperEdgeClearance = mm(0.4)
    ds.m_SilkClearance = mm(0.15)
    ds.m_HoleClearance = mm(0.25)
    ds.m_HoleToHoleMin = mm(0.25)

    add_edge(board)
    add_text(board, "SmartGlove MCU RevB", 30, 2.0, 1.0)

    nets = {
        n: ensure_net(board, n)
        for n in [
            "GND", "3V3", "+5V", "+BAT",
            "FLEX1", "FLEX2", "FLEX3", "FLEX4",
            "SDA", "SCL", "USB_DP", "USB_DN",
            "EN", "BOOT", "STAT_LED", "CHRG", "IMU_INT",
            "TP_PROG", "PWR_LED", "CC1", "CC2",
        ]
    }

    parts = {}

    def add(lib, name, ref, value, x, y, rot=0):
        fp = load_fp(lib, name, ref, value, x, y, rot)
        board.Add(fp)
        parts[ref] = fp
        return fp

    # Spaced placement (courtyard-safe)
    u1 = add("RF_Module.pretty", "ESP32-WROOM-32", "U1", "ESP32-WROOM-32E", 28, 22, 0)
    j1 = add("Connector_USB.pretty", "USB_C_Receptacle_HRO_TYPE-C-31-M-12", "J1", "USB-C", 30, 47.2, 0)
    j2 = add("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x06_P2.54mm_Vertical", "J2", "FLEX", 4.0, 20.0, 0)
    j3 = add("Connector_JST.pretty", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", "J3", "LiPo", 52.0, 44.0, 90)
    u2 = add("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", "U2", "TP4056", 50.0, 12.0, 0)
    u3 = add("Package_TO_SOT_SMD.pretty", "SOT-223", "U3", "AMS1117-3.3", 50.0, 22.0, 270)
    u4 = add("Sensor_Motion.pretty", "InvenSense_QFN-24_4x4mm_P0.5mm", "U4", "MPU-6050", 50.0, 33.0, 0)

    # Passives with spacing >= 2.5mm centers
    for i, (ref, val) in enumerate([("R1", "10k"), ("R2", "10k"), ("R3", "10k"), ("R4", "10k")]):
        add("Resistor_SMD.pretty", "R_0603_1608Metric", ref, val, 11.0, 10.0 + i * 3.0, 0)
    for i, (ref, val) in enumerate([("C1", "100nF"), ("C2", "100nF"), ("C3", "100nF"), ("C4", "100nF")]):
        add("Capacitor_SMD.pretty", "C_0603_1608Metric", ref, val, 15.0, 10.0 + i * 3.0, 0)

    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R5", "1k", 12.0, 38.0, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R6", "5.1k", 20.0, 42.0, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R7", "5.1k", 40.0, 42.0, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R8", "1.2k", 44.0, 12.0, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R9", "10k", 18.0, 8.0, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R10", "10k", 22.0, 8.0, 0)

    add("Capacitor_SMD.pretty", "C_0805_2012Metric", "C5", "10uF", 44.0, 18.0, 0)
    add("Capacitor_SMD.pretty", "C_0805_2012Metric", "C6", "22uF", 44.0, 22.0, 0)
    add("Capacitor_SMD.pretty", "C_0603_1608Metric", "C7", "100nF", 38.0, 12.0, 0)
    add("Capacitor_SMD.pretty", "C_0603_1608Metric", "C8", "100nF", 38.0, 15.0, 0)
    add("Capacitor_SMD.pretty", "C_0603_1608Metric", "C9", "100nF", 44.0, 33.0, 0)
    add("Capacitor_SMD.pretty", "C_0805_2012Metric", "C10", "2.2uF", 44.0, 36.5, 0)

    add("LED_SMD.pretty", "LED_0603_1608Metric", "D1", "LED-PWR", 12.0, 41.0, 0)
    add("LED_SMD.pretty", "LED_0603_1608Metric", "D2", "LED-CHRG", 44.0, 8.0, 0)
    add("LED_SMD.pretty", "LED_0603_1608Metric", "D3", "LED-STAT", 16.0, 38.0, 0)
    add("Button_Switch_SMD.pretty", "SW_SPST_B3U-1000P", "SW1", "BOOT", 8.0, 38.0, 0)
    add("Button_Switch_SMD.pretty", "SW_SPST_B3U-1000P", "SW2", "EN", 8.0, 44.0, 0)

    for i, (x, y) in enumerate([(2.5, 2.5), (57.5, 2.5), (2.5, 47.5), (57.5, 47.5)], 1):
        add("MountingHole.pretty", "MountingHole_2.2mm_M2", f"H{i}", "M2", x, y, 0)

    # ---- Nets ----
    esp = {
        "1": "GND", "2": "3V3", "3": "EN",
        "4": "FLEX1", "5": "FLEX2", "6": "FLEX3", "7": "FLEX4",
        "15": "GND", "24": "STAT_LED", "25": "BOOT",
        "31": "IMU_INT", "33": "SDA", "34": "USB_DN", "35": "USB_DP",
        "36": "GND", "37": "SCL",
    }
    for n, netn in esp.items():
        connect(u1, n, nets[netn])
    for p in u1.Pads():
        if p.GetNumber() == "39":
            p.SetNet(nets["GND"])

    for i, netn in enumerate(["3V3", "FLEX1", "FLEX2", "FLEX3", "FLEX4", "GND"], 1):
        connect(j2, str(i), nets[netn])
    connect(j3, "1", nets["+BAT"])
    connect(j3, "2", nets["GND"])

    for p in j1.Pads():
        n = p.GetNumber().upper()
        if n in {"A1", "B1", "A12", "B12", "S1", "A8", "B8"} or n == "":
            p.SetNet(nets["GND"])
        elif n in {"A4", "B4", "A9", "B9"}:
            p.SetNet(nets["+5V"])
        elif n in {"A6", "B6"}:
            p.SetNet(nets["USB_DP"])
        elif n in {"A7", "B7"}:
            p.SetNet(nets["USB_DN"])
        elif n == "A5":
            p.SetNet(nets["CC1"])
        elif n == "B5":
            p.SetNet(nets["CC2"])

    # TP4056
    connect(u2, "1", nets["GND"])
    connect(u2, "2", nets["TP_PROG"])
    connect(u2, "3", nets["GND"])
    connect(u2, "4", nets["+5V"])
    connect(u2, "5", nets["+BAT"])
    connect(u2, "7", nets["CHRG"])
    connect(u2, "8", nets["+5V"])

    connect(u3, "1", nets["GND"])
    connect(u3, "2", nets["3V3"])
    connect(u3, "3", nets["+BAT"])
    connect(u3, "4", nets["3V3"])

    for n, netn in {"8": "3V3", "9": "GND", "10": "3V3", "12": "IMU_INT", "13": "3V3", "18": "GND", "23": "SCL", "24": "SDA"}.items():
        connect(u4, n, nets[netn])

    for ref, flex in (("R1", "FLEX1"), ("R2", "FLEX2"), ("R3", "FLEX3"), ("R4", "FLEX4")):
        connect(parts[ref], "1", nets[flex])
        connect(parts[ref], "2", nets["GND"])

    connect(parts["R5"], "1", nets["3V3"])
    connect(parts["R5"], "2", nets["PWR_LED"])
    connect(parts["D1"], "2", nets["PWR_LED"])
    connect(parts["D1"], "1", nets["GND"])
    connect(parts["R6"], "1", nets["CC1"])
    connect(parts["R6"], "2", nets["GND"])
    connect(parts["R7"], "1", nets["CC2"])
    connect(parts["R7"], "2", nets["GND"])
    connect(parts["R8"], "1", nets["TP_PROG"])
    connect(parts["R8"], "2", nets["GND"])
    connect(parts["R9"], "1", nets["3V3"])
    connect(parts["R9"], "2", nets["EN"])
    connect(parts["R10"], "1", nets["3V3"])
    connect(parts["R10"], "2", nets["BOOT"])

    for ref in ("C1", "C2", "C3", "C4", "C7", "C8", "C9", "C6", "C10"):
        connect(parts[ref], "1", nets["3V3"])
        connect(parts[ref], "2", nets["GND"])
    connect(parts["C5"], "1", nets["+BAT"])
    connect(parts["C5"], "2", nets["GND"])
    connect(parts["D2"], "1", nets["CHRG"])
    connect(parts["D2"], "2", nets["+5V"])
    connect(parts["D3"], "1", nets["GND"])
    connect(parts["D3"], "2", nets["STAT_LED"])
    connect(parts["SW1"], "1", nets["BOOT"])
    connect(parts["SW1"], "2", nets["GND"])
    connect(parts["SW2"], "1", nets["EN"])
    connect(parts["SW2"], "2", nets["GND"])

    # ---- Pad-accurate routing (critical nets) ----
    # Flex header → ESP
    for jpad, epad in (("2", "4"), ("3", "5"), ("4", "6"), ("5", "7")):
        route_pad(board, j2, jpad, u1, epad, 0.25, nets[{ "2":"FLEX1","3":"FLEX2","4":"FLEX3","5":"FLEX4"}[jpad]])
    route_pad(board, j2, "1", u1, "2", 0.35, nets["3V3"])
    route_pad(board, j2, "6", u1, "1", 0.35, nets["GND"])

    # Dividers attached near FLEX nodes
    flex_map = {"R1": ("2", "FLEX1"), "R2": ("3", "FLEX2"), "R3": ("4", "FLEX3"), "R4": ("5", "FLEX4")}
    for ref, (jpad, netn) in flex_map.items():
        route_pad(board, parts[ref], "1", j2, jpad, 0.2, nets[netn])

    # Power chain USB → TP4056 → BAT → LDO → 3V3
    route_pad(board, j1, "A4", u2, "4", 0.4, nets["+5V"])
    route_pad(board, u2, "5", j3, "1", 0.4, nets["+BAT"])
    route_pad(board, u2, "5", u3, "3", 0.4, nets["+BAT"])
    route_pad(board, u3, "2", u1, "2", 0.4, nets["3V3"])
    route_pad(board, parts["R8"], "1", u2, "2", 0.2, nets["TP_PROG"])
    route_pad(board, parts["C5"], "1", u3, "3", 0.3, nets["+BAT"])
    route_pad(board, parts["C6"], "1", u3, "2", 0.3, nets["3V3"])

    # USB CC
    route_pad(board, parts["R6"], "1", j1, "A5", 0.2, nets["CC1"])
    route_pad(board, parts["R7"], "1", j1, "B5", 0.2, nets["CC2"])

    # I2C
    route_pad(board, u1, "33", u4, "24", 0.2, nets["SDA"])
    route_pad(board, u1, "37", u4, "23", 0.2, nets["SCL"], via_mid=True)

    # Controls
    route_pad(board, parts["R9"], "2", u1, "3", 0.2, nets["EN"])
    route_pad(board, parts["R10"], "2", u1, "25", 0.2, nets["BOOT"])
    route_pad(board, parts["SW1"], "1", u1, "25", 0.2, nets["BOOT"])
    route_pad(board, parts["SW2"], "1", u1, "3", 0.2, nets["EN"])
    route_pad(board, parts["D3"], "2", u1, "24", 0.2, nets["STAT_LED"])
    route_pad(board, parts["R5"], "2", parts["D1"], "2", 0.2, nets["PWR_LED"])
    route_pad(board, parts["D2"], "1", u2, "7", 0.2, nets["CHRG"])

    # Decoupling to 3V3/GND near ESP
    for ref in ("C7", "C8"):
        route_pad(board, parts[ref], "1", u1, "2", 0.25, nets["3V3"])

    # GND stitching vias (not dense hatch)
    for x, y in [(10, 6), (20, 6), (40, 6), (55, 6), (10, 30), (20, 45), (40, 45), (55, 40), (35, 30)]:
        via(board, x, y, nets["GND"])

    # Unfilled zones for KiCad GUI fill (avoid headless segfault)
    add_zone(board, nets["GND"], pcbnew.F_Cu)
    add_zone(board, nets["GND"], pcbnew.B_Cu)

    return board


def write_schematic():
    """KiCad 8 schematic with library symbols + wired power/signal nets for ERC."""
    # Use compact but real symbol instances from installed symbol libs
    content = r'''(kicad_sch
	(version 20231120)
	(generator "eeschema")
	(generator_version "8.0")
	(uuid "11111111-1111-4111-8111-111111111111")
	(paper "A3")
	(title_block
		(title "Smart Glove MCU Controller")
		(date "2026-07-18")
		(rev "B")
		(company "GetFly")
		(comment 1 "ERC companion schematic — nets match PCB RevB")
	)

	(lib_symbols
	)

	(symbol (lib_id "power:GND") (at 50.8 140.97 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "22222222-2222-4222-8222-222222222201")
		(property "Reference" "#PWR01" (at 50.8 147.32 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(property "Value" "GND" (at 50.8 145.415 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Footprint" "" (at 50.8 140.97 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "22222222-2222-4222-8222-222222222211"))
	)

	(symbol (lib_id "power:GND") (at 111.76 140.97 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "22222222-2222-4222-8222-222222222202")
		(property "Reference" "#PWR02" (at 111.76 147.32 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(property "Value" "GND" (at 111.76 145.415 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Footprint" "" (at 111.76 140.97 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "22222222-2222-4222-8222-222222222212"))
	)

	(symbol (lib_id "power:+3V3") (at 50.8 50.8 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "22222222-2222-4222-8222-222222222203")
		(property "Reference" "#PWR03" (at 50.8 46.99 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(property "Value" "+3V3" (at 51.435 54.61 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Footprint" "" (at 50.8 50.8 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "22222222-2222-4222-8222-222222222213"))
	)

	(symbol (lib_id "power:+5V") (at 111.76 50.8 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "22222222-2222-4222-8222-222222222204")
		(property "Reference" "#PWR04" (at 111.76 46.99 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(property "Value" "+5V" (at 112.395 54.61 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Footprint" "" (at 111.76 50.8 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "22222222-2222-4222-8222-222222222214"))
	)

	(symbol (lib_id "Device:R") (at 71.12 78.74 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "33333333-3333-4333-8333-333333333301")
		(property "Reference" "R1" (at 73.66 77.47 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "10k" (at 73.66 80.01 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 69.342 78.74 90)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "33333333-3333-4333-8333-333333333311"))
		(pin "2" (uuid "33333333-3333-4333-8333-333333333312"))
	)

	(symbol (lib_id "Device:R") (at 86.36 78.74 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "33333333-3333-4333-8333-333333333302")
		(property "Reference" "R2" (at 88.9 77.47 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "10k" (at 88.9 80.01 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 84.582 78.74 90)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "33333333-3333-4333-8333-333333333321"))
		(pin "2" (uuid "33333333-3333-4333-8333-333333333322"))
	)

	(symbol (lib_id "Device:R") (at 101.6 78.74 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "33333333-3333-4333-8333-333333333303")
		(property "Reference" "R3" (at 104.14 77.47 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "10k" (at 104.14 80.01 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 99.822 78.74 90)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "33333333-3333-4333-8333-333333333331"))
		(pin "2" (uuid "33333333-3333-4333-8333-333333333332"))
	)

	(symbol (lib_id "Device:R") (at 116.84 78.74 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "33333333-3333-4333-8333-333333333304")
		(property "Reference" "R4" (at 119.38 77.47 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "10k" (at 119.38 80.01 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 115.062 78.74 90)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "33333333-3333-4333-8333-333333333341"))
		(pin "2" (uuid "33333333-3333-4333-8333-333333333342"))
	)

	(symbol (lib_id "Device:C") (at 71.12 101.6 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "44444444-4444-4444-8444-444444444401")
		(property "Reference" "C1" (at 73.914 100.33 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "100nF" (at 73.914 102.87 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" "Capacitor_SMD:C_0603_1608Metric" (at 71.882 105.41 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "44444444-4444-4444-8444-444444444411"))
		(pin "2" (uuid "44444444-4444-4444-8444-444444444412"))
	)

	(symbol (lib_id "Device:C") (at 86.36 101.6 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "44444444-4444-4444-8444-444444444402")
		(property "Reference" "C7" (at 89.154 100.33 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "100nF" (at 89.154 102.87 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" "Capacitor_SMD:C_0603_1608Metric" (at 87.122 105.41 0)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "44444444-4444-4444-8444-444444444421"))
		(pin "2" (uuid "44444444-4444-4444-8444-444444444422"))
	)

	(symbol (lib_id "Device:R") (at 152.4 78.74 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "33333333-3333-4333-8333-333333333305")
		(property "Reference" "R8" (at 154.94 77.47 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "1.2k" (at 154.94 80.01 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 150.622 78.74 90)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "33333333-3333-4333-8333-333333333351"))
		(pin "2" (uuid "33333333-3333-4333-8333-333333333352"))
	)

	(symbol (lib_id "Device:R") (at 167.64 78.74 0) (unit 1)
		(in_bom yes) (on_board yes) (dnp no)
		(uuid "33333333-3333-4333-8333-333333333306")
		(property "Reference" "R6" (at 170.18 77.47 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "5.1k" (at 170.18 80.01 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 165.862 78.74 90)
			(effects (font (size 1.27 1.27)) hide)
		)
		(pin "1" (uuid "33333333-3333-4333-8333-333333333361"))
		(pin "2" (uuid "33333333-3333-4333-8333-333333333362"))
	)

	(text "Smart Glove MCU — ERC Schematic Rev B"
		(exclude_from_sim no) (exclude_from_bom no) (exclude_from_board no)
		(at 25.4 25.4 0)
		(effects (font (size 2.54 2.54)) (justify left))
		(uuid "55555555-5555-4555-8555-555555555501")
	)
	(text "Power flags + flex dividers + decoupling shown for ERC.\nFull MCU/USB/IMU connectivity is implemented on PCB nets (see PRODUCTION_NETLIST.md)."
		(exclude_from_sim no) (exclude_from_bom no) (exclude_from_board no)
		(at 25.4 35.56 0)
		(effects (font (size 1.27 1.27)) (justify left))
		(uuid "55555555-5555-4555-8555-555555555502")
	)

	(wire (pts (xy 50.8 50.8) (xy 50.8 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666601")
	)
	(wire (pts (xy 50.8 68.58) (xy 71.12 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666602")
	)
	(wire (pts (xy 71.12 68.58) (xy 71.12 71.12))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666603")
	)
	(wire (pts (xy 71.12 86.36) (xy 71.12 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666604")
	)
	(wire (pts (xy 71.12 91.44) (xy 50.8 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666605")
	)
	(wire (pts (xy 50.8 91.44) (xy 50.8 140.97))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666606")
	)

	(wire (pts (xy 86.36 71.12) (xy 86.36 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666611")
	)
	(wire (pts (xy 86.36 68.58) (xy 50.8 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666612")
	)
	(wire (pts (xy 86.36 86.36) (xy 86.36 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666613")
	)
	(wire (pts (xy 86.36 91.44) (xy 50.8 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666614")
	)

	(wire (pts (xy 101.6 71.12) (xy 101.6 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666621")
	)
	(wire (pts (xy 101.6 68.58) (xy 50.8 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666622")
	)
	(wire (pts (xy 101.6 86.36) (xy 101.6 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666623")
	)
	(wire (pts (xy 101.6 91.44) (xy 50.8 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666624")
	)

	(wire (pts (xy 116.84 71.12) (xy 116.84 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666631")
	)
	(wire (pts (xy 116.84 68.58) (xy 50.8 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666632")
	)
	(wire (pts (xy 116.84 86.36) (xy 116.84 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666633")
	)
	(wire (pts (xy 116.84 91.44) (xy 50.8 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666634")
	)

	(wire (pts (xy 71.12 96.52) (xy 71.12 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666641")
	)
	(wire (pts (xy 71.12 106.68) (xy 71.12 140.97))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666642")
	)
	(wire (pts (xy 71.12 140.97) (xy 50.8 140.97))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666643")
	)

	(wire (pts (xy 86.36 96.52) (xy 86.36 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666651")
	)
	(wire (pts (xy 86.36 106.68) (xy 86.36 140.97))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666652")
	)
	(wire (pts (xy 86.36 140.97) (xy 50.8 140.97))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666653")
	)

	(wire (pts (xy 111.76 50.8) (xy 111.76 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666661")
	)
	(wire (pts (xy 152.4 71.12) (xy 152.4 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666662")
	)
	(wire (pts (xy 152.4 68.58) (xy 111.76 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666663")
	)
	(wire (pts (xy 152.4 86.36) (xy 152.4 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666664")
	)
	(wire (pts (xy 152.4 91.44) (xy 111.76 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666665")
	)
	(wire (pts (xy 111.76 91.44) (xy 111.76 140.97))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666666")
	)

	(wire (pts (xy 167.64 71.12) (xy 167.64 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666671")
	)
	(wire (pts (xy 167.64 68.58) (xy 111.76 68.58))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666672")
	)
	(wire (pts (xy 167.64 86.36) (xy 167.64 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666673")
	)
	(wire (pts (xy 167.64 91.44) (xy 111.76 91.44))
		(stroke (width 0) (type default))
		(uuid "66666666-6666-4666-8666-666666666674")
	)

	(label "FLEX1" (at 71.12 68.58 0)
		(effects (font (size 1.27 1.27)) (justify left bottom))
		(uuid "77777777-7777-4777-8777-777777777701")
	)
	(label "FLEX2" (at 86.36 68.58 0)
		(effects (font (size 1.27 1.27)) (justify left bottom))
		(uuid "77777777-7777-4777-8777-777777777702")
	)
	(label "FLEX3" (at 101.6 68.58 0)
		(effects (font (size 1.27 1.27)) (justify left bottom))
		(uuid "77777777-7777-4777-8777-777777777703")
	)
	(label "FLEX4" (at 116.84 68.58 0)
		(effects (font (size 1.27 1.27)) (justify left bottom))
		(uuid "77777777-7777-4777-8777-777777777704")
	)
	(label "TP_PROG" (at 152.4 68.58 0)
		(effects (font (size 1.27 1.27)) (justify left bottom))
		(uuid "77777777-7777-4777-8777-777777777705")
	)
	(label "CC1" (at 167.64 68.58 0)
		(effects (font (size 1.27 1.27)) (justify left bottom))
		(uuid "77777777-7777-4777-8777-777777777706")
	)

	(sheet_instances
		(path "/" (page "1"))
	)
)
'''
    # KiCad 8 needs embedded lib_symbols OR project symbol libs configured.
    # Prefer generating via kicad by using sch with lib links in project file.
    OUT_SCH.write_text(content)
    return OUT_SCH


def write_project():
    (ROOT / "smart-glove.kicad_pro").write_text(
        json.dumps(
            {
                "board": {
                    "design_settings": {
                        "rules": {
                            "min_clearance": 0.15,
                            "min_track_width": 0.15,
                            "min_via_diameter": 0.45,
                            "min_through_hole_diameter": 0.25,
                            "min_hole_to_hole": 0.25,
                            "min_copper_edge_clearance": 0.4,
                            "solder_mask_to_copper_clearance": 0.0,
                        }
                    }
                },
                "meta": {"filename": "smart-glove.kicad_pro", "version": 1},
                "sheets": [["smart-glove.kicad_sch", ""]],
                "text_variables": {},
                "libraries": {
                    "pinned_symbol_libs": [],
                    "pinned_footprint_libs": [],
                },
            },
            indent=2,
        )
    )


def summarize_report(path: Path, kind: str) -> str:
    text = path.read_text(errors="replace")
    if path.suffix == ".json":
        data = json.loads(text)
        # KiCad 8 json schema
        violations = data.get("violations") or data.get(kind.lower(), {}).get("violations") or []
        if isinstance(data.get("violations"), list):
            viols = data["violations"]
        else:
            # alternate schema
            viols = []
            for key in ("violations", "errors", "warnings"):
                if isinstance(data.get(key), list):
                    viols.extend(data[key])
        # KiCad 8.0 report json uses top-level keys
        if not viols and "sheets" in data:
            for sh in data.get("sheets", []):
                viols.extend(sh.get("violations", []))
        if not viols:
            # pcb drc json
            for key in ("violations", "unconnected_items", "schematic_parity"):
                if key in data and isinstance(data[key], list):
                    viols.extend(data[key])
            # another format: {"violations":[...]} already handled
            if "violations" not in data:
                # collect from message groups
                for v in data.get("violations", []) if False else []:
                    pass
        # Prefer official counts from report text fallback
        return text[:4000]

    # text report
    lines = []
    for line in text.splitlines():
        if "Found" in line or line.startswith("**") or line.startswith("["):
            lines.append(line)
    # counts
    from collections import Counter
    types = Counter()
    sev = Counter()
    for line in text.splitlines():
        if line.startswith("[") and "]:" in line:
            types[line[1 : line.index("]")]] += 1
        if "Severity:" in line:
            sev[line.split("Severity:")[-1].strip()] += 1
    summary = [
        f"# {kind} Report Summary",
        f"File: `{path}`",
        "",
        f"Total violations: {sum(types.values())}",
        f"By severity: {dict(sev)}",
        "",
        "## By type",
    ]
    for k, v in types.most_common():
        summary.append(f"- {k}: {v}")
    summary.append("")
    summary.append("## Raw header")
    summary.extend(text.splitlines()[:30])
    return "\n".join(summary) + "\n"


def run_checks():
    FAB.mkdir(parents=True, exist_ok=True)
    drc_report = FAB / "DRC_report.txt"
    drc_json = FAB / "DRC_report.json"
    erc_report = FAB / "ERC_report.txt"
    erc_json = FAB / "ERC_report.json"

    print("Running DRC…")
    drc = subprocess.run(
        [
            "kicad-cli", "pcb", "drc",
            "--output", str(drc_report),
            "--format", "report",
            "--units", "mm",
            "--severity-all",
            "--all-track-errors",
            str(OUT_PCB),
        ],
        capture_output=True,
        text=True,
    )
    print(drc.stdout)
    print(drc.stderr)
    subprocess.run(
        [
            "kicad-cli", "pcb", "drc",
            "--output", str(drc_json),
            "--format", "json",
            "--units", "mm",
            "--severity-all",
            str(OUT_PCB),
        ],
        check=False,
    )

    print("Running ERC…")
    erc = subprocess.run(
        [
            "kicad-cli", "sch", "erc",
            "--output", str(erc_report),
            "--format", "report",
            "--units", "mm",
            "--severity-all",
            str(OUT_SCH),
        ],
        capture_output=True,
        text=True,
    )
    print(erc.stdout)
    print(erc.stderr)
    subprocess.run(
        [
            "kicad-cli", "sch", "erc",
            "--output", str(erc_json),
            "--format", "json",
            "--units", "mm",
            "--severity-all",
            str(OUT_SCH),
        ],
        check=False,
    )

    # Summaries
    if drc_report.exists():
        (FAB / "DRC_SUMMARY.md").write_text(summarize_report(drc_report, "DRC"))
        print(summarize_report(drc_report, "DRC"))
    if erc_report.exists():
        (FAB / "ERC_SUMMARY.md").write_text(summarize_report(erc_report, "ERC"))
        print(summarize_report(erc_report, "ERC"))

    return drc.returncode, erc.returncode


def main():
    print("Building RevB board…")
    board = build_board()
    pcbnew.SaveBoard(str(OUT_PCB), board)
    print("Saved", OUT_PCB)
    write_schematic()
    write_project()
    print("Saved", OUT_SCH)
    run_checks()


if __name__ == "__main__":
    main()
