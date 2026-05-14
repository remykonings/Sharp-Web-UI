#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"

# Default to the shared environment we created for ml-sharp + Sharp-Web-UI.
DEFAULT_PYTHON_BIN="${PROJECT_DIR}/../.venv-sharp311/bin/python"
PYTHON_BIN="${SHARP_WEBUI_PYTHON_BIN:-$DEFAULT_PYTHON_BIN}"

TARGET_APP_PATH="${1:-$HOME/Desktop/Sharp Web UI.app}"
APP_NAME="$(basename "$TARGET_APP_PATH" .app)"
CONTENTS_DIR="${TARGET_APP_PATH}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"

mkdir -p "$MACOS_DIR"

cat > "${CONTENTS_DIR}/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>launch.sh</string>
  <key>CFBundleIdentifier</key>
  <string>com.remy.sharpwebui</string>
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
APP_URL="http://127.0.0.1:7880"

if [[ ! -f "\${PROJECT_DIR}/app.py" ]]; then
  osascript -e 'display alert "Sharp Web UI Error" message "app.py was not found in the project folder." as critical'
  exit 1
fi

if [[ ! -x "\${PYTHON_BIN}" ]]; then
  osascript -e 'display alert "Sharp Web UI Error" message "Python runtime not found at configured path.\nRun build_macos_app.sh again after setting SHARP_WEBUI_PYTHON_BIN." as critical'
  exit 1
fi

if nc -z 127.0.0.1 7880 >/dev/null 2>&1; then
  open "\${APP_URL}"
  exit 0
fi

cd "\${PROJECT_DIR}"
( sleep 2; open "\${APP_URL}" ) &
exec "\${PYTHON_BIN}" app.py
LAUNCHER

chmod +x "${MACOS_DIR}/launch.sh"

echo "Created macOS app:"
echo "  ${TARGET_APP_PATH}"
echo
echo "You can now double-click it from Finder/Desktop."
