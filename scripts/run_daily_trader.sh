#!/bin/bash
# Run the daily trading algorithm at market open

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d .venv ]; then
    source .venv/bin/activate
fi

# Run the daily trader
echo "=========================================="
echo "Running Daily Trading Algorithm"
echo "Time: $(date)"
echo "=========================================="

python -m trading_algorithm.daily_trader

echo ""
echo "Daily trading check completed at $(date)"
