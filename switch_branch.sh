#!/usr/bin/env bash
set -e

# Move to repo root (directory of this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "============================================"
echo "  Edge Mining — Switch Branch"
echo "============================================"
echo ""
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Fetch latest remote info
echo ">> Fetching available branches..."
git fetch --all --prune --quiet

# List remote branches (excluding HEAD pointer)
BRANCHES=()
while IFS= read -r line; do
    BRANCHES+=("$line")
done < <(git branch -r --list 'origin/*' | grep -v 'HEAD' | sed 's|origin/||' | sed 's/^[[:space:]]*//')

if [ ${#BRANCHES[@]} -eq 0 ]; then
    echo "No remote branches found."
    exit 1
fi

echo ""
echo "Available branches:"
echo "--------------------------------------------"
for i in "${!BRANCHES[@]}"; do
    MARKER="  "
    if [ "${BRANCHES[$i]}" = "$CURRENT_BRANCH" ]; then
        MARKER="* "
    fi
    echo "  $((i+1))) ${MARKER}${BRANCHES[$i]}"
done
echo "--------------------------------------------"
echo ""

# Ask user to choose
read -rp "Select branch number (or press Enter to cancel): " CHOICE

if [ -z "$CHOICE" ]; then
    echo "Operation cancelled."
    exit 0
fi

# Validate input
if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt ${#BRANCHES[@]} ]; then
    echo "Invalid selection."
    exit 1
fi

TARGET_BRANCH="${BRANCHES[$((CHOICE-1))]}"

if [ "$TARGET_BRANCH" = "$CURRENT_BRANCH" ]; then
    echo "Already on branch '$CURRENT_BRANCH'. No changes needed."
    exit 0
fi

echo ""
echo ">> Switching to branch '$TARGET_BRANCH'..."

# Switch branch with submodule update
git switch "$TARGET_BRANCH" --recurse-submodules

# Ensure submodules are fully in sync
git submodule update --init --recursive

# Initialize user_data structure and default files
echo ">> Initializing user data..."
./init_user_data.sh

# Rebuild and restart the application stack
echo ">> Rebuilding and restarting the application..."
docker compose up -d --build

echo ""
echo "============================================"
echo "  Switched to branch '$TARGET_BRANCH'!"
echo "  Application restarted."
echo "============================================"
