#!/bin/bash

# JIRA Ticket Release Notes Generator
# Generate release notes from JIRA ticket(s) with optional GitHub PR enhancement

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

echo -e "${BLUE}🎫 JIRA Ticket Release Notes Generator${NC}"
echo -e "${BLUE}====================================${NC}"

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

# Check if JIRA is configured
if ! grep -q "JIRA_SERVER=" .env || ! grep -q "JIRA_USERNAME=" .env || ! grep -q "JIRA_API_TOKEN=" .env; then
    echo -e "${YELLOW}⚠️  JIRA not configured${NC}"
    echo "This script requires JIRA configuration. Please add to .env:"
    echo "  JIRA_SERVER=https://issues.redhat.com"
    echo "  JIRA_USERNAME=your.email@redhat.com"
    echo "  JIRA_API_TOKEN=your-api-token"
    exit 1
fi

# Activate virtual environment and run the JIRA ticket script
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${GREEN}🚀 Starting JIRA ticket release notes generator...${NC}"
python jira_ticket_release_notes.py

echo -e "${GREEN}✅ Done!${NC}"
