# GPIO Mapping — ESP32-S3 Wearable Rev A

## Memory LCD (Sharp LS013B7DH03) — SPI

| Signal | GPIO | Direction | Notes |
|--------|------|-----------|-------|
| LCD_SCK | 12 | Output | SPI clock |
| LCD_MOSI | 11 | Output | SPI data |
| LCD_CS | 10 | Output | Chip select, active low |
| LCD_DISP | 9 | Output | Display on/off |
| LCD_EXTCOM | 13 | Output | EXTCOMIN — toggle ~1 Hz (PWM) |

## Keypad (active low, internal/external 10 kΩ pull-up)

| Key | GPIO | Wake from deep sleep |
|-----|------|----------------------|
| UP | 1 | Yes (RTC GPIO) |
| DOWN | 2 | Yes |
| LEFT | 3 | Yes |
| RIGHT | 4 | Yes |
| ENTER | 5 | Yes |
| BACK | 6 | Yes |

## Power / system

| Signal | GPIO | Notes |
|--------|------|-------|
| VBAT_ADC | 7 | ADC1 — battery voltage divider |
| USB_D− | 19 | Native USB |
| USB_D+ | 20 | Native USB |
| BOOT | 0 | Bootloader strap — boot button |
| EN | — | Reset button on EN pin (not GPIO) |

## Strapping pins to avoid misusing

| GPIO | Strapping function |
|------|-------------------|
| 0 | Boot mode |
| 3 | JTAG / strapping |
| 45 | VDD_SPI voltage |
| 46 | ROM messages |

Do not connect external strong pull-ups/downs on strapping pins without checking the ESP32-S3 datasheet.

## Firmware header

Use `firmware/pins.h` in your ESP-IDF / Arduino / PlatformIO project.
