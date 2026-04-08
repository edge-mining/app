#!/usr/bin/env bash
set -e

# Colors
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Move to repo root (directory of this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo -e "${CYAN}${BOLD}============================================${NC}"
echo -e "${CYAN}${BOLD}  Edge Mining — Update${NC}"
echo -e "${CYAN}${BOLD}============================================${NC}"
echo ""
echo -e "Current branch: ${BOLD}$BRANCH${NC}"
echo ""

# Check if containers are running and stop them
echo -e "${YELLOW}>> Checking for running containers...${NC}"
RUNNING_CONTAINERS=$(docker compose ps --services --filter "status=running" 2>/dev/null || true)

if [ -n "$RUNNING_CONTAINERS" ]; then
    echo -e "${YELLOW}${BOLD}⚠ Running containers detected:${NC}"
    echo "$RUNNING_CONTAINERS"
    echo ""
    echo -e "${YELLOW}${BOLD}>> Stopping containers...${NC}"
    docker compose down
    echo -e "${GREEN}✓ Containers stopped successfully${NC}"
    echo ""
fi

# Pull latest changes and update submodules (--init handles newly added submodules)
echo -e "${YELLOW}>> Pulling latest changes...${NC}"
git pull
echo -e "${YELLOW}>> Updating submodules...${NC}"
git submodule update --init --recursive

# Initialize user_data structure and default files
echo -e "${YELLOW}>> Initializing user data...${NC}"
./init_user_data.sh

echo ""
echo -e "${BOLD}Do you want to rebuild and restart the Docker application? (recommended)${NC}"
read -rp "Rebuild and restart? [Y/n] " CONFIRM

if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
    echo ""
    echo -e "${YELLOW}Note: the Docker image may have changed with this update.${NC}"
    echo -e "${YELLOW}To rebuild and restart manually, run:${NC}"
    echo ""
    echo -e "  ${BOLD}docker compose up -d --build${NC}"
    echo ""
    echo -e "${GREEN}${BOLD}============================================${NC}"
    echo -e "${GREEN}${BOLD}  Update completed (without rebuild).${NC}"
    echo -e "${GREEN}${BOLD}============================================${NC}"
    exit 0
fi

# Rebuild and restart the application stack
echo ""
echo -e "${YELLOW}>> Rebuilding and restarting the application...${NC}"
docker compose up -d --build

echo ""
echo -e "${GREEN}${BOLD}============================================${NC}"
echo -e "${GREEN}${BOLD}  Update completed!${NC}"
echo -e "${GREEN}${BOLD}============================================${NC}"
