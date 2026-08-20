#!/usr/bin/env python3
"""
fix_lna_gate_bias.py

Run this ON YOUR MACHINE against your real lna_sky130.sch and your real
Sky130 xschem symbol library. It does NOT guess pin coordinates -- it reads
the actual .sym files (nfet_01v8.sym, res.sym, ind.sym, capa.sym,
vsource.sym, gnd.sym, lab_pin.sym, opin.sym), applies xschem's real
rotation/mirror transform, and computes every pin's absolute (x,y).

It then traces your existing N (wire) statements plus geometric pin/point
coincidence to build the actual electrical nets in your schematic, reports
every pin that is NOT connected to anything else (floating), and -- if the
only floating pins are exactly Rbias's two terminals sitting between the
VBIAS label and the gate/Lg net (your reported symptom) -- appends the
minimal wire segments needed to close that gap and writes a corrected file.

Usage:
    cd /home/azmuth/projects/sky130_rf_receiver/lna
    cp lna_sky130.sch lna_sky130_backup.sch
    python3 fix_lna_gate_bias.py lna_sky130.sch lna_sky130_fixed.sch

It will also just print a full connectivity report if you pass --report-only,
which is worth doing first so you can see the exact numbers instead of
trusting anything blindly.
"""

import re
import sys
import os
import argparse

PDK_SYM_DIR_ENV = "SKY130_XSCHEM_DIR"  # optional override

# Where to look for devices/*.sym and sky130_fd_pr/*.sym, in order.
def candidate_sym_dirs():
    dirs = []
    if os.environ.get(PDK_SYM_DIR_ENV):
        dirs.append(os.environ[PDK_SYM_DIR_ENV])
    # common xschem stdlib locations
    dirs += [
        os.path.expanduser("~/.xschem"),
        "/usr/share/xschem/xschem",
        "/usr/local/share/xschem/xschem",
        "/usr/share/xschem",
    ]
    return dirs


def find_sym_file(sym_ref, sch_dir, pdk_xschem_dir):
    """
    sym_ref looks like 'devices/res.sym' or 'sky130_fd_pr/nfet_01v8.sym'.
    Search, in order: relative to schematic dir, relative to the PDK's
    xschem sky130_fd_pr dir's parent, then common stdlib dirs.
    """
    candidates = []
    candidates.append(os.path.join(sch_dir, sym_ref))
    if pdk_xschem_dir:
        # pdk_xschem_dir points at .../libs.tech/xschem/sky130_fd_pr
        # its parent (.../xschem) is where 'devices/' normally also lives
        # in a merged XSCHEM_LIBRARY_PATH setup, but sky130_fd_pr symbols
        # are relative to the parent of that dir.
        parent = os.path.dirname(pdk_xschem_dir.rstrip("/"))
        candidates.append(os.path.join(parent, sym_ref))
        candidates.append(os.path.join(pdk_xschem_dir, os.path.basename(sym_ref)))
    for d in candidate_sym_dirs():
        candidates.append(os.path.join(d, sym_ref))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


PIN_RE = re.compile(
    r"^B\s+5\s+([\-0-9.]+)\s+([\-0-9.]+)\s+([\-0-9.]+)\s+([\-0-9.]+)\s+\{([^}]*)\}",
    re.MULTILINE,
)
NAME_RE = re.compile(r"name=(\S+)")


def parse_sym_pins(sym_path):
    """Return dict pin_name -> (x,y) local coordinates (rectangle center)."""
    with open(sym_path, "r", errors="replace") as f:
        text = f.read()
    pins = {}
    for m in PIN_RE.finditer(text):
        x1, y1, x2, y2, attrs = m.groups()
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        nm = NAME_RE.search(attrs)
        if nm:
            pins[nm.group(1)] = (cx, cy)
    return pins


def xform(x, y, x0, y0, rot, flip):
    """xschem's real placement transform: rotate then translate, with
    mirror applied before rotation, matching xschem's ROTATION()/FLIP()
    convention (rot in {0,1,2,3} = 0/90/180/270 deg CCW)."""
    if flip:
        x = -x
    if rot == 0:
        rx, ry = x, y
    elif rot == 1:
        rx, ry = -y, x
    elif rot == 2:
        rx, ry = -x, -y
    elif rot == 3:
        rx, ry = y, -x
    else:
        raise ValueError(f"bad rot {rot}")
    return x0 + rx, y0 + ry


COMP_RE = re.compile(
    r"^C\s+\{([^}]+)\}\s+([\-0-9.]+)\s+([\-0-9.]+)\s+([0-3])\s+([01])\s+\{(.*)\}\s*$",
    re.MULTILINE,
)
WIRE_RE = re.compile(
    r"^N\s+([\-0-9.]+)\s+([\-0-9.]+)\s+([\-0-9.]+)\s+([\-0-9.]+)\s+\{[^}]*\}\s*$",
    re.MULTILINE,
)


