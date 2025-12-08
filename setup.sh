#!/bin/bash
# Setup script for MemGPT

echo "=========================================="
echo "  MemGPT Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Create data directory
echo ""
echo "Creating data directory..."
mkdir -p data/chroma

# Check for API key
echo ""
echo "Checking for OpenAI API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "WARNING: OPENAI_API_KEY environment variable is not set."
    echo "Please set it before running MemGPT:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "Or create a .env file with:"
    echo "  OPENAI_API_KEY=your-api-key-here"
else
    echo "API key found!"
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run MemGPT:"
echo "  python main.py"
echo ""
echo "To run examples:"
echo "  python example.py"
echo ""
echo "For more information, see README.md"
echo ""
