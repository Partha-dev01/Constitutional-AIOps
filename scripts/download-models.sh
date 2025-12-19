#!/bin/bash
# Constitutional AIOps - Model Download Script
# Downloads Qwen3-4B and Qwen3-14B Q4_K_M quantized models

set -e

MODELS_DIR="${1:-./models}"
mkdir -p "$MODELS_DIR"

echo "=========================================="
echo "Constitutional AIOps - Model Downloader"
echo "=========================================="
echo ""
echo "Target directory: $MODELS_DIR"
echo ""

# Model URLs (Hugging Face)
# Note: Update these URLs when official Q4_K_M versions are available
FAST_MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
FAST_MODEL_FILE="qwen3-4b-q4_k_m.gguf"

REASONING_MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q4_k_m.gguf"
REASONING_MODEL_FILE="qwen3-14b-q4_k_m.gguf"

# Function to download with progress
download_model() {
    local url="$1"
    local output="$2"
    local name="$3"
    
    if [ -f "$MODELS_DIR/$output" ]; then
        echo "✓ $name already exists, skipping..."
        return 0
    fi
    
    echo "Downloading $name..."
    echo "  URL: $url"
    echo "  Output: $MODELS_DIR/$output"
    echo ""
    
    # Use wget or curl
    if command -v wget &> /dev/null; then
        wget --progress=bar:force:noscroll -O "$MODELS_DIR/$output" "$url"
    elif command -v curl &> /dev/null; then
        curl -L --progress-bar -o "$MODELS_DIR/$output" "$url"
    else
        echo "ERROR: Neither wget nor curl found. Please install one."
        exit 1
    fi
    
    echo "✓ $name downloaded successfully"
    echo ""
}

# Download Fast Agent model (Qwen3-4B)
echo "----------------------------------------"
echo "1/2: Fast Agent Model (Qwen3-4B Q4_K_M)"
echo "----------------------------------------"
echo "VRAM: ~2.5GB model + ~1GB KV cache = ~4GB"
echo ""
download_model "$FAST_MODEL_URL" "$FAST_MODEL_FILE" "Qwen3-4B Q4_K_M"

# Download Reasoning Agent model (Qwen3-14B)
echo "----------------------------------------"
echo "2/2: Reasoning Agent Model (Qwen3-14B Q4_K_M)"
echo "----------------------------------------"
echo "VRAM: ~9GB model + ~1.5GB KV cache = ~11GB"
echo ""
download_model "$REASONING_MODEL_URL" "$REASONING_MODEL_FILE" "Qwen3-14B Q4_K_M"

# Verify downloads
echo "=========================================="
echo "Verification"
echo "=========================================="

verify_model() {
    local file="$1"
    local min_size="$2"  # in MB
    local name="$3"
    
    if [ -f "$MODELS_DIR/$file" ]; then
        size=$(du -m "$MODELS_DIR/$file" | cut -f1)
        if [ "$size" -ge "$min_size" ]; then
            echo "✓ $name: ${size}MB (OK)"
        else
            echo "✗ $name: ${size}MB (Expected >=${min_size}MB - may be corrupted)"
        fi
    else
        echo "✗ $name: NOT FOUND"
    fi
}

verify_model "$FAST_MODEL_FILE" 2000 "Qwen3-4B Q4_K_M"
verify_model "$REASONING_MODEL_FILE" 8000 "Qwen3-14B Q4_K_M"

echo ""
echo "=========================================="
echo "Download Complete!"
echo "=========================================="
echo ""
echo "Models are ready in: $MODELS_DIR"
echo ""
echo "Total VRAM required: ~15GB (fits on 24GB L4/A10G)"
echo ""
echo "Next steps:"
echo "  1. Start llama-swap: docker-compose -f docker-compose.yml -f docker/docker-compose.gpu.yml up"
echo "  2. Verify endpoints:"
echo "     - Fast Agent: curl http://localhost:8081/health"
echo "     - Reasoning Agent: curl http://localhost:8082/health"
echo ""
