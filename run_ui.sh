#!/bin/bash

# Procurement Workflow UI Launcher
# Run this script from the project root with venv activated

set -e

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Error: Virtual environment not activated!"
    echo ""
    echo "Please activate your virtual environment first:"
    echo "  source venv/bin/activate"
    echo ""
    echo "Then run this script again:"
    echo "  ./run_ui.sh"
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Error: Streamlit not installed!"
    echo ""
    echo "Install it with:"
    echo "  pip install streamlit pandas"
    exit 1
fi

echo "✅ Streamlit found"

# Check if the app file exists
APP_FILE="src/ui/workflow_app.py"
if [[ ! -f "$APP_FILE" ]]; then
    echo "❌ Error: App file not found at $APP_FILE"
    echo ""
    echo "Make sure you're running this from the project root directory."
    exit 1
fi

echo "✅ App file found"
echo ""
echo "🚀 Starting Procurement Workflow UI..."
echo "   Open http://localhost:8501 in your browser"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

# Run streamlit
streamlit run "$APP_FILE" --server.port 8501

