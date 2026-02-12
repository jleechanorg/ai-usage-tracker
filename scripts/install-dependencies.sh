#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script to install ccusage and ccusage-codex CLI tools

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AI Usage Tracker - Dependency Installation Script       ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if Node.js is installed
print_status "Checking for Node.js..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed!"
    echo ""
    echo "Please install Node.js first:"
    echo "  - macOS: brew install node"
    echo "  - Linux: Use your package manager (apt, yum, etc.)"
    echo "  - Windows: Download from https://nodejs.org"
    echo ""
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js ${NODE_VERSION} is installed"

# Check if npm is installed
print_status "Checking for npm..."
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed!"
    exit 1
fi

NPM_VERSION=$(npm --version)
print_success "npm ${NPM_VERSION} is installed"
echo ""

# Check if ccusage is already installed
print_status "Checking if ccusage is already installed..."
if command -v ccusage &> /dev/null; then
    CCUSAGE_VERSION=$(ccusage --version 2>&1 || echo "unknown")
    print_warning "ccusage is already installed (${CCUSAGE_VERSION})"
    echo ""
    read -p "Do you want to reinstall ccusage? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Reinstalling ccusage..."
        npm install -g ccusage
        print_success "ccusage reinstalled successfully"
    else
        print_status "Skipping ccusage installation"
    fi
else
    print_status "Installing ccusage..."
    npm install -g ccusage
    print_success "ccusage installed successfully"
fi
echo ""

# Check if ccusage-codex is already installed
print_status "Checking if ccusage-codex is already installed..."
if command -v ccusage-codex &> /dev/null; then
    CCUSAGE_CODEX_VERSION=$(ccusage-codex --version 2>&1 || echo "unknown")
    print_warning "ccusage-codex is already installed (${CCUSAGE_CODEX_VERSION})"
    echo ""
    read -p "Do you want to reinstall ccusage-codex? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Reinstalling ccusage-codex..."
        npm install -g ccusage-codex
        print_success "ccusage-codex reinstalled successfully"
    else
        print_status "Skipping ccusage-codex installation"
    fi
else
    print_status "Installing ccusage-codex..."
    npm install -g ccusage-codex
    print_success "ccusage-codex installed successfully"
fi
echo ""

# Verify installations
print_status "Verifying installations..."
echo ""

if command -v ccusage &> /dev/null; then
    CCUSAGE_LOCATION=$(which ccusage)
    CCUSAGE_VERSION=$(ccusage --version 2>&1 || echo "unknown")
    print_success "ccusage is installed at: ${CCUSAGE_LOCATION}"
    echo "   Version: ${CCUSAGE_VERSION}"
else
    print_error "ccusage installation failed!"
    exit 1
fi

echo ""

if command -v ccusage-codex &> /dev/null; then
    CCUSAGE_CODEX_LOCATION=$(which ccusage-codex)
    CCUSAGE_CODEX_VERSION=$(ccusage-codex --version 2>&1 || echo "unknown")
    print_success "ccusage-codex is installed at: ${CCUSAGE_CODEX_LOCATION}"
    echo "   Version: ${CCUSAGE_CODEX_VERSION}"
else
    print_error "ccusage-codex installation failed!"
    exit 1
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation Complete!                                   ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "You can now run the combined usage report:"
echo "  python3 scripts/combined-usage-report.py"
echo ""
echo "Or test the individual tools:"
echo "  ccusage daily"
echo "  ccusage-codex daily"
echo ""
