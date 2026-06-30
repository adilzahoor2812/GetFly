# TestFlight Distribution Guide

Use this guide to install **GetFly** (ESP32 Quadcopter Controller) on your iPhone via TestFlight.

## Prerequisites

1. **Apple Developer Program** membership (paid account).
2. **Mac with Xcode** installed (latest stable version recommended).
3. Access to [App Store Connect](https://appstoreconnect.apple.com) for team `49QJL3FTQK`.
4. Bundle ID `codebuzz.GetFly` registered in the Apple Developer portal and App Store Connect.

## One-time App Store Connect setup

1. Sign in to [App Store Connect](https://appstoreconnect.apple.com).
2. Go to **Apps** → **+** → **New App**.
3. Set:
   - **Platform**: iOS
   - **Name**: GetFly
   - **Bundle ID**: `codebuzz.GetFly`
   - **SKU**: any unique string (e.g. `getfly-quadcopter-001`)
4. Under **App Information**, add a short description. No App Store screenshots are required for internal TestFlight testing.

## Option A — Upload with Xcode (recommended first time)

1. Open `Hike.xcodeproj` on your Mac.
2. Select the **GetFly** target → **Signing & Capabilities**.
   - Team: your team (`49QJL3FTQK`)
   - Bundle Identifier: `codebuzz.GetFly`
   - Signing: **Automatically manage signing**
3. Select **Any iOS Device (arm64)** as the run destination (not a simulator).
4. Menu: **Product → Archive**.
5. When the Organizer opens, select the archive → **Distribute App**.
6. Choose **App Store Connect** → **Upload**.
7. Accept defaults for symbols and signing; finish the upload.

After upload, App Store Connect processes the build (usually 5–30 minutes). You will get an email when it is ready.

## Option B — Upload with fastlane

```bash
cd /path/to/Hike
bundle install
bundle exec fastlane beta
```

On first run, fastlane will prompt for your Apple ID or App Store Connect API key. To bump the build number before re-uploading the same marketing version:

```bash
bundle exec fastlane bump_build
```

## Add testers

### Internal testers (fastest)

- Up to 100 users on your App Store Connect team.
- No Beta App Review required.
- App Store Connect → your app → **TestFlight** → **Internal Testing** → add testers.

### External testers

- Up to 10,000 users by email or public link.
- Requires a short **Beta App Review** (usually quick for utility apps).
- App Store Connect → **External Testing** → create a group → add the build → submit for review.

## Install on your iPhone

1. Install the **TestFlight** app from the App Store.
2. Accept the email invite, or open the public TestFlight link.
3. Tap **Install** for GetFly.

## Testing with your ESP32

1. Flash the ESP32 with firmware from `firmware/esp32_quadcopter_server/`.
2. On the iPhone, join the ESP32 Wi‑Fi network (`Quadcopter-ESP32` by default).
3. Open GetFly → **Settings** → confirm address `192.168.4.1:80`.
4. When prompted, allow **Local Network** access (required for ESP32 HTTP).

## Version and build numbers

| Setting | Current value | Where to change |
|---------|---------------|-----------------|
| Marketing version | 1.0 | Xcode → GetFly target → General → Version |
| Build number | 1 | Xcode → General → Build, or `fastlane bump_build` |

**Important:** Each TestFlight upload needs a **unique build number**. Increment `CURRENT_PROJECT_VERSION` before every upload if the marketing version stays at 1.0.

## Device requirements

The project currently targets **iOS 18.0+**. Testers need an iPhone or iPad running iOS 18 or later. To support older devices, lower `IPHONEOS_DEPLOYMENT_TARGET` in the Xcode project.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Archive button is grayed out | Select **Any iOS Device (arm64)**, not a simulator. |
| Signing errors | Confirm team membership and that bundle ID `codebuzz.GetFly` exists in your developer account. |
| Build stuck "Processing" | Wait up to 30 minutes; check email for processing errors. |
| Cannot reach ESP32 on TestFlight build | Ensure Local Network permission was granted; verify iPhone is on ESP32 Wi‑Fi. |
| Export compliance prompt | The project sets `ITSAppUsesNonExemptEncryption = NO` (standard HTTPS only, no custom crypto). |

## What was added for TestFlight

- Shared Xcode scheme: `Hike.xcodeproj/xcshareddata/xcschemes/GetFly.xcscheme`
- Local network ATS exception (HTTP to ESP32 on LAN)
- Export compliance flag (skips repeated encryption questionnaires)
- `fastlane/` + `ExportOptions.plist` for automated uploads
