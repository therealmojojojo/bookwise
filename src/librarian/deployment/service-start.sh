#!/bin/bash
# Start BookWise Librarian as a macOS launchd service

set -e

echo "🚀 Installing BookWise Librarian Service..."
echo ""

# Check if .env file exists in project root
if [ ! -f "../../../.env" ]; then
    echo "❌ Error: .env file not found in project root"
    echo "   Expected location: /path/to/bookwise/.env"
    exit 1
fi

# Create logs directory
mkdir -p ~/Library/Logs
touch ~/Library/Logs/bookwise-librarian.log
touch ~/Library/Logs/bookwise-librarian-error.log

# Load the service
echo "📋 Loading service into launchd..."
launchctl unload ~/Library/LaunchAgents/com.bookwise.librarian.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.bookwise.librarian.plist

sleep 2

# Check status
if launchctl list | grep -q "com.bookwise.librarian"; then
    echo ""
    echo "✅ Service installed and started!"
    echo ""
    echo "📊 Service Info:"
    echo "   Name: com.bookwise.librarian"
    echo "   URL: http://localhost:8766"
    echo "   Logs: ~/Library/Logs/bookwise-librarian.log"
    echo "   Errors: ~/Library/Logs/bookwise-librarian-error.log"
    echo ""
    echo "📝 Useful Commands:"
    echo "   View status:  launchctl list | grep bookwise"
    echo "   View logs:    tail -f ~/Library/Logs/bookwise-librarian.log"
    echo "   Stop service: launchctl unload ~/Library/LaunchAgents/com.bookwise.librarian.plist"
    echo "   Start again:  launchctl load ~/Library/LaunchAgents/com.bookwise.librarian.plist"
    echo "   Restart:      launchctl kickstart -k gui/$(id -u)/com.bookwise.librarian"
    echo ""
    
    # Wait a bit and test
    echo "⏳ Waiting for server to start..."
    sleep 3
    
    if curl -sf http://localhost:8766/health > /dev/null 2>&1; then
        echo ""
        echo "✅ Server is healthy and responding!"
        curl -s http://localhost:8766/health | python -m json.tool
    else
        echo ""
        echo "⚠️  Server may still be starting. Check logs:"
        echo "   tail -f ~/Library/Logs/bookwise-librarian.log"
    fi
else
    echo ""
    echo "❌ Failed to start service. Check logs:"
    echo "   tail ~/Library/Logs/bookwise-librarian-error.log"
    exit 1
fi

echo ""
echo "🎉 Service will auto-start on boot and auto-restart if it crashes!"

