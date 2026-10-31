#!/usr/bin/env python3
"""Debrand + green-retheme the open-source Flipper Android app (MIT licensed).

Run from the repo root:  python3 debrand.py
Idempotent enough to re-run on a fresh checkout. Keeps LICENSE intact.
"""
import colorsys, json, os, re, shutil, sys
from pathlib import Path

APP_NAME = os.environ.get("APP_NAME", "Verdant")
APP_ID = os.environ.get("APP_ID", "com.verdant.companion")
TARGET_HUE = 152 / 360.0          # cool emerald / mint green
SPLASH_BG_LIGHT = "#F2FBF6"
SPLASH_BG_DARK = "#04140D"
ICON_BG = "#0B2E20"
ICON_FG = "#3DFFA6"

root = Path.cwd()
if not (root / "settings.gradle.kts").exists():
    sys.exit("Run this from the Flipper-Android-App repo root.")

def edit(path, fn):
    p = root / path
    s = p.read_text(encoding="utf-8")
    n = fn(s)
    if n != s:
        p.write_text(n, encoding="utf-8")
        print("  edited", path)

# ---------------------------------------------------------------- 1. name + id
print("1. App name and package id")
for f in ["instances/android/app/src/main/res/values/strings.xml",
          "instances/wearable/src/main/res/values/strings.xml"]:
    edit(f, lambda s: re.sub(r'(<string name="app_name">)[^<]*(</string>)',
                             rf"\g<1>{APP_NAME}\g<2>", s))

edit("build-logic/plugins/convention/src/main/kotlin/com/flipperdevices/buildlogic/ApkConfig.kt",
     lambda s: s.replace('APPLICATION_ID = "com.flipperdevices.app"',
                         f'APPLICATION_ID = "{APP_ID}"'))

# google-services plugin needs a client entry for the new package id
gs = root / "instances/android/app/google-services.json"
d = json.loads(gs.read_text())
pkgs = [c["client_info"]["android_client_info"]["package_name"] for c in d["client"]]
for suffix in ["", ".debug"]:
    pid = APP_ID + suffix
    if pid not in pkgs:
        c = json.loads(json.dumps(d["client"][0]))
        c["client_info"]["android_client_info"]["package_name"] = pid
        d["client"].append(c)
gs.write_text(json.dumps(d, indent=2))
print("  edited", gs.relative_to(root))

