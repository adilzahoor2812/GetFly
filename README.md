# ESP32 Quadcopter iOS Controller

SwiftUI iOS app to control an autonomous quadcopter over Wi‑Fi using an ESP32 microcontroller.

## Features

- Live drone status (position, battery, flight mode)
- Set target coordinates (X, Y, Z in meters)
- Tap the OpenStreetMap to pick coordinates (relative to your home point)
- Build and run multi-waypoint missions
- Flight controls: Arm, Disarm, Take Off, Land, Hover, Return Home, Emergency Stop
- Configurable ESP32 IP address and port

## Setup

1. Flash the ESP32 with the reference firmware in `firmware/esp32_quadcopter_server/`.
2. Connect your iPhone to the ESP32 Wi‑Fi network (`Quadcopter-ESP32` by default).
3. Open the app in Xcode and run on your device.
4. In **Settings** (gear icon), confirm the ESP32 address (default: `192.168.4.1:80`).

## HTTP API (ESP32)

### GET `/status`

```json
{
  "armed": false,
  "flying": false,
  "x": 0.0,
  "y": 0.0,
  "z": 0.0,
  "battery": 100,
  "mode": "idle",
  "message": "ok"
}
```

### POST `/command`

Go to a coordinate:

```json
{
  "action": "goto",
  "x": 2.0,
  "y": 1.5,
  "z": 1.5
}
```

Run a waypoint mission:

```json
{
  "action": "mission",
  "waypoints": [
    { "x": 1.0, "y": 0.0, "z": 1.5, "hold_seconds": 2.0 },
    { "x": 2.0, "y": 2.0, "z": 1.5, "hold_seconds": 2.0 }
  ]
}
```

Other actions: `arm`, `disarm`, `takeoff`, `land`, `hover`, `home`, `emergency_stop`.

Response:

```json
{ "success": true, "message": "Command accepted" }
```

## OpenStreetMap

The flight map uses **OpenStreetMap** tiles via MapKit. Set your **home point** in Settings:

1. Open **Settings** (gear icon)
2. Set home latitude/longitude, or tap **Use My Current Location**
3. Local X/Y (meters) are calculated east/north from home
4. Tap the map to set target coordinates

Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors.

## Coordinate system

- **X**: forward (meters)
- **Y**: left/right (meters)
- **Z**: altitude (meters)

Origin (0, 0, 0) is the home/takeoff point.

## Project structure

```
Hike/
  Model/          - Coordinate, waypoint, command, status types
  Services/       - ESP32 HTTP client and connection settings
  ViewModel/      - DroneViewModel
  App Main/       - SwiftUI screens
firmware/         - ESP32 Arduino reference server
```

## Notes

- The included ESP32 sketch is a **reference server** — wire the TODO sections into your real motor/PID/autopilot code.
- iOS requires local network permission to reach the ESP32 on your LAN or AP.
- If your PDF specifies a different protocol, share it and the app can be adjusted to match.
