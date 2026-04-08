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

echo -e "${CYAN}${BOLD}============================================${NC}"
echo -e "${CYAN}${BOLD}  Edge Mining — First Start${NC}"
echo -e "${CYAN}${BOLD}============================================${NC}"
echo ""

# Initialize user_data structure and default files
echo -e "${YELLOW}>> Initializing user data...${NC}"
./init_user_data.sh

echo ""
echo -e "${BOLD}This will build the Docker images and start the application.${NC}"
read -rp "Do you want to continue? [Y/n] " CONFIRM

if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
    echo -e "${RED}Operation cancelled.${NC}"
    exit 0
fi

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

# Build and start the application stack for the first time
# (builds images and starts containers in the background)
echo -e "${YELLOW}>> Building and starting the application...${NC}"
docker compose up -d --build

echo ""
echo -e "${GREEN}${BOLD}============================================${NC}"
echo -e "${GREEN}${BOLD}  First start completed!${NC}"
echo -e "${GREEN}${BOLD}============================================${NC}"
