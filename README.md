# Verdant — debranded, green Flipper companion app

Builds the open-source Flipper Android app (MIT licensed) with:

- App name **Verdant** (change it when you run the build) and package id `com.verdant.companion`, so it installs alongside the official app
- Orange accent recolored to a cool emerald/mint green throughout the UI, illustrations and dark/light palettes
- New original launcher icon (hexagon + signal glyph) and plain green splash screen — dolphin artwork and wordmark removed
- Google services, analytics and crash reporting switched off

In-app text that names the *device* (e.g. "Connect your Flipper") is left as-is, since that's the hardware you're pairing.

## Build it (about 20–40 min, free, works from a phone)

1. Create a new GitHub repository (private is fine).
2. Upload `debrand.py` to its root and `.github/workflows/build.yml` to that same path.
3. Go to **Actions → Build Verdant APK → Run workflow**.
4. When it finishes, open **Releases** and download `verdant.apk` onto your phone. Allow "Install unknown apps" for your browser when prompted.

## Keep updates installable (optional)

Without a signing key, each build uses a throwaway key, so a new build has to replace (uninstall) the old one. To keep one stable key, add two repository secrets:

- `KEYSTORE_B64` — `base64 -w0 release.jks` of a keystore whose key alias is `app`
- `KEYSTORE_PASSWORD` — its store/key password

## Notes

The upstream project is MIT licensed; keep its `LICENSE` notice if you redistribute the APK.
