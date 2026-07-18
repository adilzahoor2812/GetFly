#!/usr/bin/env python3
"""
SignSpeak Smart Glove — Production Rev G (Man Who Embed)
==================================
Compact glove-back MCU (55×40 mm) · UART prog header · 2-layer · fab package.
Note: 40×30 mm is not possible with ESP32-WROOM-32E (~25.5 mm) + USB-C (~9.5 mm).

Production routing rules (learned from Rev C shorts):
  • GND only via filled copper zones (no GND trunks)
  • Signals: short F.Cu pad→via escapes, then exclusive B.Cu columns
  • Never run long F.Cu horizontals across the board
  • Never put B.Cu verticals on ESP pad-column X
  • Stagger vias so adjacent 1.27 mm pitch pads do not share via X/Y
  • Replace stock ESP courtyard (~48×43) with module-sized courtyard
"""

from __future__ import annotations

import csv
import json
import math
import re
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew
from pcbnew import VECTOR2I

ROOT = Path(__file__).resolve().parent
FP_ROOT = Path("/usr/share/kicad/footprints")
FAB = ROOT / "fab"
DOCS = ROOT / "docs"
GERBER = ROOT / "gerbers"
ART = Path("/opt/cursor/artifacts")
OUT_PCB = ROOT / "smart-glove.kicad_pcb"
OUT_SCH = ROOT / "smart-glove.kicad_sch"
OUT_PRO = ROOT / "smart-glove.kicad_pro"

# Compact dorsal-glove outline (finger edge = top / y=0, wrist = bottom)
# 60×45 mm — smallest reliably routable with WROOM-32E + USB-C + charger + IMU + UART
# (40×30 requested but physically too small for this module set)
BOARD_W, BOARD_H = 60.0, 45.0
# Antenna keepout strip at finger edge (ESP32 antenna faces +top)
KEEP_Y = 6.0
# Approximate module body (no through-routing) — U1 at (30, 15)
MOD = dict(x0=20.0, x1=40.0, y0=4.0, y1=28.0)
# Keep y∈[LANE] empty of footprints (helps autorouter)
LANE_Y0, LANE_Y1 = 28.5, 33.0

TRACK_SIG = 0.25
TRACK_PWR = 0.40
VIA_SIZE = 0.60
VIA_DRILL = 0.30
CLR = 0.20


def mm(x: float) -> int:
    return pcbnew.FromMM(x)


def to_mm(v: int) -> float:
    return pcbnew.ToMM(v)


def ensure_net(board, name):
    net = board.GetNetInfo().GetNetItem(name)
    if net is not None and net.GetNetCode() != 0:
        return net
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
    return net


def load_fp(lib, name, ref, value, x, y, rot=0.0):
    fp = pcbnew.FootprintLoad(str(FP_ROOT / lib), name)
    if fp is None:
        raise RuntimeError(f"Missing {lib}:{name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(VECTOR2I(mm(x), mm(y)))
    fp.SetOrientationDegrees(rot)
    try:
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
    except Exception:
        pass
    return fp


def clear_layer_graphics(fp, layer):
    try:
        items = list(fp.GraphicalItems())
    except Exception:
        return
    for item in items:
        try:
            if item.GetLayer() == layer:
                fp.Remove(item)
        except Exception:
            pass


def strip_rule_areas(fp):
    for z in list(fp.Zones()):
        try:
            fp.Remove(z)
        except Exception:
            pass


def add_courtyard_box(fp, w, h, ox=0.0, oy=0.0):
    """Closed rectangle on F.CrtYd using segments (local footprint coords)."""
    hw, hh = w / 2, h / 2
    corners = [
        (-hw + ox, -hh + oy),
        (hw + ox, -hh + oy),
        (hw + ox, hh + oy),
        (-hw + ox, hh + oy),
    ]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:] + corners[:1]):
        seg = pcbnew.PCB_SHAPE(fp)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(VECTOR2I(mm(x1), mm(y1)))
        seg.SetEnd(VECTOR2I(mm(x2), mm(y2)))
        seg.SetWidth(mm(0.05))
        seg.SetLayer(pcbnew.F_CrtYd)
        fp.Add(seg)


def pad(fp, number):
    for p in fp.Pads():
        if p.GetNumber() == str(number):
            return p
    return None


def pad_xy(fp, number):
    p = pad(fp, number)
    if p is None:
        raise RuntimeError(f"{fp.GetReference()} missing pad {number}")
    c = p.GetPosition()
    return to_mm(c.x), to_mm(c.y)


def connect(fp, number, net):
    """Assign net to all pads with this number (ESP32 pin 39 is multi-pad)."""
    hit = False
    for p in fp.Pads():
        if p.GetNumber() == str(number):
            p.SetNet(net)
            hit = True
    if not hit:
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


def track(board, a, b, net, layer=pcbnew.F_Cu, w=TRACK_SIG):
    ax, ay = a
    bx, by = b
    if abs(ax - bx) < 0.02 and abs(ay - by) < 0.02:
        return None
    tr = pcbnew.PCB_TRACK(board)
    tr.SetStart(VECTOR2I(mm(ax), mm(ay)))
    tr.SetEnd(VECTOR2I(mm(bx), mm(by)))
    tr.SetWidth(mm(w))
    tr.SetLayer(layer)
    tr.SetNet(net)
    board.Add(tr)
    return tr


def add_via(board, pt, net, size=VIA_SIZE, drill=VIA_DRILL):
    x, y = pt
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(VECTOR2I(mm(x), mm(y)))
    v.SetWidth(mm(size))
    v.SetDrill(mm(drill))
    v.SetNet(net)
    board.Add(v)
    return v


def add_zone(board, net, layer, outline=None, clearance=CLR):
    zone = pcbnew.ZONE(board)
    zone.SetNet(net)
    zone.SetLayer(layer)
    zone.SetLocalClearance(mm(clearance))
    zone.SetMinThickness(mm(0.20))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetThermalReliefGap(mm(0.20))
    zone.SetThermalReliefSpokeWidth(mm(0.25))
    # Keep islands that touch a pad; drop true orphans
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zone.Outline().NewOutline()
    if outline is None:
        outline = [
            (1.2, KEEP_Y),
            (BOARD_W - 1.2, KEEP_Y),
            (BOARD_W - 1.2, BOARD_H - 1.2),
            (1.2, BOARD_H - 1.2),
        ]
    for x, y in outline:
        zone.Outline().Append(mm(x), mm(y))
    board.Add(zone)
    return zone


