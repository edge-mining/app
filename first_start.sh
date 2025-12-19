#!/usr/bin/env bash
set -e

# Move to repo root (directory of this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Initialize user_data structure and default files
./init_user_data.sh

# Build and start the application stack for the first time
# (builds images and starts containers in the background)
docker compose up -d --build
