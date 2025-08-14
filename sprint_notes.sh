#!/bin/bash

# Sprint Release Notes Generator
# Generate release notes for all PRs associated with a specific sprint

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

echo -e "${BLUE}🏃 Sprint Release Notes Generator${NC}"
echo -e "${BLUE}===================================${NC}"

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

# Activate virtual environment and run the sprint script
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${GREEN}🚀 Starting sprint release notes generator...${NC}"
python sprint_release_notes.py

echo -e "${GREEN}✅ Done!${NC}"