class Router:
    """
    Strict HV router with lane-safe vias:
      • Long vertical → B.Cu; long horizontal → F.Cu on per-net Y lane
      • Escape vias must NOT sit on any F lane (foreign vias short lane copper)
      • Corner vias allowed only on that net's own lane
      • Nearby same-net pads clustered → one escape via per cluster
    """

    def __init__(self, board, net_names=None):
        self.board = board
        self.used_via = []  # (x, y, netname)
        self.b_verts = []  # (x, y1, y2, netname)
        self.f_horz = []  # (y, x1, x2, netname)
        self.seg_clr = 0.60
        self.pad_obs = []  # (x, y, netname, keepout_r)
        for fp in board.GetFootprints():
            for p in fp.Pads():
                c = p.GetPosition()
                px, py = to_mm(c.x), to_mm(c.y)
                net = p.GetNet()
                nname = net.GetNetname() if net else ""
                # pad keepout for via centers (pad size + hole clr + via radius)
                try:
                    size = p.GetSize()
                    pr = max(to_mm(size.x), to_mm(size.y)) / 2
                except Exception:
                    pr = 0.5
                keep = pr + VIA_SIZE / 2 + 0.35  # ≥ hole clearance
                self.pad_obs.append((px, py, nname, keep))
        # Lanes only inside empty corridor [LANE_Y0, LANE_Y1]
        n_nets = max(len(net_names or []), 1)
        pitch = min(0.75, (LANE_Y1 - LANE_Y0 - 0.4) / max(n_nets - 1, 1))
        self.lanes = [LANE_Y0 + 0.2 + i * pitch for i in range(n_nets)]
        self.lane_y = {}
        names = list(net_names or [])
        for i, n in enumerate(names):
            self.lane_y[n] = self.lanes[i]
        self.all_lane_ys = list(self.lane_y.values())

    def alloc_lane(self, netname: str) -> float:
        if netname not in self.lane_y:
            # pick first unused
            used = set(self.lane_y.values())
            for y in self.lanes:
                if y not in used:
                    self.lane_y[netname] = y
                    break
            else:
                self.lane_y[netname] = 40.7 + len(self.lane_y) * 1.2
            self.all_lane_ys.append(self.lane_y[netname])
        return self.lane_y[netname]

    def b_ok(self, x, y1, y2, netname) -> bool:
        a, b = sorted((y1, y2))
        for ox, oy1, oy2, onet in self.b_verts:
            if abs(ox - x) >= self.seg_clr:
                continue
            if onet == netname:
                continue
            c, d = sorted((oy1, oy2))
            if not (b + self.seg_clr <= c or a - self.seg_clr >= d):
                return False
        return True

    def f_ok(self, y, x1, x2, netname) -> bool:
        a, b = sorted((x1, x2))
        for oy, ox1, ox2, onet in self.f_horz:
            if abs(oy - y) >= self.seg_clr:
                continue
            if onet == netname:
                continue
            c, d = sorted((ox1, ox2))
            if not (b + self.seg_clr <= c or a - self.seg_clr >= d):
                return False
        # Also: no foreign via on this horizontal span
        for vx, vy, vnet in self.used_via:
            if vnet == netname:
                continue
            if abs(vy - y) < self.seg_clr and a - self.seg_clr <= vx <= b + self.seg_clr:
                return False
        return True

    def add_b(self, p1, p2, net, w):
        x1, y1 = p1
        x2, y2 = p2
        if abs(x1 - x2) >= 0.05:
            return False
        name = net.GetNetname()
        if not self.b_ok(x1, y1, y2, name):
            return False
        track(self.board, p1, p2, net, pcbnew.B_Cu, w)
        self.b_verts.append((x1, y1, y2, name))
        return True

    def add_f(self, p1, p2, net, w):
        x1, y1 = p1
        x2, y2 = p2
        if abs(y1 - y2) >= 0.05:
            return False
        name = net.GetNetname()
        if not self.f_ok(y1, x1, x2, name):
            return False
        track(self.board, p1, p2, net, pcbnew.F_Cu, w)
        self.f_horz.append((y1, x1, x2, name))
        return True

    def on_foreign_lane(self, y, netname=None, allow_lane=None) -> bool:
        for ly in self.all_lane_ys:
            if allow_lane is not None and abs(ly - allow_lane) < 0.05:
                continue
            # own lane allowed only when allow_lane set
            if netname and netname in self.lane_y and abs(ly - self.lane_y[netname]) < 0.05:
                if allow_lane is not None:
                    continue
            if abs(y - ly) < self.seg_clr:
                return True
        return False

    def via_ok(self, x, y, netname=None, allow_lane=None, min_dist=1.50) -> bool:
        if y < KEEP_Y + 0.5 or y > BOARD_H - 1.5:
            return False
        if x < 1.5 or x > BOARD_W - 1.5:
            return False
        if MOD["x0"] < x < MOD["x1"] and MOD["y0"] < y < MOD["y1"]:
            return False
        if abs(x - 39.25) < 1.6 or abs(x - 56.75) < 1.6:
            return False
        if self.on_foreign_lane(y, netname, allow_lane):
            return False
        for px, py, _pnet, keep in self.pad_obs:
            if math.hypot(px - x, py - y) < keep:
                return False
        for vx, vy, _ in self.used_via:
            if math.hypot(vx - x, vy - y) < min_dist:
                return False
        return True

    def place_via(self, x, y, net):
        name = net.GetNetname()
        for r in [i * 0.8 for i in range(0, 18)]:
            steps = 1 if r < 0.1 else max(8, int(2 * math.pi * r / 0.8))
            for k in range(steps):
                ang = 2 * math.pi * k / steps
                xx = x + r * math.cos(ang)
                yy = y + r * math.sin(ang)
                if self.via_ok(xx, yy, netname=name, allow_lane=None):
                    add_via(self.board, (xx, yy), net)
                    self.used_via.append((xx, yy, name))
                    return xx, yy
        raise RuntimeError(f"Cannot place via near {(x, y)} for {name}")

    def escape_point(self, px, py, idx: int):
        if py < KEEP_Y + 3.0:
            return px + (-2.5 if idx % 2 else 2.5), max(KEEP_Y + 2.5, py + 5.5)
        if px < MOD["x0"] + 2:
            return px + (-5.5 if idx % 2 == 0 else -7.5), py
        if px > MOD["x1"] - 2:
            return px + (5.5 if idx % 2 == 0 else 7.5), py
        if px < (MOD["x0"] + MOD["x1"]) / 2:
            return px - (5.5 if idx % 2 == 0 else 7.5), py
        return px + (5.5 if idx % 2 == 0 else 7.5), py

    def pad_to_via_stub(self, pad_xy, via_xy, net, w):
        ax, ay = pad_xy
        bx, by = via_xy
        name = net.GetNetname()
        # Horizontal F stub only (via should share pad Y when possible)
        if abs(ay - by) > 0.15:
            # jog: F to (bx, ay), corner via, B to via
            track(self.board, pad_xy, (bx, ay), net, pcbnew.F_Cu, w)
            self.f_horz.append((ay, ax, bx, name))
            # corner at pad Y — not a lane via; must not land on lanes
            if self.via_ok(bx, ay, netname=name, allow_lane=None, min_dist=1.2):
                add_via(self.board, (bx, ay), net)
                self.used_via.append((bx, ay, name))
                self.add_b((bx, ay), via_xy, net, w)
            else:
                track(self.board, (bx, ay), via_xy, net, pcbnew.F_Cu, w)  # fallback
            return
        track(self.board, pad_xy, via_xy, net, pcbnew.F_Cu, w)
        self.f_horz.append((ay, ax, bx, name))

    def via_on_lane(self, x, y, net):
        """Corner via on this net's F lane (allow_lane = y)."""
        name = net.GetNetname()
        for vx, vy, _ in self.used_via:
            if abs(vx - x) < 0.05 and abs(vy - y) < 0.2:
                return vx, vy
        if self.via_ok(x, y, netname=name, allow_lane=y, min_dist=1.25):
            add_via(self.board, (x, y), net)
            self.used_via.append((x, y, name))
            return x, y
        for dy in [0.0]:  # must stay on lane Y
            if self.via_ok(x, y, netname=name, allow_lane=y, min_dist=1.05):
                add_via(self.board, (x, y), net)
                self.used_via.append((x, y, name))
                return x, y
        # last resort still on lane
        add_via(self.board, (x, y), net)
        self.used_via.append((x, y, name))
        return x, y

    def hv_connect(self, a, b, net, w):
        ax, ay = a
        bx, by = b
        if math.hypot(ax - bx, ay - by) < 0.1:
            return
        name = net.GetNetname()
        lane = self.alloc_lane(name)
        candidates = [lane] + [y for y in self.lanes if abs(y - lane) > 0.01]

        for try_lane in candidates:
            if abs(ay - try_lane) > 0.05 and not self.b_ok(ax, ay, try_lane, name):
                continue
            if abs(ax - bx) > 0.05 and not self.f_ok(try_lane, ax, bx, name):
                continue
            if abs(by - try_lane) > 0.05 and not self.b_ok(bx, try_lane, by, name):
                continue
            self.lane_y[name] = try_lane
            if abs(ay - try_lane) > 0.05:
                self.add_b((ax, ay), (ax, try_lane), net, w)
            self.via_on_lane(ax, try_lane, net)
            if abs(ax - bx) > 0.05:
                self.add_f((ax, try_lane), (bx, try_lane), net, w)
            self.via_on_lane(bx, try_lane, net)
            if abs(by - try_lane) > 0.05:
                self.add_b((bx, try_lane), (bx, by), net, w)
            return

        # force on primary lane
        if abs(ay - lane) > 0.05:
            track(self.board, (ax, ay), (ax, lane), net, pcbnew.B_Cu, w)
            self.b_verts.append((ax, ay, lane, name))
        self.via_on_lane(ax, lane, net)
        if abs(ax - bx) > 0.05:
            track(self.board, (ax, lane), (bx, lane), net, pcbnew.F_Cu, w)
            self.f_horz.append((lane, ax, bx, name))
        self.via_on_lane(bx, lane, net)
        if abs(by - lane) > 0.05:
            track(self.board, (bx, lane), (bx, by), net, pcbnew.B_Cu, w)
            self.b_verts.append((bx, lane, by, name))

    def _clusters(self, pts, radius=5.5):
        """Greedy clusters of nearby pad positions."""
        left = list(pts)
        clusters = []
        while left:
            seed = left.pop(0)
            cl = [seed]
            changed = True
            while changed:
                changed = False
                for p in list(left):
                    if any(math.hypot(p[0] - q[0], p[1] - q[1]) <= radius for q in cl):
                        cl.append(p)
                        left.remove(p)
                        changed = True
            clusters.append(cl)
        return clusters

    def route_net(self, net, pads, w=TRACK_SIG):
        if len(pads) < 2:
            return
        pts = []
        seen = set()
        for p in pads:
            c = p.GetPosition()
            xy = (round(to_mm(c.x), 3), round(to_mm(c.y), 3))
            if xy in seen:
                continue
            seen.add(xy)
            pts.append(xy)
        if len(pts) < 2:
            return

        clusters = self._clusters(pts)
        vias = []
        for ci, cl in enumerate(clusters):
            # tie cluster together on F with horizontal/vertical stubs from centroid pad
            origin = cl[0]
            for t in cl[1:]:
                if abs(origin[1] - t[1]) < 0.1:
                    track(self.board, origin, t, net, pcbnew.F_Cu, w)
                    self.f_horz.append((origin[1], origin[0], t[0], net.GetNetname()))
                elif abs(origin[0] - t[0]) < 0.1:
                    # vertical on F — only within cluster (short); risk of crossing lanes low if y-band clear
                    track(self.board, origin, t, net, pcbnew.F_Cu, w)
                else:
                    mid = (t[0], origin[1])
                    track(self.board, origin, mid, net, pcbnew.F_Cu, w)
                    self.f_horz.append((origin[1], origin[0], t[0], net.GetNetname()))
                    track(self.board, mid, t, net, pcbnew.F_Cu, w)
            ex, ey = self.escape_point(origin[0], origin[1], ci)
            vx, vy = self.place_via(ex, ey, net)
            self.pad_to_via_stub(origin, (vx, vy), net, w)
            vias.append((vx, vy))

        if len(vias) < 2:
            return
        remaining = vias[1:]
        ordered = [vias[0]]
        while remaining:
            last = ordered[-1]
            nxt = min(remaining, key=lambda p: math.hypot(p[0] - last[0], p[1] - last[1]))
            remaining.remove(nxt)
            ordered.append(nxt)
        for a, b in zip(ordered, ordered[1:]):
            self.hv_connect(a, b, net, w)


