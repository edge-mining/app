#!/usr/bin/env bash
set -e

# Colors
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Move to repo root (directory of this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo -e "${CYAN}${BOLD}============================================${NC}"
echo -e "${CYAN}${BOLD}  Edge Mining — Switch Branch${NC}"
echo -e "${CYAN}${BOLD}============================================${NC}"
echo ""
echo -e "Current branch: ${BOLD}$CURRENT_BRANCH${NC}"
echo ""

# Fetch latest remote info
echo -e "${YELLOW}>> Fetching available branches...${NC}"
git fetch --all --prune --quiet

# List remote branches (excluding HEAD pointer)
BRANCHES=()
while IFS= read -r line; do
    BRANCHES+=("$line")
done < <(git branch -r --list 'origin/*' | grep -v 'HEAD' | sed 's|origin/||' | sed 's/^[[:space:]]*//')

if [ ${#BRANCHES[@]} -eq 0 ]; then
    echo -e "${RED}No remote branches found.${NC}"
    exit 1
fi

echo ""
echo -e "${BOLD}Available branches:${NC}"
echo "--------------------------------------------"
for i in "${!BRANCHES[@]}"; do
    MARKER="  "
    SUFFIX=""
    if [ "${BRANCHES[$i]}" = "$CURRENT_BRANCH" ]; then
        MARKER="${GREEN}* "
        SUFFIX=" (current)"
    fi
    echo -e "  $((i+1))) ${MARKER}${BRANCHES[$i]}${SUFFIX}${NC}"
done
echo "--------------------------------------------"
echo ""

# Ask user to choose
read -rp "Select branch number (or press Enter to cancel): " CHOICE

if [ -z "$CHOICE" ]; then
    echo -e "${RED}Operation cancelled.${NC}"
    exit 0
fi

# Validate input
if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt ${#BRANCHES[@]} ]; then
    echo -e "${RED}Invalid selection.${NC}"
    exit 1
fi

TARGET_BRANCH="${BRANCHES[$((CHOICE-1))]}"

if [ "$TARGET_BRANCH" = "$CURRENT_BRANCH" ]; then
    echo -e "${YELLOW}Already on branch '$CURRENT_BRANCH'. No changes needed.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}>> Switching to branch '$TARGET_BRANCH'...${NC}"

# Switch branch with submodule update
git switch "$TARGET_BRANCH" --recurse-submodules

# Ensure submodules are fully in sync
git submodule update --init --recursive

# Initialize user_data structure and default files
echo -e "${YELLOW}>> Initializing user data...${NC}"
./init_user_data.sh

# Rebuild and restart the application stack
echo -e "${YELLOW}>> Rebuilding and restarting the application...${NC}"
docker compose up -d --build

echo ""
echo -e "${GREEN}${BOLD}============================================${NC}"
echo -e "${GREEN}${BOLD}  Switched to branch '$TARGET_BRANCH'!${NC}"
echo -e "${GREEN}${BOLD}  Application restarted.${NC}"
echo -e "${GREEN}${BOLD}============================================${NC}"