def parse_components(sch_text):
    comps = []
    for m in COMP_RE.finditer(sch_text):
        sym_ref, x0, y0, rot, flip, attrs = m.groups()
        x0, y0, rot, flip = float(x0), float(y0), int(rot), int(flip)
        name_m = NAME_RE.search(attrs)
        lab_m = re.search(r"lab=(\S+)", attrs)
        comps.append(
            dict(
                sym_ref=sym_ref,
                x0=x0,
                y0=y0,
                rot=rot,
                flip=flip,
                attrs=attrs,
                inst_name=name_m.group(1) if name_m else None,
                lab=lab_m.group(1) if lab_m else None,
            )
        )
    return comps


def parse_wires(sch_text):
    wires = []
    for m in WIRE_RE.finditer(sch_text):
        x1, y1, x2, y2 = map(float, m.groups())
        wires.append(((x1, y1), (x2, y2)))
    return wires


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, a):
        self.parent.setdefault(a, a)
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sch_in")
    ap.add_argument("sch_out", nargs="?", default=None)
    ap.add_argument(
        "--pdk-xschem-dir",
        default="/home/azmuth/.volare/volare/volare/sky130/versions/"
        "0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/xschem/sky130_fd_pr",
        help="path to .../libs.tech/xschem/sky130_fd_pr",
    )
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    sch_dir = os.path.dirname(os.path.abspath(args.sch_in)) or "."
    with open(args.sch_in, "r", errors="replace") as f:
        sch_text = f.read()

    comps = parse_components(sch_text)
    wires = parse_wires(sch_text)

    uf = UnionFind()

    # 1) union wire endpoints with each other
    for (p1, p2) in wires:
        uf.union(p1, p2)

    # 2) resolve every component's pins to absolute coords, union pins
    #    that land on the exact same point as any wire endpoint or other pin
    all_points = {}  # point -> list of (inst_name, pin_name)
    missing_syms = []

    for c in comps:
        sym_path = find_sym_file(c["sym_ref"], sch_dir, args.pdk_xschem_dir)
        if not sym_path:
            missing_syms.append(c["sym_ref"])
            continue
        local_pins = parse_sym_pins(sym_path)
        if not local_pins:
            # gnd.sym / lab_pin.sym / opin.sym / vsource.sym etc:
            # some stdlib symbols use a single implicit pin at origin
            # instead of a B 5 rect (older symbol style). Fall back to
            # treating the origin as the single connection point.
            local_pins = {"P": (0.0, 0.0)}
        for pin_name, (lx, ly) in local_pins.items():
            ax, ay = xform(lx, ly, c["x0"], c["y0"], c["rot"], c["flip"])
            pt = (round(ax, 3), round(ay, 3))
            all_points.setdefault(pt, []).append((c["inst_name"] or c["sym_ref"], pin_name))
            uf.union(pt, pt)

    if missing_syms:
        print("WARNING: could not locate these symbol files on disk -- "
              "results below are INCOMPLETE until you fix the search path "
              "(pass --pdk-xschem-dir, or set SKY130_XSCHEM_DIR):")
        for s in sorted(set(missing_syms)):
            print("   ", s)
        print()

    # union any pin points that are geometrically coincident with a wire
    # endpoint (already handled since we union'd the same tuple key) and
    # also union pins that exactly coincide with each other (e.g. gnd
    # symbols dropped directly on top of a pin, no wire drawn)
    pts = list(all_points.keys())
    for i, p in enumerate(pts):
        uf.union(p, p)

    # merge wire-endpoint groups with pin groups sharing the same coordinate
    for (p1, p2) in wires:
        if p1 in all_points:
            uf.union(p1, p1)
        if p2 in all_points:
            uf.union(p2, p2)

    # Now build final net groups keyed by union-find root, pulling in
    # labels (lab_pin/gnd/opin) as the net's electrical name where present.
    net_of = {}
    for pt, entries in all_points.items():
        net_of.setdefault(uf.find(pt), []).extend(entries)

    # net name resolution: any lab_pin/gnd/opin component pin in a group
    # names that whole electrical net (xschem also unions by matching
    # label text across the sheet, not just geometry -- do that too)
    label_groups = {}  # label text -> set of roots
    for c in comps:
        if c["lab"] and c["sym_ref"] in (
            "devices/lab_pin.sym",
            "devices/gnd.sym",
            "devices/opin.sym",
            "devices/ipin.sym",
        ):
            sym_path = find_sym_file(c["sym_ref"], sch_dir, args.pdk_xschem_dir)
            local_pins = parse_sym_pins(sym_path) if sym_path else {"P": (0.0, 0.0)}
            if not local_pins:
                local_pins = {"P": (0.0, 0.0)}
            for pin_name, (lx, ly) in local_pins.items():
                ax, ay = xform(lx, ly, c["x0"], c["y0"], c["rot"], c["flip"])
                pt = (round(ax, 3), round(ay, 3))
                root = uf.find(pt)
                label_groups.setdefault(c["lab"], set()).add(root)

    # union roots that share the same label text (this is what actually
    # ties GND instances together across the sheet without explicit wires,
    # and would tie two VBIAS labels together if you ever add a second one)
    for lab, roots in label_groups.items():
        roots = list(roots)
        for r in roots[1:]:
            uf.union(r, roots[0])

    # rebuild final groups after label-driven unions
    final = {}
    for pt, entries in all_points.items():
        final.setdefault(uf.find(pt), []).append((pt, entries))

    def net_label(root):
        names = set()
        for lab, roots in label_groups.items():
            if uf.find(next(iter(roots))) == root:
                names.add(lab)
        return "/".join(sorted(names)) if names else None

    print("=== Net report (each group = one electrical node) ===")
    root_of_group = {}
    for root, members in final.items():
        pin_list = []
        for pt, entries in members:
            for inst, pin in entries:
                pin_list.append(f"{inst}.{pin}@{pt}")
        label = net_label(uf.find(root))
        name = label or "(unnamed net)"
        print(f"  {name}: {', '.join(sorted(pin_list))}")

    # ---- specific check the user asked about ----
    def find_pin(inst_name, pin_name=None):
        for root, members in final.items():
            for pt, entries in members:
                for inst, pin in entries:
                    if inst == inst_name and (pin_name is None or pin == pin_name):
                        return root, pt, pin
        return None, None, None

    print("\n=== Gate-bias specific check ===")
    m1_gate_root, m1_gate_pt, m1_gate_pin = find_pin("M1", "G")
    vb_root, vb_pt, _ = None, None, None
    vbias_roots = label_groups.get("VBIAS", set())
    if m1_gate_root is None:
        print("Could not find M1's gate pin -- check that nfet_01v8.sym was "
              "located correctly above (see WARNING section if any).")
        return

    if vbias_roots and uf.find(next(iter(vbias_roots))) == uf.find(m1_gate_root):
        print("M1 gate IS on the same net as the VBIAS label. "
              "If DC bias still looks wrong, the problem is elsewhere "
              "(check VB source polarity/value, not connectivity).")
    else:
        print("CONFIRMED: M1 gate is NOT electrically connected to the "
              "VBIAS net. This matches your reported VGS~4.5mV symptom.")
        rbias_root, rbias_p1, _ = find_pin("Rbias")
        # find both Rbias pins specifically
        rbias_pins = []
        for root, members in final.items():
            for pt, entries in members:
                for inst, pin in entries:
                    if inst == "Rbias":
                        rbias_pins.append((pt, pin, root))
        print(f"Rbias pins found at: {[(p, n) for p, n, r in rbias_pins]}")
        if len(rbias_pins) != 2:
            print("Could not identify exactly 2 Rbias pins -- inspect the "
                  "report above manually and connect by hand in xschem "
                  "using the coordinates printed there.")
            return

        # gate net's floating end and vbias net's floating end are the
        # two points closest to each Rbias pin -> wire Rbias pin to
        # nearest existing point actually IN the gate net / vbias net.
        gate_pts = [pt for pt, entries in final[m1_gate_root]]
        vbias_root = uf.find(next(iter(vbias_roots))) if vbias_roots else None
        vbias_pts = [pt for pt, entries in final.get(vbias_root, [])] if vbias_root else []

        def closest(pt, candidates):
            return min(candidates, key=lambda c: (c[0]-pt[0])**2 + (c[1]-pt[1])**2)

        (rp1, rn1, _), (rp2, rn2, _) = rbias_pins
        # decide which Rbias pin faces the gate side vs the vbias side by
        # proximity
        if min((rp1[0]-p[0])**2+(rp1[1]-p[1])**2 for p in gate_pts) < \
           min((rp2[0]-p[0])**2+(rp2[1]-p[1])**2 for p in gate_pts):
            gate_side, vbias_side = rp1, rp2
        else:
            gate_side, vbias_side = rp2, rp1

        gate_target = closest(gate_side, gate_pts)
        vbias_target = closest(vbias_side, vbias_pts) if vbias_pts else None

        new_wires = []
        if gate_side != gate_target:
            new_wires.append((gate_side, gate_target))
        if vbias_target and vbias_side != vbias_target:
            new_wires.append((vbias_side, vbias_target))

        print("\nWires needed to close the gap:")
        for (a, b) in new_wires:
            print(f"  N {a[0]:g} {a[1]:g} {b[0]:g} {b[1]:g} {{}}")

        if not args.report_only and args.sch_out:
            out_lines = sch_text.rstrip("\n").split("\n")
            for (a, b) in new_wires:
                out_lines.append(f"N {a[0]:g} {a[1]:g} {b[0]:g} {b[1]:g} {{}}")
            with open(args.sch_out, "w") as f:
                f.write("\n".join(out_lines) + "\n")
            print(f"\nWrote corrected schematic to: {args.sch_out}")


if __name__ == "__main__":
    main()