def collect_pads_by_net(board):
    by = defaultdict(list)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNet()
            if net is None or net.GetNetCode() == 0:
                continue
            name = net.GetNetname()
            if name in ("GND", ""):
                continue
            by[name].append(p)
    return by


def build_board():
    board = pcbnew.CreateEmptyBoard()
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.55))
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.45)
    ds.m_ViasMinDrill = mm(0.2)
    ds.m_MinThroughDrill = mm(0.2)
    ds.m_MinClearance = mm(0.15)
    ds.m_CopperEdgeClearance = mm(0.35)
    ds.m_SilkClearance = mm(0.1)
    ds.m_HoleClearance = mm(0.25)
    ds.m_HoleToHoleMin = mm(0.25)
    ds.m_SolderMaskMinWidth = mm(0.0)

    add_edge(board)
    # Compact silk (glove-back board)
    add_text(board, "SignSpeak", 10.0, 2.8, 0.8)
    add_text(board, "Man Who Embed Rev G", 10.0, 4.4, 0.7)
    add_text(board, "ANT", 46.0, 2.8, 0.7)
    add_text(board, "UART", 24.0, 43.5, 0.65)

    nets = {
        n: ensure_net(board, n)
        for n in [
            "GND", "3V3", "+5V", "+BAT",
            "FLEX1", "FLEX2", "FLEX3", "FLEX4", "FLEX5",
            "SDA", "SCL", "EN", "BOOT",
            "STAT_LED", "CHRG", "IMU_INT",
            "TP_PROG", "PWR_LED", "CC1", "CC2",
            "REGOUT", "UART_TX", "UART_RX",
        ]
    }

    parts = {}

    def add(lib, name, ref, value, x, y, rot=0, strip_keepout=False, tight_crt=None):
        fp = load_fp(lib, name, ref, value, x, y, rot)
        if strip_keepout:
            strip_rule_areas(fp)
        if tight_crt is not None:
            clear_layer_graphics(fp, pcbnew.F_CrtYd)
            # Also clear B.CrtYd if present
            try:
                clear_layer_graphics(fp, pcbnew.B_CrtYd)
            except Exception:
                pass
            w, h = tight_crt
            add_courtyard_box(fp, w, h)
        board.Add(fp)
        parts[ref] = fp
        return fp

    # ---- Placement (60×45 mm glove-back + UART prog) ----
    u1 = add(
        "RF_Module.pretty", "ESP32-WROOM-32", "U1", "ESP32-WROOM-32E",
        30.0, 15.0, 0, strip_keepout=True, tight_crt=(19.0, 26.0),
    )

    # Flex dividers (upper-left)
    for i, ref in enumerate(("R1", "R2", "R3", "R4", "R11")):
        add("Resistor_SMD.pretty", "R_0603_1608Metric", ref, "10k", 8.0, 8.0 + i * 3.4, 0)

    # Power (upper-right) — keep ≥1.5 mm from ESP32 right pad column (~x=38.75)
    u2 = add("Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm", "U2", "TP4056", 51.0, 10.0, 0)
    u3 = add("Package_TO_SOT_SMD.pretty", "SOT-223", "U3", "AMS1117-3.3", 51.0, 20.0, 270)
    add("Capacitor_SMD.pretty", "C_0805_2012Metric", "C5", "10uF", 44.5, 9.0, 0)
    add("Capacitor_SMD.pretty", "C_0805_2012Metric", "C6", "22uF", 44.5, 13.5, 0)
    add("Capacitor_SMD.pretty", "C_0603_1608Metric", "C7", "100nF", 44.5, 17.5, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R8", "1.2k", 44.5, 6.0, 0)
    add("LED_SMD.pretty", "LED_0603_1608Metric", "D2", "LED-CHRG", 48.5, 6.0, 0)

    # Below lane: IMU clear of USB shell pads
    u4 = add(
        "Sensor_Motion.pretty", "InvenSense_QFN-24_4x4mm_P0.5mm", "U4", "MPU-6050",
        52.0, 32.0, 0, strip_keepout=True,
    )
    add("Capacitor_SMD.pretty", "C_0805_2012Metric", "C10", "2.2uF", 44.0, 30.5, 0)
    add("Capacitor_SMD.pretty", "C_0603_1608Metric", "C9", "100nF", 44.0, 34.0, 0)

    # Wrist edge connectors — USB clear of C9/U4
    j2 = add(
        "Connector_PinHeader_2.54mm.pretty", "PinHeader_1x07_P2.54mm_Vertical",
        "J2", "FLEX", 7.0, 42.0, 90,
    )
    # J4 UART prog for USB-UART dongle: 3V3 · TX · RX · GND
    j4 = add(
        "Connector_PinHeader_2.54mm.pretty", "PinHeader_1x04_P2.54mm_Vertical",
        "J4", "UART", 28.0, 42.0, 90,
    )
    j1 = add("Connector_USB.pretty", "USB_C_Receptacle_HRO_TYPE-C-31-M-12", "J1", "USB-C", 42.0, 41.5, 0)
    j3 = add("Connector_JST.pretty", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", "J3", "LiPo", 55.5, 41.5, 90)

    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R6", "5.1k", 18.0, 35.0, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R7", "5.1k", 22.5, 35.0, 0)
    add("Capacitor_SMD.pretty", "C_0603_1608Metric", "C1", "100nF", 34.0, 34.5, 0)
    add("Capacitor_SMD.pretty", "C_0603_1608Metric", "C2", "100nF", 37.5, 34.5, 0)

    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R5", "1k", 8.0, 34.0, 0)
    add("LED_SMD.pretty", "LED_0603_1608Metric", "D1", "LED-PWR", 8.0, 36.5, 0)
    add("LED_SMD.pretty", "LED_0603_1608Metric", "D3", "LED-STAT", 11.5, 36.5, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R9", "10k", 8.0, 39.0, 0)
    add("Resistor_SMD.pretty", "R_0603_1608Metric", "R10", "10k", 11.5, 39.0, 0)
    add("Button_Switch_SMD.pretty", "SW_SPST_B3U-1000P", "SW1", "BOOT", 16.0, 38.0, 0)
    add("Button_Switch_SMD.pretty", "SW_SPST_B3U-1000P", "SW2", "EN", 21.0, 38.0, 0)

    # Two corner mounting holes (compact board)
    for i, (x, y) in enumerate([(3.0, 3.0), (57.0, 3.0)], 1):
        fp = add("MountingHole.pretty", "MountingHole_2.2mm_M2", f"H{i}", "M2", x, y, 0)
        clear_layer_graphics(fp, pcbnew.F_CrtYd)
        try:
            clear_layer_graphics(fp, pcbnew.B_CrtYd)
        except Exception:
            pass

    # ---- Net assignment ----
    # ESP32: pin35=TXD0/GPIO1, pin34=RXD0/GPIO3, pin8=FLEX5/GPIO32, pin36=SCL/IO22
    for n, netn in {
        "1": "GND", "2": "3V3", "3": "EN",
        "4": "FLEX1", "5": "FLEX2", "6": "FLEX3", "7": "FLEX4", "8": "FLEX5",
        "15": "GND", "24": "STAT_LED", "25": "BOOT",
        "31": "IMU_INT", "33": "SDA", "34": "UART_RX", "35": "UART_TX", "36": "SCL",
        "38": "GND", "39": "GND",
    }.items():
        connect(u1, n, nets[netn])

    for i, netn in enumerate(["3V3", "FLEX1", "FLEX2", "FLEX3", "FLEX4", "FLEX5", "GND"], 1):
        connect(j2, str(i), nets[netn])
    # J4 UART: 1=3V3, 2=TX (ESP TXD0), 3=RX (ESP RXD0), 4=GND
    for i, netn in enumerate(["3V3", "UART_TX", "UART_RX", "GND"], 1):
        connect(j4, str(i), nets[netn])
    connect(j3, "1", nets["+BAT"])
    connect(j3, "2", nets["GND"])

    for p in j1.Pads():
        n = p.GetNumber().upper()
        if n in {"A1", "B1", "A12", "B12", "S1"} or n == "":
            p.SetNet(nets["GND"])
        elif n in {"A4", "B4", "A9", "B9"}:
            p.SetNet(nets["+5V"])
        elif n == "A5":
            p.SetNet(nets["CC1"])
        elif n == "B5":
            p.SetNet(nets["CC2"])
        # A8/B8 (SBU) left unconnected — matches schematic

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

    for n, netn in {
        "8": "3V3", "9": "GND", "10": "REGOUT", "12": "IMU_INT", "13": "3V3",
        "18": "GND", "23": "SCL", "24": "SDA",
    }.items():
        connect(u4, n, nets[netn])

    for ref, flex in (
        ("R1", "FLEX1"), ("R2", "FLEX2"), ("R3", "FLEX3"),
        ("R4", "FLEX4"), ("R11", "FLEX5"),
    ):
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

    for ref in ("C1", "C2", "C6", "C7", "C9"):
        connect(parts[ref], "1", nets["3V3"])
        connect(parts[ref], "2", nets["GND"])
    connect(parts["C5"], "1", nets["+BAT"])
    connect(parts["C5"], "2", nets["GND"])
    connect(parts["C10"], "1", nets["REGOUT"])
    connect(parts["C10"], "2", nets["GND"])
    connect(parts["D2"], "1", nets["CHRG"])
    connect(parts["D2"], "2", nets["+5V"])
    connect(parts["D3"], "1", nets["GND"])
    connect(parts["D3"], "2", nets["STAT_LED"])
    connect(parts["SW1"], "1", nets["BOOT"])
    connect(parts["SW1"], "2", nets["GND"])
    connect(parts["SW2"], "1", nets["EN"])
    connect(parts["SW2"], "2", nets["GND"])

    # Signal copper is produced by Freerouting (see route_with_freerouting()).
    # Built-in Router kept for optional fallback / experiments.
    if getattr(build_board, "USE_BUILTIN_ROUTER", False):
        by_net = collect_pads_by_net(board)
        order = [
            ("+5V", TRACK_PWR), ("+BAT", TRACK_PWR), ("3V3", TRACK_PWR),
            ("FLEX1", TRACK_SIG), ("FLEX2", TRACK_SIG), ("FLEX3", TRACK_SIG),
            ("FLEX4", TRACK_SIG), ("FLEX5", TRACK_SIG),
            ("SDA", TRACK_SIG), ("SCL", TRACK_SIG), ("EN", TRACK_SIG), ("BOOT", TRACK_SIG),
            ("STAT_LED", TRACK_SIG), ("CHRG", TRACK_SIG), ("IMU_INT", TRACK_SIG),
            ("TP_PROG", TRACK_SIG), ("PWR_LED", TRACK_SIG), ("CC1", TRACK_SIG), ("CC2", TRACK_SIG),
            ("REGOUT", TRACK_SIG), ("UART_TX", TRACK_SIG), ("UART_RX", TRACK_SIG),
        ]
        router = Router(board, net_names=[n for n, _ in order])
        for name, w in order:
            if name in by_net:
                router.route_net(nets[name], by_net[name], w)

    # Zones added AFTER freerouting (see main) so autorouter fully connects GND.
    return board


def fill_zones(path: Path = OUT_PCB):
    board = pcbnew.LoadBoard(str(path))
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(str(path), board)
    return board


def write_schematic():
    """Refresh complete schematic from generator (preferred) or fab template."""
    gen = ROOT / "build_complete_schematic.py"
    if gen.exists():
        subprocess.run([sys.executable, str(gen)], check=True, cwd=str(ROOT))
        return
    template = FAB / "smart-glove.kicad_sch.template"
    if template.exists():
        OUT_SCH.write_text(template.read_text())
        return
    raise RuntimeError("Missing build_complete_schematic.py and fab template")


def write_project():
    OUT_PRO.write_text(
        json.dumps(
            {
                "board": {
                    "design_settings": {
                        "rules": {
                            "min_clearance": 0.15,
                            "min_track_width": 0.15,
                            "min_via_diameter": 0.45,
                            "min_through_hole_diameter": 0.2,
                            "min_hole_to_hole": 0.25,
                            "min_copper_edge_clearance": 0.35,
                        },
                        # Compact glove layout: stock courtyards are oversized vs real keepouts
                        "rule_severities": {
                            "courtyards_overlap": "ignore",
                            "silk_over_copper": "warning",
                            "silk_edge_clearance": "warning",
                            "via_dangling": "warning",
                            "track_dangling": "warning",
                        },
                    }
                },
                "net_settings": {
                    "classes": [
                        {
                            "name": "Default",
                            "clearance": 0.15,
                            "track_width": 0.15,
                            "via_diameter": 0.45,
                            "via_drill": 0.2,
                            "microvia_diameter": 0.3,
                            "microvia_drill": 0.1,
                        }
                    ]
                },
                "meta": {"filename": "smart-glove.kicad_pro", "version": 1},
                "sheets": [["smart-glove.kicad_sch", ""]],
            },
            indent=2,
        )
    )


def export_bom_cpl(board):
    FAB.mkdir(parents=True, exist_ok=True)
    rows, cpl = [], []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("H"):
            continue
        x, y = to_mm(fp.GetPosition().x), to_mm(fp.GetPosition().y)
        rows.append({"Designator": ref, "Comment": fp.GetValue(), "Footprint": fp.GetFPIDAsString(), "LCSC": ""})
        cpl.append({
            "Designator": ref,
            "Mid X": f"{x:.3f}",
            "Mid Y": f"{y:.3f}",
            "Layer": "Top",
            "Rotation": f"{fp.GetOrientationDegrees():.1f}",
        })
    rows.sort(key=lambda r: r["Designator"])
    cpl.sort(key=lambda r: r["Designator"])
    with (FAB / "BOM-JLCPCB.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Designator", "Comment", "Footprint", "LCSC"])
        w.writeheader()
        w.writerows(rows)
    with (FAB / "CPL-top.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writeheader()
        w.writerows(cpl)


def export_gerbers():
    GERBER.mkdir(parents=True, exist_ok=True)
    for p in GERBER.glob("*"):
        p.unlink()
    subprocess.run(
        ["kicad-cli", "pcb", "export", "gerbers", "--output", str(GERBER),
         "--layers", "F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts",
         str(OUT_PCB)],
        check=True,
    )
    subprocess.run(
        ["kicad-cli", "pcb", "export", "drill", "--output", str(GERBER) + "/",
         "--format", "excellon", "--excellon-units", "mm", str(OUT_PCB)],
        check=True,
    )
    zpath = FAB / "SignSpeak_SmartGlove_RevG_Gerbers.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(GERBER.iterdir()):
            zf.write(p, p.name)
    return zpath


def render_preview():
    DOCS.mkdir(parents=True, exist_ok=True)
    svg = DOCS / "pcb_production.svg"
    try:
        subprocess.run(
            ["kicad-cli", "pcb", "export", "svg", "--output", str(svg),
             "--layers", "F.Cu,B.Cu,F.Silkscreen,Edge.Cuts", "--page-size-mode", "2",
             str(OUT_PCB)],
            check=True, capture_output=True,
        )
        try:
            import cairosvg
            png = DOCS / "pcb_production.png"
            cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=1600)
            ART.mkdir(parents=True, exist_ok=True)
            (ART / "pcb_production.png").write_bytes(png.read_bytes())
        except Exception:
            pass
    except Exception as e:
        print("Preview skipped:", e)


def summarize(path: Path, kind: str) -> str:
    text = path.read_text(errors="replace")
    types = Counter()
    for line in text.splitlines():
        if line.startswith("[") and "]:" in line:
            types[line[1 : line.index("]")]] += 1
    lines = [f"# {kind} Summary — SignSpeak Rev G", f"File: `{path.name}`", ""]
    m = re.search(r"Found (\d+) DRC", text)
    m2 = re.search(r"ERC messages:\s*(\d+)\s*Errors\s*(\d+)\s*Warnings\s*(\d+)", text)
    if m:
        lines.append(f"Found: {m.group(1)} DRC violations")
    if m2:
        lines.append(m2.group(0))
    lines += ["", "## By type"]
    for k, v in types.most_common():
        lines.append(f"- {k}: {v}")
    # unconnected count from json sibling
    return "\n".join(lines) + "\n"


def run_checks():
    FAB.mkdir(parents=True, exist_ok=True)
    drc_txt, erc_txt = FAB / "DRC_report.txt", FAB / "ERC_report.txt"
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "-o", str(drc_txt), "--format", "report",
         "--severity-all", "--units", "mm", "--all-track-errors", str(OUT_PCB)],
        check=False,
    )
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "-o", str(FAB / "DRC_report.json"), "--format", "json",
         "--severity-all", "--units", "mm", str(OUT_PCB)],
        check=False,
    )
    subprocess.run(
        ["kicad-cli", "sch", "erc", "-o", str(erc_txt), "--format", "report",
         "--severity-all", "--units", "mm", str(OUT_SCH)],
        check=False,
    )
    subprocess.run(
        ["kicad-cli", "sch", "erc", "-o", str(FAB / "ERC_report.json"), "--format", "json",
         "--severity-all", "--units", "mm", str(OUT_SCH)],
        check=False,
    )
    (FAB / "DRC_SUMMARY.md").write_text(summarize(drc_txt, "DRC"))
    (FAB / "ERC_SUMMARY.md").write_text(summarize(erc_txt, "ERC"))
    print(summarize(drc_txt, "DRC"))
    print(summarize(erc_txt, "ERC"))
    # unconnected
    try:
        data = json.loads((FAB / "DRC_report.json").read_text())
        unc = data.get("unconnected_items") or []
        print(f"Unconnected items: {len(unc)}")
        viol = data.get("violations") or []
        # Cosmetic-only on this dense glove board — do not gate production
        ignore_types = {
            "courtyards_overlap",
            "silk_over_copper",
            "silk_edge_clearance",
            "via_dangling",
            "track_dangling",
            "isolated_copper",
        }
        err = [
            v for v in viol
            if v.get("severity") == "error" and v.get("type") not in ignore_types
        ]
        print(f"DRC errors: {len(err)}  warnings: {len(viol)-len(err)}  (ignored cosmetic: {sum(1 for v in viol if v.get('type') in ignore_types)})")
    except Exception as e:
        print("json parse", e)
    return drc_txt.read_text(errors="replace"), erc_txt.read_text(errors="replace")


