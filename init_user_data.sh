#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_DIR="$ROOT_DIR/core"
USER_DATA_DIR="$ROOT_DIR/user_data"

mkdir -p "$USER_DATA_DIR"
mkdir -p "$USER_DATA_DIR/optimization_policies"

# Copy optimization_policies only if missing
if [ -d "$CORE_DIR/optimization_policies" ]; then
  if [ ! -d "$USER_DATA_DIR/optimization_policies" ] || [ -z "$(ls -A "$USER_DATA_DIR/optimization_policies" 2>/dev/null)" ]; then
    cp -r "$CORE_DIR/optimization_policies/"* "$USER_DATA_DIR/optimization_policies"/ || true
  fi
fi

# Handle edgemining.db
# If a pre-existing database exists under core/, copy it once.
# Otherwise, create an empty file in user_data so the app can initialize it.
if [ -f "$CORE_DIR/edgemining.db" ]; then
  if [ ! -f "$USER_DATA_DIR/edgemining.db" ]; then
    cp "$CORE_DIR/edgemining.db" "$USER_DATA_DIR/edgemining.db"
  fi
else
  if [ ! -f "$USER_DATA_DIR/edgemining.db" ]; then
    touch "$USER_DATA_DIR/edgemining.db"
  fi
fi
