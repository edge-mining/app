#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_CORE_DIR="$ROOT_DIR/core"
APP_CORE_DATA_DIR="$APP_CORE_DIR/data"
APP_USER_DATA_DIR="$ROOT_DIR/user_data"

mkdir -p "$APP_USER_DATA_DIR"
mkdir -p "$APP_USER_DATA_DIR/policies"
mkdir -p "$APP_USER_DATA_DIR/examples"
mkdir -p "$APP_USER_DATA_DIR/db"

# Copy policies only if missing
if [ -d "$APP_CORE_DATA_DIR/policies" ]; then
  if [ ! -d "$APP_USER_DATA_DIR/policies" ] || [ -z "$(ls -A "$APP_USER_DATA_DIR/policies" 2>/dev/null)" ]; then
    cp -r "$APP_CORE_DATA_DIR/policies/"* "$APP_USER_DATA_DIR/policies"/ || true
  fi
fi

# Copy examples only if missing
if [ -d "$APP_CORE_DATA_DIR/examples" ]; then
  if [ ! -d "$APP_USER_DATA_DIR/examples" ] || [ -z "$(ls -A "$APP_USER_DATA_DIR/examples" 2>/dev/null)" ]; then
    cp -r "$APP_CORE_DATA_DIR/examples/"* "$APP_USER_DATA_DIR/examples"/ || true
  fi
fi

# Handle edgemining.db
# If a pre-existing database exists under core/, copy it once.
# Otherwise, create an empty file in user_data so the app can initialize it.
if [ -f "$APP_CORE_DATA_DIR/db/edgemining.db" ]; then
  if [ ! -f "$APP_USER_DATA_DIR/db/edgemining.db" ]; then
    cp "$APP_CORE_DATA_DIR/db/edgemining.db" "$APP_USER_DATA_DIR/db/edgemining.db"
  fi
else
  if [ ! -f "$APP_USER_DATA_DIR/db/edgemining.db" ]; then
    touch "$APP_USER_DATA_DIR/db/edgemining.db"
  fi
fi
