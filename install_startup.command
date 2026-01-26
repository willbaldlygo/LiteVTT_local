#!/bin/bash
# Enable LiteType at Login via LaunchAgent

APP_PATH="/Users/will/VTT_local"
PLIST_PATH="$HOME/Library/LaunchAgents/com.will.litetype.plist"

echo "========================================================"
echo "    LiteType - Startup Settings"
echo "========================================================"
echo ""

# Create plist
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.will.litetype</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$APP_PATH/LiteType.command</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$APP_PATH</string>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/litetype.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/litetype.err.log</string>
</dict>
</plist>
EOF

echo "✅ Created settings file."
echo ""
echo "Activating..."
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

if [ $? -eq 0 ]; then
    echo "✅ Success! LiteType will run when you log in."
else
    echo "⚠️  Activation failed. You may need to add it manually in System Settings."
fi

echo ""
echo "Press Enter to close..."
read
