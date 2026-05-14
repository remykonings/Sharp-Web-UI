#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"

# Default to the shared environment used for ml-sharp + Sharp-Web-UI.
DEFAULT_PYTHON_BIN="${PROJECT_DIR}/../.venv-sharp311/bin/python"
PYTHON_BIN="${SHARP_WEBUI_PYTHON_BIN:-$DEFAULT_PYTHON_BIN}"

TARGET_APP_PATH="${1:-$HOME/Desktop/Sharp Web UI Native.app}"
APP_NAME="$(basename "$TARGET_APP_PATH" .app)"
CONTENTS_DIR="${TARGET_APP_PATH}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python runtime not found: ${PYTHON_BIN}" >&2
  echo "Set SHARP_WEBUI_PYTHON_BIN=/absolute/path/to/python and try again." >&2
  exit 1
fi

echo "Installing native launcher dependencies..."
"${PYTHON_BIN}" -m pip install -r "${PROJECT_DIR}/requirements-native.txt" >/dev/null

mkdir -p "$MACOS_DIR"

cat > "${CONTENTS_DIR}/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>launch.sh</string>
  <key>CFBundleIdentifier</key>
  <string>com.remy.sharpwebui.native</string>
  <key>CFBundleName</key>
  <string>${APP_NAME}</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
</dict>
</plist>
PLIST

cat > "${MACOS_DIR}/launch.sh" <<LAUNCHER
#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR}"
PYTHON_BIN="${PYTHON_BIN}"

if [[ ! -x "\${PYTHON_BIN}" ]]; then
  osascript -e 'display alert "Sharp Web UI Error" message "Python runtime not found at configured path." as critical'
  exit 1
fi

if [[ ! -f "\${PROJECT_DIR}/native_mac_app.py" ]]; then
  osascript -e 'display alert "Sharp Web UI Error" message "native_mac_app.py was not found in the project folder." as critical'
  exit 1
fi

cd "\${PROJECT_DIR}"
exec "\${PYTHON_BIN}" native_mac_app.py
LAUNCHER

chmod +x "${MACOS_DIR}/launch.sh"

echo "Created native macOS app:"
echo "  ${TARGET_APP_PATH}"
echo
echo "Double-click it from Finder/Desktop. It runs in a native window (no external browser)."