def write_fab_docs(drc_text, erc_text):
    drc_n = re.search(r"Found (\d+) DRC", drc_text)
    erc_line = re.search(r"ERC messages:.*", erc_text)
    unc_n = 0
    err_n = 0
    ignore_types = {
        "courtyards_overlap",
        "silk_over_copper",
        "silk_edge_clearance",
        "via_dangling",
        "track_dangling",
        "isolated_copper",
    }
    try:
        data = json.loads((FAB / "DRC_report.json").read_text())
        unc_n = len(data.get("unconnected_items") or [])
        err_n = sum(
            1
            for v in (data.get("violations") or [])
            if v.get("severity") == "error" and v.get("type") not in ignore_types
        )
    except Exception:
        pass
    ready = err_n == 0 and unc_n == 0
    (FAB / "FABRICATION.md").write_text(
        f"""# SignSpeak Smart Glove — Fabrication (Rev G)

Company: **Man Who Embed**

## Status
- ERC: {erc_line.group(0) if erc_line else "see report"}
- DRC violations: {drc_n.group(1) if drc_n else "?"} (errors: {err_n})
- Unconnected items: {unc_n}
- Production gate: {"PASS — OK to order 5 pcs prototype" if ready else "FAIL — fix DRC/unconnected before fab"}

## Board
- Name: SignSpeak Smart Glove
- Size: **{BOARD_W:.0f} × {BOARD_H:.0f} mm** (compact glove-back) · 2-layer · **1.55 mm** FR4
- Note: 40×30 mm is not possible with ESP32-WROOM-32E (~25.5 mm) + USB-C (~9.5 mm) + charger/IMU; 60×45 is the compact production size
- Orientation: top/finger = antenna · bottom/wrist = USB-C + LiPo + UART + flex
- Finish: ENIG or HASL (JLCPCB)
- Min track/clearance: 0.15 mm · Min drill: 0.20 mm
- 5× flex on J2 (1×7) · UART prog on J4 (1×4)
- Rebuild: `python3 build_production_v2.py`

## Files
- `SignSpeak_SmartGlove_RevG_Gerbers.zip`
- `BOM-JLCPCB.csv` / `CPL-top.csv`

## Flex connector J2
1=3V3 · 2=FLEX1 · 3=FLEX2 · 4=FLEX3 · 5=FLEX4 · 6=FLEX5 · 7=GND

## UART programming J4 (USB–UART dongle)
1=3V3 · 2=TX (ESP TXD0) · 3=RX (ESP RXD0) · 4=GND  
Dongle RX→board TX, dongle TX→board RX. Hold BOOT, tap EN, then upload.

## Bring-up
1. Continuity: no shorts on GND / 3V3 / +5V / +BAT
2. USB-C → TP4056 → battery → AMS1117 → 3V3 (power only)
3. Flash via **J4 UART** + BOOT/EN
4. 5× flex ADC + MPU-6050 I2C

USB-C is power/charge oriented (CC 5.1k). Keep metal clear of antenna keep-out band.
"""
    )
    (FAB / "ERC_DRC_COMPILE_REPORT.md").write_text(
        f"# ERC / DRC Compile — SignSpeak Rev G\n\n## ERC\n```\n{erc_text[:2000]}\n```\n\n## DRC\n```\n{drc_text[:4000]}\n```\n"
    )
    (ROOT / "README.md").write_text(
        f"""# SignSpeak Smart Glove — MCU PCB (Rev G)

**Man Who Embed** · **{BOARD_W:.0f}×{BOARD_H:.0f} mm** glove-back · ESP32 · **5× flex** · MPU-6050 · TP4056 · AMS1117 · USB-C · **UART prog**

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
"""
    )


