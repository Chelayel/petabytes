#!/bin/sh
# Builds mac/build/Petabytes.app and mac/build/Petabytes-<version>.dmg, a universal (Apple silicon and Intel) app
# signed ad hoc. The version defaults to the JetBrains plugin's, so one tag versions everything.
set -eu
cd "$(dirname "$0")"
version=${1:-$(sed -n 's/^pluginVersion=//p' ../intellij/gradle.properties)}

swift build -c release --arch arm64 --arch x86_64
bin=$(swift build -c release --arch arm64 --arch x86_64 --show-bin-path)

rm -rf build
app=build/Petabytes.app
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
cp "$bin/Petabytes" "$app/Contents/MacOS/"
sed "s/{{version}}/$version/g" Info.plist > "$app/Contents/Info.plist"
cp ../web/pet.html ../web/pets.json "$app/Contents/Resources/"

iconset=build/AppIcon.iconset
mkdir -p "$iconset"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" AppIcon.png --out "$iconset/icon_${size}x${size}.png" >/dev/null
  sips -z $((size * 2)) $((size * 2)) AppIcon.png --out "$iconset/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$iconset" -o "$app/Contents/Resources/AppIcon.icns"

codesign --force --sign - "$app"

stage=build/dmg
mkdir -p "$stage"
cp -R "$app" "$stage/"
ln -s /Applications "$stage/Applications"
hdiutil create -volname Petabytes -srcfolder "$stage" -ov -format UDZO "build/Petabytes-$version.dmg" >/dev/null
echo "build/Petabytes-$version.dmg"
