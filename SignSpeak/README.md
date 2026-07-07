# SignSpeak Mobile App (Flutter Starter)

This is a starter mobile app for the SignSpeak glove project.

## Features included

- BLE pairing screen scaffold
- Live translation screen scaffold
- Mock demo mode (works without glove hardware)
- Packet model for glove data
- BLE service skeleton (scan/connect/subscribe/write)
- Text-to-speech service

## Run locally

Flutter SDK is not available in this cloud environment, so run these commands on your machine:

```bash
cd SignSpeak
flutter pub get
flutter run
```

## Next steps

1. Replace BLE UUIDs in `lib/core/constants/ble_constants.dart`.
2. Connect `PairingPage` scan/connect actions to your glove.
3. Feed notification packets into `LiveTranslatePage`.
4. Add local history storage (Hive/SQLite).
5. Request runtime Bluetooth permissions with `permission_handler` before scanning.

## Android BLE permissions

Permission-ready Android files are included:

- `android/app/src/main/AndroidManifest.xml`
- `android/app/src/main/kotlin/com/signspeak/app/MainActivity.kt`

These are starter templates. If you regenerate a full Flutter Android folder via
`flutter create .`, merge the BLE permissions from this manifest into the generated one.
