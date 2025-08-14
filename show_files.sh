#!/bin/bash

# Show All Files in PR
# Utility script to display all files changed in a pull request

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📁 Show All Files in PR${NC}"
echo -e "${BLUE}========================${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Please run: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Please create .env file with your API keys (see env.example)"
    exit 1
fi

# Activate virtual environment and run the show files script
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if PR URL is provided as argument
if [ $# -gt 0 ]; then
    echo -e "${GREEN}🚀 Showing files for: $1${NC}"
    python show_all_files.py "$1"
else
    echo -e "${GREEN}🚀 Starting show files utility...${NC}"
    python show_all_files.py
fi

echo -e "${GREEN}✅ Done!${NC}"
