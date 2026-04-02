#!/usr/bin/env bash
set -e

# Move to repo root (directory of this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "============================================"
echo "  Edge Mining — Update"
echo "============================================"
echo ""
echo "Current branch: $BRANCH"
echo ""

# Pull latest changes (with submodule update)
echo ">> Pulling latest changes..."
git pull --recurse-submodules

# Ensure submodules are in sync with the commit recorded in the superproject
echo ">> Updating submodules..."
git submodule update --init --recursive

# Initialize user_data structure and default files
echo ">> Initializing user data..."
./init_user_data.sh

# Rebuild and restart the application stack
echo ">> Rebuilding and restarting the application..."
docker compose up -d --build

echo ""
echo "============================================"
echo "  Update completed!"
echo "============================================"
