#!/bin/bash

# AI Release Notes Generator - Simple launcher script
# Usage: ./generate_release_notes.sh <PR_URL> [options]

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if PR URL is provided
if [ $# -eq 0 ]; then
    echo "❌ No PR URL provided."
    echo "Usage: $0 <PR_URL> [options]"
    echo "Example: $0 https://github.com/owner/repo/pull/123 --style brief"
    exit 1
fi

# Run the Python script with the virtual environment
./venv/bin/python main.py "$@"