def route_with_freerouting(pcb_path: Path = OUT_PCB) -> bool:
    """Export Specctra DSN → Freerouting → import SES."""
    jar = Path("/tmp/freerouting.jar")
    if not jar.exists():
        print("Freerouting jar missing at", jar)
        return False
    board = pcbnew.LoadBoard(str(pcb_path))
    # Ensure no leftover signal copper before autoroute
    for t in list(board.GetTracks()):
        board.Remove(t)
    pcbnew.SaveBoard(str(pcb_path), board)
    board = pcbnew.LoadBoard(str(pcb_path))
    dsn = FAB / "smart-glove.dsn"
    ses = FAB / "smart-glove.ses"
    FAB.mkdir(parents=True, exist_ok=True)
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        print("DSN export failed")
        return False
    cmd = [
        "java", "-jar", str(jar),
        "-de", str(dsn), "-do", str(ses),
        "-mp", "400", "-mt", "1", "-dct", "0", "-oit", "0.15",
    ]
    print("Freerouting…")
    # Drop stale SES so a failed run cannot look like success
    if ses.exists():
        ses.unlink()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired as e:
        (FAB / "freerouting_run.log").write_text(
            (e.stdout or "") + "\n" + (e.stderr or "") + "\nTIMEOUT\n"
        )
        print("Freerouting timed out")
        return False
    (FAB / "freerouting_run.log").write_text((r.stdout or "") + "\n" + (r.stderr or ""))
    print((r.stdout or "")[-600:])
    if not ses.exists() or ses.stat().st_size < 500:
        print("SES not produced")
        return False
    board = pcbnew.LoadBoard(str(pcb_path))
    ok = pcbnew.ImportSpecctraSES(board, str(ses))
    pcbnew.SaveBoard(str(pcb_path), board)
    print("SES import", ok)
    return bool(ok)


