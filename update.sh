#!/bin/bash
#
# update.sh - Automatically pull new version files from the repository
# This script updates the x11stream repository to the latest version
#

set -e  # Exit on error
set -u  # Exit on undefined variables
set -o pipefail  # Catch errors in pipelines

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}x11stream Repository Update Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're in a git repository
if [ ! -d "$SCRIPT_DIR/.git" ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    echo "This script must be run from the x11stream repository directory"
    exit 1
fi

# Change to repository directory
cd "$SCRIPT_DIR"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${YELLOW}Warning: You have uncommitted changes in the repository${NC}"
    echo ""
    git status --short
    echo ""
    read -p "Do you want to continue and potentially lose these changes? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Update cancelled${NC}"
        exit 0
    fi
    
    # Stash changes
    echo -e "${BLUE}Stashing local changes...${NC}"
    git stash push -m "Auto-stash before update on $(date)"
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}Current branch: ${GREEN}$CURRENT_BRANCH${NC}"

# Fetch latest changes
echo -e "${BLUE}Fetching latest changes from remote...${NC}"
git fetch origin

# Check if there are updates available
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
BASE=$(git merge-base @ @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo -e "${YELLOW}Warning: No upstream branch configured${NC}"
    echo "Attempting to pull from origin/$CURRENT_BRANCH..."
    REMOTE=$(git rev-parse "origin/$CURRENT_BRANCH" 2>/dev/null || echo "")
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✓ Already up to date${NC}"
    exit 0
elif [ "$LOCAL" = "$BASE" ]; then
    echo -e "${BLUE}Updates available. Pulling changes...${NC}"
    git pull origin "$CURRENT_BRANCH"
    echo -e "${GREEN}✓ Repository updated successfully${NC}"
    
    # Check if requirements.txt was updated
    if git diff --name-only HEAD@{1} HEAD | grep -q "requirements.txt"; then
        echo ""
        echo -e "${YELLOW}Note: requirements.txt was updated${NC}"
        echo "You may want to update your Python dependencies:"
        echo "  pip3 install --user -r requirements.txt"
    fi
    
    # Check if services were updated
    if git diff --name-only HEAD@{1} HEAD | grep -q "\.service$"; then
        echo ""
        echo -e "${YELLOW}Note: Service files were updated${NC}"
        echo "You may want to reload systemd services:"
        echo "  sudo systemctl daemon-reload"
        echo "  sudo systemctl restart x11stream.service"
        echo "  sudo systemctl restart oled_display.service"
    fi
    
    echo ""
    echo -e "${GREEN}Update completed successfully!${NC}"
elif [ "$REMOTE" = "$BASE" ]; then
    echo -e "${YELLOW}Warning: Local branch is ahead of remote${NC}"
    echo "No update needed"
    exit 0
else
    echo -e "${RED}Error: Local and remote branches have diverged${NC}"
    echo "Please resolve conflicts manually"
    exit 1
fi
