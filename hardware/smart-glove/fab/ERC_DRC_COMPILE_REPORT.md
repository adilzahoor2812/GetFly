# ERC / DRC Compile — SignSpeak Rev H

## ERC
```
ERC report (2026-07-18T23:15:58+0000, Encoding UTF8)

***** Sheet /
[no_connect_dangling]: Unconnected "no connection" flag
    ; warning
    @(48.2600 mm, 105.4100 mm): No Connect
[no_connect_connected]: Pin with 'no connection' type is connected
    ; warning
    @(48.2600 mm, 105.4100 mm): Symbol U5 Hidden pin 7 [NC, Unconnected, Line]
    @(48.2600 mm, 105.4100 mm): No Connect
[lib_symbol_issues]: Symbol 'AMS1117-3.3' not found in symbol library 'Device'
    ; warning
    @(50.8000 mm, 129.5400 mm): Symbol U3 [AMS1117-3.3]
[lib_symbol_issues]: Symbol 'FS8205A' not found in symbol library 'Device'
    ; warning
    @(250.1900 mm, 80.0100 mm): Symbol U7 [FS8205A]
[lib_symbol_issues]: Symbol 'DW01A' not found in symbol library 'Device'
    ; warning
    @(250.1900 mm, 50.8000 mm): Symbol U6 [DW01A]
[lib_symbol_issues]: Symbol 'TP4056' not found in symbol library 'Device'
    ; warning
    @(152.4000 mm, 50.8000 mm): Symbol U2 [TP4056]

 ** ERC messages: 6  Errors 0  Warnings 6

```

## DRC
```
** Drc report for smart-glove.kicad_pcb **
** Created on 2026-07-18T23:15:57+0000 **

** Found 7 DRC violations **
[silk_overlap]: Silkscreen overlap
    Rule: board setup constraints silk; warning
    @(50.7000 mm, 46.1000 mm): Segment on F.Silkscreen
    @(48.0000 mm, 48.5000 mm): PCB Text 'USB-C SERIAL' on F.Silkscreen
[silk_over_copper]: Silkscreen clipped by solder mask
    Local override; warning
    @(10.0000 mm, 3.0000 mm): PCB Text 'SignSpeak Smart Glove' on F.Silkscreen
[silk_over_copper]: Silkscreen clipped by solder mask
    Local override; warning
    @(48.0000 mm, 48.5000 mm): PCB Text 'USB-C SERIAL' on F.Silkscreen
[silk_over_copper]: Silkscreen clipped by solder mask
    Local override; warning
    @(10.0000 mm, 5.0000 mm): PCB Text 'Man Who Embed Rev H' on F.Silkscreen
[text_height]: Text height out of range (board setup constraints silk text height min height 0.8000 mm; actual 0.6500 mm)
    Rule: board setup constraints silk text height; warning
    @(48.0000 mm, 48.5000 mm): PCB Text 'USB-C SERIAL' on F.Silkscreen
[text_height]: Text height out of range (board setup constraints silk text height min height 0.8000 mm; actual 0.7500 mm)
    Rule: board setup constraints silk text height; warning
    @(50.0000 mm, 4.0000 mm): PCB Text 'ANT KEEP OUT' on F.Silkscreen
[text_height]: Text height out of range (board setup constraints silk text height min height 0.8000 mm; actual 0.7500 mm)
    Rule: board setup constraints silk text height; warning
    @(10.0000 mm, 5.0000 mm): PCB Text 'Man Who Embed Rev H' on F.Silkscreen

** Found 0 unconnected pads **

** Found 0 Footprint errors **

** End of Report **

```