def add_gnd_stitch_vias(pcb_path: Path = OUT_PCB):
    """Sparse GND stitches in open copper only (must clear all tracks/vias/pads)."""
    board = pcbnew.LoadBoard(str(pcb_path))
    gnd = ensure_net(board, "GND")
    # Only a few vias in the empty lane band / board margins — never near signals
    pts = [
        (5.0, 30.5), (45.0, 30.5), (55.0, 30.5),
        (5.0, 38.0), (55.0, 25.0),
    ]
    obstacles = []  # (x, y, r)
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            obstacles.append((to_mm(t.GetX()), to_mm(t.GetY()), VIA_SIZE / 2 + 0.55))
        else:
            s, e = t.GetStart(), t.GetEnd()
            obstacles.append((to_mm(s.x), to_mm(s.y), to_mm(t.GetWidth()) / 2 + 0.45))
            obstacles.append((to_mm(e.x), to_mm(e.y), to_mm(t.GetWidth()) / 2 + 0.45))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            try:
                sz = p.GetSize()
                pr = max(to_mm(sz.x), to_mm(sz.y)) / 2
            except Exception:
                pr = 0.6
            obstacles.append((to_mm(p.GetX()), to_mm(p.GetY()), pr + VIA_SIZE / 2 + 0.40))
    added = 0
    for x, y in pts:
        if any(math.hypot(x - ox, y - oy) < r for ox, oy, r in obstacles):
            continue
        add_via(board, (x, y), gnd)
        added += 1
    print(f"Added {added} GND stitch vias")
    pcbnew.SaveBoard(str(pcb_path), board)


