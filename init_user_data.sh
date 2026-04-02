#!/usr/bin/env bash
set -e

# Colors
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
DIM='\033[2m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_CORE_DIR="$ROOT_DIR/core"
APP_CORE_DATA_DIR="$APP_CORE_DIR/data"
APP_USER_DATA_DIR="$ROOT_DIR/user_data"

echo -e "${YELLOW}>> Setting up user_data directory...${NC}"

mkdir -p "$APP_USER_DATA_DIR"
mkdir -p "$APP_USER_DATA_DIR/policies"
mkdir -p "$APP_USER_DATA_DIR/examples"
mkdir -p "$APP_USER_DATA_DIR/db"
echo -e "   ${DIM}Created directory structure${NC}"

# Copy policies only if missing
if [ -d "$APP_CORE_DATA_DIR/policies" ]; then
  if [ ! -d "$APP_USER_DATA_DIR/policies" ] || [ -z "$(ls -A "$APP_USER_DATA_DIR/policies" 2>/dev/null)" ]; then
    cp -r "$APP_CORE_DATA_DIR/policies/"* "$APP_USER_DATA_DIR/policies"/ || true
    echo -e "   ${DIM}Copied default policies${NC}"
  else
    echo -e "   ${DIM}Policies already present, skipping${NC}"
  fi
fi

# Copy examples only if missing
if [ -d "$APP_CORE_DATA_DIR/examples" ]; then
  if [ ! -d "$APP_USER_DATA_DIR/examples" ] || [ -z "$(ls -A "$APP_USER_DATA_DIR/examples" 2>/dev/null)" ]; then
    cp -r "$APP_CORE_DATA_DIR/examples/"* "$APP_USER_DATA_DIR/examples"/ || true
    echo -e "   ${DIM}Copied example files${NC}"
  else
    echo -e "   ${DIM}Examples already present, skipping${NC}"
  fi
fi

# Handle edgemining.db
# If a pre-existing database exists under core/, copy it once.
# Otherwise, create an empty file in user_data (only if it doesn't exist) so the app can initialize it.
if [ -f "$APP_CORE_DATA_DIR/db/edgemining.db" ]; then
  if [ ! -f "$APP_USER_DATA_DIR/db/edgemining.db" ]; then
    cp "$APP_CORE_DATA_DIR/db/edgemining.db" "$APP_USER_DATA_DIR/db/edgemining.db"
    echo -e "   ${DIM}Copied existing database${NC}"
  else
    echo -e "   ${DIM}Database already present, skipping${NC}"
  fi
else
  if [ ! -f "$APP_USER_DATA_DIR/db/edgemining.db" ]; then
    touch "$APP_USER_DATA_DIR/db/edgemining.db"
    echo -e "   ${DIM}Created empty database${NC}"
  else
    echo -e "   ${DIM}Database already present, skipping${NC}"
  fi
fi

echo -e "${GREEN}   User data ready.${NC}"
