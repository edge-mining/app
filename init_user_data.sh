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

# Copy edgemining.db only if missing
if [ -f "$CORE_DIR/edgemining.db" ] && [ ! -f "$USER_DATA_DIR/edgemining.db" ]; then
  cp "$CORE_DIR/edgemining.db" "$USER_DATA_DIR/edgemining.db"
fi
