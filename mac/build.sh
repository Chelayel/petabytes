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

# Signed with the project's own certificate when there is one, so macOS recognizes every build as the same
# app and permissions (Accessibility, for talking above the Dock) survive updates. CI passes it as base64 in
# MAC_SIGNING_P12 with MAC_SIGNING_PASSWORD; locally it's ~/.config/petabytes/signing.p12. It goes into a
# throwaway keychain, so the login keychain is never touched. Without one, the app is signed ad hoc.
p12="$HOME/.config/petabytes/signing.p12"
if [ -n "${MAC_SIGNING_P12:-}" ]; then
  p12=build/signing.p12
  printf '%s' "$MAC_SIGNING_P12" | base64 --decode > "$p12"
  password="$MAC_SIGNING_PASSWORD"
elif [ -f "$p12" ]; then
  password=$(cat "$HOME/.config/petabytes/signing-password")
else
  p12=""
fi
if [ -n "$p12" ]; then
  keychain="$PWD/build/signing.keychain-db"
  keychain_password=$(uuidgen)
  security create-keychain -p "$keychain_password" "$keychain"
  security set-keychain-settings "$keychain"
  security unlock-keychain -p "$keychain_password" "$keychain"
  security import "$p12" -k "$keychain" -P "$password" -T /usr/bin/codesign >/dev/null
  security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$keychain_password" "$keychain" >/dev/null
  identity=$(security find-identity -p codesigning "$keychain" | awk '/\)/ { print $2; exit }')
  codesign --force --sign "$identity" --keychain "$keychain" "$app"
  security delete-keychain "$keychain"
  [ -n "${MAC_SIGNING_P12:-}" ] && rm -f build/signing.p12
else
  codesign --force --sign - "$app"
fi

stage=build/dmg
mkdir -p "$stage"
cp -R "$app" "$stage/"
ln -s /Applications "$stage/Applications"
hdiutil create -volname Petabytes -srcfolder "$stage" -ov -format UDZO "build/Petabytes-$version.dmg" >/dev/null
echo "build/Petabytes-$version.dmg"
