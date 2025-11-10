#!/bin/bash
# Stop BookWise Librarian service

echo "🛑 Stopping BookWise Librarian Service..."
launchctl unload ~/Library/LaunchAgents/com.bookwise.librarian.plist 2>/dev/null || true

sleep 1

if launchctl list | grep -q "com.bookwise.librarian"; then
    echo "❌ Service still running"
    exit 1
else
    echo "✅ Service stopped"
    echo ""
    echo "💡 To start again: ./service-start.sh"
    echo "💡 To uninstall: rm ~/Library/LaunchAgents/com.bookwise.librarian.plist"
fi

