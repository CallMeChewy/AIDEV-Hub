#!/bin/bash
# File: remove-venv.sh
# Path: AIDEV-Hub/remove-venv.sh
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  3:45PM
# Description: Script to remove .venv directory from Git tracking

echo "Removing .venv directory from Git tracking (keeping the directory on disk)..."

# First ensure .venv is in .gitignore
if ! grep -q "^\.venv/" .gitignore; then
    echo "Adding .venv/ to .gitignore..."
    echo -e "\n# Python virtual environment\n.venv/" >> .gitignore
    echo ".venv/ added to .gitignore"
fi

# Remove .venv from Git tracking without deleting it from disk
echo "Removing .venv from Git tracking..."
git rm -r --cached .venv/

echo "The .venv directory has been removed from Git tracking but kept on your filesystem."
echo "Commit these changes with:"
echo "  git commit -m \"Remove .venv directory from version control\""
echo "  git push"
