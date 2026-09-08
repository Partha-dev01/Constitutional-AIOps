#!/bin/bash
#
# Constitutional AIOps - Installation Wizard
#
# One-command setup for Constitutional AIOps system.
# Supports both GPU (AWS g6.xlarge) and CPU-only (local dev) deployments.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/your-repo/constitutional-aiops/main/scripts/install.sh | bash
#   OR
#   ./scripts/install.sh [--gpu|--local|--help]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/your-repo/constitutional-aiops"
MIN_DOCKER_VERSION="20.10"
MIN_MEMORY_GB=8
MIN_GPU_MEMORY_GB=20

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║           Constitutional AIOps - Installation Wizard          ║"
    echo "║         Autonomous Infrastructure with Constitutional AI      ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print step
print_step() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Print warning
print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Print error
print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Print info
print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get system memory in GB
get_memory_gb() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        free -g | awk '/^Mem:/{print $2}'
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}'
    else
        echo "8" # Default assumption
    fi
}

# Check for NVIDIA GPU
check_nvidia_gpu() {
    if command_exists nvidia-smi; then
        nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1
    else
        echo "0"
    fi
}

# Check Docker version
check_docker_version() {
    if command_exists docker; then
        docker --version | awk '{print $3}' | tr -d ','
    else
        echo "0"
    fi
}

# Version comparison
version_gte() {
    printf '%s\n%s' "$2" "$1" | sort -V -C
}

# Hardware detection
detect_hardware() {
    print_info "Detecting hardware configuration..."

    # Memory
    MEMORY_GB=$(get_memory_gb)
    print_step "System memory: ${MEMORY_GB}GB"

    # GPU
    GPU_MEMORY=$(check_nvidia_gpu)
    if [ "$GPU_MEMORY" != "0" ] && [ -n "$GPU_MEMORY" ]; then
        GPU_MEMORY_GB=$((GPU_MEMORY / 1024))
        print_step "NVIDIA GPU detected: ${GPU_MEMORY_GB}GB VRAM"
        HAS_GPU=true

        # Check for NVIDIA Container Toolkit
        if docker info 2>/dev/null | grep -q "nvidia"; then
            print_step "NVIDIA Container Toolkit: installed"
            NVIDIA_TOOLKIT=true
        else
            print_warning "NVIDIA Container Toolkit: not detected"
            NVIDIA_TOOLKIT=false
        fi
    else
        print_info "No NVIDIA GPU detected"
        HAS_GPU=false
        GPU_MEMORY_GB=0
    fi

    # CPU
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        CPU_CORES=$(nproc)
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        CPU_CORES=$(sysctl -n hw.ncpu)
    else
        CPU_CORES=4
    fi
    print_step "CPU cores: $CPU_CORES"

    # Recommend deployment mode
    if [ "$HAS_GPU" = true ] && [ "$GPU_MEMORY_GB" -ge "$MIN_GPU_MEMORY_GB" ] && [ "$NVIDIA_TOOLKIT" = true ]; then
        RECOMMENDED_MODE="gpu"
        print_step "Recommended deployment: GPU (full LLM capabilities)"
    else
        RECOMMENDED_MODE="local"
        print_step "Recommended deployment: Local (mock LLM server)"
    fi
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    PREREQS_MET=true

    # Docker
    if command_exists docker; then
        DOCKER_VERSION=$(check_docker_version)
        if version_gte "$DOCKER_VERSION" "$MIN_DOCKER_VERSION"; then
            print_step "Docker: $DOCKER_VERSION"
        else
            print_error "Docker version $DOCKER_VERSION is too old (need >= $MIN_DOCKER_VERSION)"
            PREREQS_MET=false
        fi
    else
        print_error "Docker: not installed"
        PREREQS_MET=false
    fi

    # Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        if docker compose version >/dev/null 2>&1; then
            print_step "Docker Compose: $(docker compose version --short)"
        else
            print_step "Docker Compose: $(docker-compose --version | awk '{print $3}' | tr -d ',')"
        fi
    else
        print_error "Docker Compose: not installed"
        PREREQS_MET=false
    fi

    # Git
    if command_exists git; then
        print_step "Git: $(git --version | awk '{print $3}')"
    else
        print_warning "Git: not installed (optional, needed for updates)"
    fi

    # curl
    if command_exists curl; then
        print_step "curl: available"
    else
        print_error "curl: not installed"
        PREREQS_MET=false
    fi

    # Memory check
    MEMORY_GB=$(get_memory_gb)
    if [ "$MEMORY_GB" -ge "$MIN_MEMORY_GB" ]; then
        print_step "Memory: ${MEMORY_GB}GB (minimum: ${MIN_MEMORY_GB}GB)"
    else
        print_warning "Memory: ${MEMORY_GB}GB (recommended: ${MIN_MEMORY_GB}GB+)"
    fi

    if [ "$PREREQS_MET" = false ]; then
        print_error "Prerequisites not met. Please install missing dependencies."
        exit 1
    fi
}

# Create environment file
create_env_file() {
    print_info "Creating environment configuration..."

    if [ -f ".env" ]; then
        print_warning ".env file already exists, backing up to .env.backup"
        cp .env .env.backup
    fi

    cat > .env << EOF
# Constitutional AIOps - Environment Configuration
# Generated by install.sh on $(date)

# Deployment Mode: gpu | local
DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-$RECOMMENDED_MODE}

