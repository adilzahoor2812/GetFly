## DRC Result

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

Full: `fab/DRC_report.txt`, `fab/DRC_report.json`

## Interpretation

- **ERC** validates the companion schematic (power flags, flex dividers R1–R4, decoupling C1).
- **DRC** validates the PCB. Remaining violations are mainly auto-router L-path shorts/mask bridges and unconnected pads from dense ESP32 module fanout — clean these in KiCad GUI before volume fab.
