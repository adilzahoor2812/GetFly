# Smart Glove — ERC & DRC Compile Report

**Tool:** `8.0.9`

## ERC

```
 ** ERC messages: 7  Errors 7  Warnings 0
```

| Type | Count |
|------|------:|
| label_dangling | 4 |
| pin_not_connected | 3 |

Artifacts: `fab/ERC_report.txt`, `fab/ERC_report.json`

## DRC

```
** Found 276 DRC violations **
** Found 68 unconnected pads **
** Found 0 Footprint errors **
```

| Type | Count |
|------|------:|
| solder_mask_bridge | 140 |
| unconnected_items | 68 |
| items_not_allowed | 41 |
| shorting_items | 30 |
| tracks_crossing | 21 |
| drill_out_of_range | 12 |
| courtyards_overlap | 10 |
| via_dangling | 9 |
| silk_overlap | 4 |
| silk_over_copper | 3 |
| silk_edge_clearance | 2 |
| clearance | 2 |
| hole_clearance | 1 |
| track_dangling | 1 |

Artifacts: `fab/DRC_report.txt`, `fab/DRC_report.json`

## Notes

- ERC compiled on companion schematic (power rails, flex divider resistors, decoupling).
- DRC compiled on PCB RevB. Violations remain from automated L-routing; resolve in KiCad before volume production.
- Re-run: `kicad-cli sch erc` / `kicad-cli pcb drc`
