# RF & glove mounting (SignSpeak Rev H)

ESP32-WROOM-32E has a PCB antenna at the **finger / top** edge of the board.

## Keep-out

- Do **not** place metal, batteries, flex PCBs, or dense ground pour over the antenna keep-out band (silkscreen: `ANT`).
- Keep ≥ **15 mm** free space beyond the antenna end when possible.
- Wrist-side metal (USB shell, LiPo) is intentional — away from the antenna.

## Glove assembly

1. Mount board on the **back of the hand** (dorsal).
2. Antenna edge toward the **fingers**.
3. Prefer a **plastic / FR4 / fabric** standoff under the antenna zone — not a steel plate.
4. Route flex sensor cables from **J2** toward fingers without covering the antenna.
5. Battery pouch toward the **wrist**, under or beside USB — not under the antenna.

## Validation

After assembly, check Wi‑Fi/BLE RSSI with the glove worn. If range collapses, increase antenna clearance or move metal fasteners.
