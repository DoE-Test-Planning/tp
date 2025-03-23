#!/bin/bash
# Script to install git hooks for the Test Planning Helper project

# Find the Git hooks directory
REPO_ROOT=$(git rev-parse --show-toplevel)
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"
HOOKS_SOURCE_DIR="$REPO_ROOT/backend/dev_scripts/git_hooks"

# Check if Git hooks directory exists
if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo "Error: Git hooks directory not found at $GIT_HOOKS_DIR"
    echo "Make sure you're in a Git repository."
    exit 1
fi

# Check if our hooks source directory exists
if [ ! -d "$HOOKS_SOURCE_DIR" ]; then
    echo "Error: Hooks source directory not found at $HOOKS_SOURCE_DIR"
    exit 1
fi

# Install pre-commit hook
if [ -f "$HOOKS_SOURCE_DIR/pre-commit" ]; then
    echo "Installing pre-commit hook..."
    cp "$HOOKS_SOURCE_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_DIR/pre-commit"
    echo "Pre-commit hook installed successfully."
else
    echo "Error: pre-commit hook not found in source directory."
fi

# Install other hooks here if needed in the future...

echo "Git hooks installation complete!" 