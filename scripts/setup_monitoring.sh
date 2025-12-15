#!/bin/bash
# Setup script for periodic trading monitoring

echo "🤖 Setting up periodic trading monitoring"

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/.venv/bin/python"

echo "Project directory: $SCRIPT_DIR"

# Create a wrapper script that ensures proper environment
cat > "$SCRIPT_DIR/run_trader.sh" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
source .venv/bin/activate
export PATH="$SCRIPT_DIR/.venv/bin:\$PATH"
$PYTHON_PATH -m trading_algorithm.live_trader >> "$SCRIPT_DIR/trading.log" 2>&1
EOF

chmod +x "$SCRIPT_DIR/run_trader.sh"

echo "✅ Created run_trader.sh wrapper"

# Create log rotation script
cat > "$SCRIPT_DIR/rotate_logs.sh" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
if [ -f trading.log ] && [ \$(wc -l < trading.log) -gt 1000 ]; then
    mv trading.log "trading_\$(date +%Y%m%d_%H%M%S).log"
    touch trading.log
fi
EOF

chmod +x "$SCRIPT_DIR/rotate_logs.sh"

echo "✅ Created log rotation script"

# Show cron job instructions
echo ""
echo "📅 To set up automatic monitoring, add this to your crontab:"
echo "   Run: crontab -e"
echo "   Add these lines:"
echo ""
echo "# Trading algorithm - runs every 30 minutes during market hours (9:30 AM - 4 PM ET)"
echo "*/30 9-16 * * 1-5 $SCRIPT_DIR/run_trader.sh"
echo ""
echo "# Log rotation - daily at 6 AM"
echo "0 6 * * * $SCRIPT_DIR/rotate_logs.sh"
echo ""
echo "💡 Market hours: Mon-Fri, 9:30 AM - 4:00 PM ET"
echo "📝 Logs will be saved to: $SCRIPT_DIR/trading.log"
echo ""
echo "To test manually: $SCRIPT_DIR/run_trader.sh"