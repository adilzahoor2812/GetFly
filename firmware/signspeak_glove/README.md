# SignSpeak Smart Glove — Firmware

Arduino sketch for **ESP32-WROOM-32E** on the SignSpeak Rev H PCB.

## Upload (USB-C)

1. Install [Arduino IDE](https://www.arduino.cc/) + **esp32** board package (Espressif).
2. Board: **ESP32 Dev Module** · Upload speed **115200** · Port = the CH340 COM port.
3. Plug laptop → **USB-C** on the glove board (onboard CH340).
4. Click **Upload**. If it stalls on “Connecting…”, hold **BOOT**, tap **EN**, release **BOOT**.

## Serial Monitor

Same USB-C port · baud **115200**.

CSV stream:

```text
flex1,flex2,flex3,flex4,flex5,ax,ay,az,gx,gy,gz
```

## Pins (Rev H)

| Function | GPIO |
|----------|------|
| FLEX1…5 | 36, 39, 34, 35, 32 |
| SDA / SCL | 21 / 22 |
| STAT LED | 2 |
| UART0 | USB-C via CH340 (also J4) |
