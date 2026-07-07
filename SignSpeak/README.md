# SignSpeak Mobile App (Flutter Starter)

This is a starter mobile app for the SignSpeak glove project.

## Features included

- BLE pairing screen scaffold
- Live translation screen scaffold
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
