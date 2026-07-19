/**
 * SignSpeak Smart Glove — Rev H firmware (Man Who Embed)
 *
 * Board: ESP32-WROOM-32E
 * - 5× flex sensors on ADC1 (GPIO36/39/34/35/32)
 * - MPU-6050 on I2C (SDA=GPIO21, SCL=GPIO22)
 * - Status LED on GPIO2
 *
 * Upload / Serial Monitor:
 *   USB-C (onboard CH340) or J4 UART dongle @ 115200
 *   Hold BOOT, tap EN if auto-reset is not used.
 */

#include <Wire.h>

static const int PIN_FLEX[5] = {36, 39, 34, 35, 32};  // FLEX1..FLEX5
static const int PIN_SDA = 21;
static const int PIN_SCL = 22;
static const int PIN_STAT = 2;
static const uint8_t MPU_ADDR = 0x68;

static bool mpuOk = false;

static bool mpuWrite8(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

static bool mpuRead(uint8_t reg, uint8_t *buf, size_t n) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, (uint8_t)n) != (int)n) return false;
  for (size_t i = 0; i < n; i++) buf[i] = Wire.read();
  return true;
}

static bool mpuBegin() {
  uint8_t who = 0;
  if (!mpuRead(0x75, &who, 1)) return false;  // WHO_AM_I
  if (who != 0x68 && who != 0x70 && who != 0x71) {
    // 0x68 classic; some clones differ — still try wake
  }
  if (!mpuWrite8(0x6B, 0x00)) return false;  // PWR_MGMT_1 wake
  delay(50);
  return true;
}

static bool mpuReadAccelGyro(int16_t *ax, int16_t *ay, int16_t *az,
                             int16_t *gx, int16_t *gy, int16_t *gz) {
  uint8_t b[14];
  if (!mpuRead(0x3B, b, 14)) return false;
  *ax = (int16_t)((b[0] << 8) | b[1]);
  *ay = (int16_t)((b[2] << 8) | b[3]);
  *az = (int16_t)((b[4] << 8) | b[5]);
  *gx = (int16_t)((b[8] << 8) | b[9]);
  *gy = (int16_t)((b[10] << 8) | b[11]);
  *gz = (int16_t)((b[12] << 8) | b[13]);
  return true;
}

void setup() {
  pinMode(PIN_STAT, OUTPUT);
  digitalWrite(PIN_STAT, HIGH);

  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println(F("SignSpeak Smart Glove — Man Who Embed"));
  Serial.println(F("Firmware Rev H · flex×5 + MPU-6050"));

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);
  mpuOk = mpuBegin();
  Serial.print(F("MPU-6050: "));
  Serial.println(mpuOk ? F("OK") : F("NOT FOUND (check solder/power)"));
  Serial.println(F("flex1,flex2,flex3,flex4,flex5,ax,ay,az,gx,gy,gz"));
}

void loop() {
  int flex[5];
  for (int i = 0; i < 5; i++) {
    long acc = 0;
    for (int s = 0; s < 4; s++) acc += analogRead(PIN_FLEX[i]);
    flex[i] = (int)(acc / 4);
  }

  int16_t ax = 0, ay = 0, az = 0, gx = 0, gy = 0, gz = 0;
  if (mpuOk) {
    if (!mpuReadAccelGyro(&ax, &ay, &az, &gx, &gy, &gz)) {
      mpuOk = false;
    }
  }

  // CSV line for Serial Monitor / host app
  for (int i = 0; i < 5; i++) {
    Serial.print(flex[i]);
    Serial.print(',');
  }
  Serial.print(ax); Serial.print(',');
  Serial.print(ay); Serial.print(',');
  Serial.print(az); Serial.print(',');
  Serial.print(gx); Serial.print(',');
  Serial.print(gy); Serial.print(',');
  Serial.println(gz);

  digitalWrite(PIN_STAT, (millis() / 250) % 2);
  delay(50);  // ~20 Hz
}