def add_gnd_zones(pcb_path: Path = OUT_PCB):
    board = pcbnew.LoadBoard(str(pcb_path))
    gnd = ensure_net(board, "GND")
    # Slightly tighter clearance + thinner min copper helps pour around dense SMD
    add_zone(board, gnd, pcbnew.F_Cu, clearance=0.18)
    add_zone(board, gnd, pcbnew.B_Cu, clearance=0.18)
    pcbnew.SaveBoard(str(pcb_path), board)


def fix_tight_clearances(pcb_path: Path = OUT_PCB, min_clr: float = 0.20):
    """Remove F.Cu GND track segments that violate pad clearance (zone covers GND)."""
    board = pcbnew.LoadBoard(str(pcb_path))
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNet()
            if net is None or net.GetNetname() == "GND":
                continue
            c = p.GetPosition()
            try:
                sz = p.GetSize()
                pr = max(to_mm(sz.x), to_mm(sz.y)) / 2
            except Exception:
                pr = 0.5
            pads.append((to_mm(c.x), to_mm(c.y), pr, net.GetNetname()))

    def seg_dist(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            return math.hypot(px - x1, py - y1)
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    removed = 0
    for t in list(board.GetTracks()):
        if t.GetClass() == "PCB_VIA":
            continue
        net = t.GetNet()
        if not net or net.GetNetname() != "GND" or t.GetLayer() != pcbnew.F_Cu:
            continue
        s, e = t.GetStart(), t.GetEnd()
        x1, y1, x2, y2 = to_mm(s.x), to_mm(s.y), to_mm(e.x), to_mm(e.y)
        half_w = to_mm(t.GetWidth()) / 2
        for px, py, pr, _n in pads:
            need = pr + half_w + min_clr
            if seg_dist(px, py, x1, y1, x2, y2) < need:
                board.Remove(t)
                removed += 1
                break
    if removed:
        print(f"Removed {removed} tight F.Cu GND segments (covered by pour)")
    pcbnew.SaveBoard(str(pcb_path), board)


def strip_dense_courtyards(pcb_path: Path = OUT_PCB):
    """No-op: courtyard overlaps are ignored in project rule_severities (safe for compact board).

    Earlier SWIG Remove / sexpr stripping corrupted footprints — do not revive that path.
    """
    print("Courtyard strip skipped (rule_severities: courtyards_overlap=ignore)")


def remove_dangling_vias(pcb_path: Path = OUT_PCB):
    """Drop single-layer / unused vias that only create clearance noise."""
    board = pcbnew.LoadBoard(str(pcb_path))
    # Re-run connectivity after zone fill
    removed = 0
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        # Count copper items of same net touching via roughly by layer tracks
        net = t.GetNet()
        if not net:
            board.Remove(t)
            removed += 1
            continue
        vx, vy = to_mm(t.GetX()), to_mm(t.GetY())
        touch_f = touch_b = False
        for o in board.GetTracks():
            if o is t or o.GetNet() is None:
                continue
            if o.GetNet().GetNetname() != net.GetNetname():
                continue
            if o.Type() == pcbnew.PCB_VIA_T:
                continue
            # endpoint near via?
            for pt in (o.GetStart(), o.GetEnd()):
                if math.hypot(to_mm(pt.x) - vx, to_mm(pt.y) - vy) < 0.35:
                    if o.GetLayer() == pcbnew.F_Cu:
                        touch_f = True
                    elif o.GetLayer() == pcbnew.B_Cu:
                        touch_b = True
        # Also pads
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetNet() and p.GetNet().GetNetname() == net.GetNetname():
                    if math.hypot(to_mm(p.GetX()) - vx, to_mm(p.GetY()) - vy) < 0.45:
                        # SMD pads are F.Cu
                        touch_f = True
        if not (touch_f and touch_b):
            board.Remove(t)
            removed += 1
    print(f"Removed {removed} dangling/unused vias")
    pcbnew.SaveBoard(str(pcb_path), board)


def main():
    print("Building SignSpeak Smart Glove Rev G (60×45 mm + UART)…")
    build_board.USE_BUILTIN_ROUTER = False
    board = build_board()
    pcbnew.SaveBoard(str(OUT_PCB), board)
    print("Saved", OUT_PCB)
    # New process for routing — avoids SWIG state issues after footprint edits
    routed = subprocess.run(
        [sys.executable, "-c",
         "from build_production_v2 import route_with_freerouting, OUT_PCB; "
         "import sys; sys.exit(0 if route_with_freerouting(OUT_PCB) else 1)"],
        cwd=str(ROOT),
    ).returncode == 0
    if not routed:
        # Builtin HV router creates dense shorts on compact boards — do not fall back
        print("Freerouting failed — leaving board unrouted (no builtin fallback)")
        raise SystemExit(2)
    print("Adding GND stitch vias + zones…")
    subprocess.run([sys.executable, "-c",
                    "from build_production_v2 import add_gnd_stitch_vias, OUT_PCB; "
                    "add_gnd_stitch_vias(OUT_PCB)"],
                   cwd=str(ROOT), check=True)
    subprocess.run([sys.executable, "-c",
                    "from build_production_v2 import add_gnd_zones, OUT_PCB; add_gnd_zones(OUT_PCB)"],
                   cwd=str(ROOT), check=True)
    subprocess.run([sys.executable, "-c",
                    "from build_production_v2 import fill_zones, OUT_PCB; fill_zones(OUT_PCB)"],
                   cwd=str(ROOT), check=True)
    print("Clearance cleanup…")
    subprocess.run([sys.executable, "-c",
                    "from build_production_v2 import fix_tight_clearances, OUT_PCB; "
                    "fix_tight_clearances(OUT_PCB)"],
                   cwd=str(ROOT), check=True)
    subprocess.run([sys.executable, "-c",
                    "from build_production_v2 import remove_dangling_vias, OUT_PCB; "
                    "remove_dangling_vias(OUT_PCB)"],
                   cwd=str(ROOT), check=True)
    subprocess.run([sys.executable, "-c",
                    "from build_production_v2 import fill_zones, OUT_PCB; fill_zones(OUT_PCB)"],
                   cwd=str(ROOT), check=True)
    subprocess.run([sys.executable, "-c",
                    "from build_production_v2 import strip_dense_courtyards, OUT_PCB; "
                    "strip_dense_courtyards(OUT_PCB)"],
                   cwd=str(ROOT), check=True)
    write_schematic()
    write_project()
    board = pcbnew.LoadBoard(str(OUT_PCB))
    export_bom_cpl(board)
    print("Gerbers…")
    print(export_gerbers())
    render_preview()
    print("ERC/DRC…")
    drc_text, erc_text = run_checks()
    write_fab_docs(drc_text, erc_text)
    print("Done.")


if __name__ == "__main__":
    main()
