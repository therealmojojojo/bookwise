#!/bin/bash
# Start the BookWise Librarian API server in DEVELOPMENT mode (with auto-reload)
# For production, use ./service-start.sh instead

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$DIR/../../.." && pwd )"

echo "📚 Starting BookWise Librarian API..."
echo "Project root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Please create .env file with required configuration"
    echo ""
fi

# Start the server
echo "Starting development server with auto-reload..."
echo "Press CTRL+C to stop"
echo ""
python -m uvicorn src.librarian.server:app \
    --host 0.0.0.0 \
    --port ${PORT:-8766} \
    --reload \
    --log-level info

# Note: --reload enables auto-restart on code changes (development mode)
# For production deployment, use ./service-start.sh instead

