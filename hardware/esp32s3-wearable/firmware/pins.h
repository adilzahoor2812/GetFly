/* Auto-generated pin map for ESP32-S3 wearable PCB Rev A */
#pragma once

// Sharp LS013B7DH03 memory LCD (SPI)
#define PIN_LCD_SCK     12
#define PIN_LCD_MOSI    11
#define PIN_LCD_CS      10
#define PIN_LCD_DISP    9
#define PIN_LCD_EXTCOM  13   // PWM ~1 Hz EXTCOMIN

// 6-key keypad (active low)
#define PIN_KEY_UP      1
#define PIN_KEY_DOWN    2
#define PIN_KEY_LEFT    3
#define PIN_KEY_RIGHT   4
#define PIN_KEY_ENTER   5
#define PIN_KEY_BACK    6

// Battery sense (ADC1)
#define PIN_VBAT_ADC    7

// Native USB (ESP32-S3)
#define PIN_USB_DM      19
#define PIN_USB_DP      20

// System
#define PIN_BOOT        0
#define PIN_EN          -1  // dedicated reset circuit
