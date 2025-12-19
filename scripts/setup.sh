#!/bin/bash
# Constitutional AIOps - Setup Script
# Initializes the development environment

set -e

echo "=========================================="
echo "Constitutional AIOps - Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 found"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

echo "Checking prerequisites..."
echo ""

MISSING=0

check_command python3 || MISSING=1
check_command pip3 || MISSING=1
check_command node || MISSING=1
check_command npm || MISSING=1
check_command docker || MISSING=1
check_command docker-compose || echo -e "${YELLOW}!${NC} docker-compose not found (may use 'docker compose' instead)"

if [ $MISSING -eq 1 ]; then
    echo ""
    echo -e "${RED}Missing prerequisites. Please install them first.${NC}"
    exit 1
fi

echo ""

# Python version check
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(echo "$PYTHON_VERSION >= 3.11" | bc)" -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION (>= 3.11 required)"
else
    echo -e "${RED}✗${NC} Python $PYTHON_VERSION (>= 3.11 required)"
    exit 1
fi

# Node version check
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -ge 20 ]; then
    echo -e "${GREEN}✓${NC} Node.js v$NODE_VERSION (>= 20 required)"
else
    echo -e "${RED}✗${NC} Node.js v$NODE_VERSION (>= 20 required)"
    exit 1
fi

echo ""
echo "----------------------------------------"
echo "Setting up Python environment..."
echo "----------------------------------------"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install dev dependencies
if [ -f "requirements-dev.txt" ]; then
    echo "Installing dev dependencies..."
    pip install -r requirements-dev.txt
fi

# Install package in editable mode
pip install -e .

echo ""
echo "----------------------------------------"
echo "Setting up Node.js environment..."
echo "----------------------------------------"

# Setup frontend
if [ -d "frontend" ]; then
    cd frontend
    echo "Installing Node.js dependencies..."
    npm install
    cd ..
fi

echo ""
echo "----------------------------------------"
echo "Setting up configuration..."
echo "----------------------------------------"

# Copy environment file if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}!${NC} Please edit .env with your settings"
fi

# Create models directory
mkdir -p models

# Create logs directory
mkdir -p logs

echo ""
echo "----------------------------------------"
echo "Setting up pre-commit hooks..."
echo "----------------------------------------"

# Setup pre-commit if available
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}✓${NC} Pre-commit hooks installed"
else
    echo -e "${YELLOW}!${NC} pre-commit not found, skipping hooks setup"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Edit configuration:"
echo "   nano .env"
echo ""
echo "3. Download models (requires ~12GB):"
echo "   ./scripts/download-models.sh"
echo ""
echo "4. Start local development (no GPU):"
echo "   docker-compose -f docker-compose.yml -f docker/docker-compose.local.yml up"
echo ""
echo "5. Start with GPU:"
echo "   docker-compose -f docker-compose.yml -f docker/docker-compose.gpu.yml up"
echo ""
echo "6. Run tests:"
echo "   pytest tests/ -v"
echo ""