# Neo4j Configuration (set NEO4J_PASSWORD in your shell to override the default)
NEO4J_PASSWORD=${NEO4J_PASSWORD:-changeme_neo4j_password}

# Grafana Configuration
GRAFANA_PASSWORD=admin

# LLM Configuration (GPU mode only)
FAST_AGENT_URL=http://llama-swap:8081/v1
REASONING_AGENT_URL=http://llama-swap:8082/v1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Frontend Configuration
VITE_API_URL=http://localhost:8000
EOF

    print_step "Environment file created: .env"
}

# Download models (GPU mode only)
download_models() {
    if [ "$DEPLOYMENT_MODE" != "gpu" ]; then
        return
    fi

    print_info "Checking LLM models..."

    mkdir -p models

    # Check if models already exist
    if [ -f "models/qwen3-4b-q4_k_m.gguf" ] && [ -f "models/qwen3-14b-q4_k_m.gguf" ]; then
        print_step "Models already downloaded"
        return
    fi

    print_info "Downloading LLM models (this may take a while)..."

    # Download Qwen3-4B
    if [ ! -f "models/qwen3-4b-q4_k_m.gguf" ]; then
        print_info "Downloading Qwen3-4B Q4_K_M (~2.5GB)..."
        curl -L -o models/qwen3-4b-q4_k_m.gguf \
            "https://huggingface.co/Qwen/Qwen2.5-4B-Instruct-GGUF/resolve/main/qwen2.5-4b-instruct-q4_k_m.gguf" || {
            print_warning "Failed to download Qwen3-4B. You may need to download manually."
        }
    fi

    # Download Qwen3-14B
    if [ ! -f "models/qwen3-14b-q4_k_m.gguf" ]; then
        print_info "Downloading Qwen3-14B Q4_K_M (~9GB)..."
        curl -L -o models/qwen3-14b-q4_k_m.gguf \
            "https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q4_k_m.gguf" || {
            print_warning "Failed to download Qwen3-14B. You may need to download manually."
        }
    fi

    print_step "Model download complete"
}

# Start services
start_services() {
    print_info "Starting Constitutional AIOps services..."

    if [ "$DEPLOYMENT_MODE" = "gpu" ]; then
        print_info "Starting in GPU mode (with LLM inference)..."
        docker compose -f docker-compose.yml -f docker/docker-compose.gpu.yml up -d
    else
        print_info "Starting in local mode (mock LLM server)..."
        docker compose -f docker-compose.yml -f docker/docker-compose.local.yml up -d
    fi

    print_step "Services starting..."
}

# Wait for services
wait_for_services() {
    print_info "Waiting for services to be ready..."

    # Wait for backend
    echo -n "  Waiting for backend"
    for i in {1..60}; do
        if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            echo ""
            print_step "Backend ready"
            break
        fi
        echo -n "."
        sleep 2
    done

    # Wait for frontend
    echo -n "  Waiting for frontend"
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo ""
            print_step "Frontend ready"
            break
        fi
        echo -n "."
        sleep 2
    done
}

# Print success message
print_success() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           Constitutional AIOps - Installation Complete!       ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Access points:"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend API:  http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo "  Grafana:      http://localhost:3001 (admin/admin)"
    echo "  Neo4j:        http://localhost:7474 (user neo4j; password = NEO4J_PASSWORD in .env)"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker compose logs -f"
    echo "  Stop:         docker compose down"
    echo "  Restart:      docker compose restart"
    echo ""
    if [ "$DEPLOYMENT_MODE" = "gpu" ]; then
        echo "LLM Endpoints:"
        echo "  Fast Agent:      http://localhost:8081/v1"
        echo "  Reasoning Agent: http://localhost:8082/v1"
    else
        echo -e "${YELLOW}Note: Running in local mode with mock LLM server.${NC}"
        echo "For full LLM capabilities, deploy on GPU-enabled hardware."
    fi
    echo ""
}

# Show help
show_help() {
    echo "Constitutional AIOps - Installation Wizard"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --gpu       Force GPU deployment mode"
    echo "  --local     Force local (CPU-only) deployment mode"
    echo "  --no-start  Configure only, don't start services"
    echo "  --help      Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DEPLOYMENT_MODE   Set to 'gpu' or 'local'"
    echo "  NEO4J_PASSWORD    Neo4j database password"
    echo "  GRAFANA_PASSWORD  Grafana admin password"
    echo ""
}

# Main installation flow
main() {
    # Parse arguments
    START_SERVICES=true
    while [[ $# -gt 0 ]]; do
        case $1 in
            --gpu)
                DEPLOYMENT_MODE="gpu"
                shift
                ;;
            --local)
                DEPLOYMENT_MODE="local"
                shift
                ;;
            --no-start)
                START_SERVICES=false
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    print_banner

    # Check prerequisites
    check_prerequisites
    echo ""

    # Detect hardware
    detect_hardware
    echo ""

    # Use detected mode if not specified
    DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-$RECOMMENDED_MODE}
    print_info "Deployment mode: $DEPLOYMENT_MODE"
    echo ""

    # Create environment file
    create_env_file
    echo ""

    # Download models for GPU mode
    if [ "$DEPLOYMENT_MODE" = "gpu" ]; then
        download_models
        echo ""
    fi

    # Start services
    if [ "$START_SERVICES" = true ]; then
        start_services
        echo ""

        wait_for_services
        echo ""

        print_success
    else
        print_info "Configuration complete. Run 'docker compose up -d' to start services."
    fi
}

# Run main
main "$@"