# ---------------------------------------------------------------- 2. recolor
print("2. Orange -> green across Kotlin palettes and vector drawables")
def to_green(rgb):
    r, g, b = (int(rgb[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if not (18 / 360 <= h <= 38 / 360 and s >= 0.45 and 0.12 <= l <= 0.95):
        return None
    r, g, b = colorsys.hls_to_rgb(TARGET_HUE, min(l, 0.9), s * 0.92)
    return "%02X%02X%02X" % tuple(round(x * 255) for x in (r, g, b))

kt_re = re.compile(r"0x([0-9A-Fa-f]{2})([0-9A-Fa-f]{6})")
xml_re = re.compile(r"#([0-9A-Fa-f]{2})?([0-9A-Fa-f]{6})\b")
changed = 0
for base in ["components", "instances"]:
    for p in (root / base).rglob("*"):
        if p.suffix not in (".kt", ".xml") or "/build/" in str(p):
            continue
        s = p.read_text(encoding="utf-8", errors="ignore")
        def kt(m):
            g = to_green(m.group(2)); return f"0x{m.group(1)}{g}" if g else m.group(0)
        def xm(m):
            g = to_green(m.group(2)); return f"#{m.group(1) or ''}{g}" if g else m.group(0)
        n = kt_re.sub(kt, s) if p.suffix == ".kt" else xml_re.sub(xm, s)
        if n != s:
            p.write_text(n, encoding="utf-8"); changed += 1
print(f"  recolored {changed} files")

# ---------------------------------------------------------------- 3. icon
print("3. Launcher icon (original glyph: hexagon + signal arcs)")
res = root / "components/core/ui/res/src/androidMain/res"
GLYPH = """    <group android:translateX="24" android:translateY="24" android:scaleX="1.25" android:scaleY="1.25">
        <path android:fillColor="{c}" android:fillType="evenOdd" android:pathData="M24,2 L43,13 L43,35 L24,46 L5,35 L5,13 Z M24,8 L10,16 L10,32 L24,40 L38,32 L38,16 Z"/>
        <path android:fillColor="{c}" android:fillType="evenOdd" android:pathData="M24,20 a4,4 0 1,1 0,8 a4,4 0 1,1 0,-8 Z"/>
        <path android:strokeColor="{c}" android:strokeWidth="2.6" android:strokeLineCap="round" android:pathData="M17,17 a10,10 0 0,0 0,14 M31,17 a10,10 0 0,1 0,14"/>
    </group>"""
def vector(color, size=108):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="{size}dp" android:height="{size}dp"
    android:viewportWidth="108" android:viewportHeight="108">
{GLYPH.format(c=color)}
</vector>
"""
(res / "drawable/ic_launcher_foreground.xml").write_text(vector(ICON_FG))
(res / "drawable/ic_launcher_foreground_monochrome.xml").write_text(vector("#FFFFFF"))
(res / "values/ic_launcher_background.xml").write_text(
    f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">{ICON_BG}</color>\n</resources>\n')
for d_ in res.glob("mipmap-*dpi"):          # old raster foregrounds (branded)
    for f in d_.glob("ic_launcher_foreground.png"):
        f.unlink()
    if not any(d_.iterdir()):
        d_.rmdir()
# minSdk is 26, so the adaptive icon in mipmap-anydpi-v26 covers every device

# ---------------------------------------------------------------- 4. splash
print("4. Splash screens")
app_res = root / "instances/android/app/src/main/res"
for name in ["pic_splashscreen_dolphin.xml", "pic_splashscreen_furippa.xml", "pic_splashscreen_text.xml"]:
    f = app_res / "drawable" / name
    if f.exists():
        f.unlink()
(app_res / "drawable/pic_splash_glyph.xml").write_text(vector(ICON_FG, 120))
(app_res / "drawable/splash_screen.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@color/background" />
    <item android:drawable="@drawable/pic_splash_glyph" android:gravity="center" />
</layer-list>
""")
edit("instances/android/app/src/main/res/values-v31/styles.xml",
     lambda s: re.sub(r'\s*<item name="android:windowSplashScreenBrandingImage">[^<]*</item>', "",
                      s.replace("@drawable/pic_splashscreen_dolphin_v31", "@drawable/pic_splash_glyph_v31")))
(res / "drawable-v31/pic_splash_glyph_v31.xml").write_text(vector(ICON_FG, 108))
for name in ["pic_splashscreen_dolphin_v31.xml", "pic_splashscreen_text_v31.xml", "ic_splashscreen_text_centred.xml"]:
    for f in res.rglob(name):
        f.unlink()

# background tint behind splash / window
edit("components/core/ui/res/src/androidMain/res/values/colors.xml",
     lambda s: re.sub(r'(<color name="background">)[^<]*', rf"\g<1>{SPLASH_BG_LIGHT}", s))
edit("components/core/ui/res/src/androidMain/res/values-night/colors.xml",
     lambda s: re.sub(r'(<color name="background">)[^<]*', rf"\g<1>{SPLASH_BG_DARK}", s))

# ---------------------------------------------------------------- 5. sanity
print("5. Checking nothing still references removed drawables")
gone = ["pic_splashscreen_dolphin", "pic_splashscreen_furippa", "pic_splashscreen_text",
        "ic_splashscreen_text_centred"]
bad = []
for p in list((root / "components").rglob("*.xml")) + list((root / "instances").rglob("*.xml")) \
        + list((root / "components").rglob("*.kt")) + list((root / "instances").rglob("*.kt")):
    s = p.read_text(encoding="utf-8", errors="ignore")
    for g in gone:
        if re.search(rf"\b{g}\b", s):
            bad.append(f"{p.relative_to(root)} -> {g}")
if bad:
    print("  WARNING, dangling references:\n   " + "\n   ".join(bad)); sys.exit(1)
print(f"Done: {APP_NAME} ({APP_ID})")
