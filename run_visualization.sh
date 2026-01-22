#!/bin/bash

# METAR Wind Data Visualization Runner
# This script fetches data and opens the visualization

echo "🌬️  La Gomera Airport Wind Data Visualization"
echo "=============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import requests" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -q -r requirements.txt
fi

# Fetch METAR data
echo "📡 Fetching METAR data from Aviation Weather Center..."
python export_wind_data.py 2>/dev/null | grep -E "(Fetching|Found|Aggregating|Exported|complete)"

echo ""
echo "🌐 Starting local web server..."

# Kill any existing server on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Start HTTP server in background
python3 -m http.server 8000 > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 1

echo "✅ Server started (PID: $SERVER_PID)"
echo ""
echo "🚀 Opening visualization in browser..."
echo "   URL: http://localhost:8000/wind_visualization.html"
echo ""

# Open browser
if command -v open &> /dev/null; then
    # macOS
    open http://localhost:8000/wind_visualization.html
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:8000/wind_visualization.html
elif command -v start &> /dev/null; then
    # Windows
    start http://localhost:8000/wind_visualization.html
else
    echo "Please open this URL in your browser:"
    echo "http://localhost:8000/wind_visualization.html"
fi

echo ""
echo "💡 Tips:"
echo "   - The server is running on http://localhost:8000"
echo "   - Press Ctrl+C to stop the server when done"
echo "   - Run this script again to refresh data"
echo ""
echo "Press Ctrl+C to stop the server..."

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping server...'; kill $SERVER_PID 2>/dev/null; echo '✅ Server stopped. Goodbye!'; exit 0" INT

# Keep script running
wait $SERVER_PID
