#!/bin/bash
# Constitutional AIOps - Jarvis Labs Ollama Setup Script
#
# Run this ON the Jarvis Labs instance via SSH:
#   ssh -p [PORT] root@sshn.jarvislabs.ai 'bash -s' < scripts/setup-jarvis-ollama.sh
#
# Or copy and paste commands manually after SSH-ing in.

set -e

echo "=============================================="
echo "Constitutional AIOps - Jarvis Labs Setup"
echo "=============================================="
echo ""
echo "Models: Qwen3-4B (Fast) + Qwen3-14B (Reasoning)"
echo "Storage: /home/ollama-models (PERSISTS!)"
echo ""

# Check if Ollama is running
if ! command -v ollama &> /dev/null; then
    echo "ERROR: Ollama not found. Make sure you're using the Ollama template!"
    exit 1
fi

echo "Ollama detected. Setting up..."

# CRITICAL: Configure persistent model storage FIRST
echo ""
echo "=============================================="
echo "Step 0: Setting up persistent model storage"
echo "=============================================="
echo ""
echo "IMPORTANT: Only /home directory persists between pause/resume!"
echo ""

export OLLAMA_MODELS=/home/ollama-models
mkdir -p /home/ollama-models
echo "Models will be stored in: $OLLAMA_MODELS"

# Add to .bashrc for future sessions
if ! grep -q "OLLAMA_MODELS" ~/.bashrc 2>/dev/null; then
    echo 'export OLLAMA_MODELS=/home/ollama-models' >> ~/.bashrc
    echo "Added OLLAMA_MODELS to ~/.bashrc"
fi

# Restart Ollama with new model path
echo ""
echo "Restarting Ollama with persistent storage..."
pkill ollama 2>/dev/null || true
sleep 2
OLLAMA_MODELS=/home/ollama-models ollama serve &
sleep 5

echo ""
echo "=============================================="
echo "Step 1: Pulling Qwen3 4B (Fast Agent)"
echo "=============================================="
echo "Purpose: Telemetry annotation, classification"
echo "Size: ~2.5GB, Time: ~1-2 minutes"
echo ""
OLLAMA_MODELS=/home/ollama-models ollama pull qwen3:4b

echo ""
echo "=============================================="
echo "Step 2: Pulling Qwen3 14B (Reasoning Agent)"
echo "=============================================="
echo "Purpose: RCA, remediation planning, chat"
echo "Size: ~9.3GB, Time: ~5-8 minutes"
echo ""
OLLAMA_MODELS=/home/ollama-models ollama pull qwen3:14b

echo ""
echo "=============================================="
echo "Step 3: Verifying Installed Models"
echo "=============================================="
OLLAMA_MODELS=/home/ollama-models ollama list

echo ""
echo "=============================================="
echo "Step 4: Verifying Persistence"
echo "=============================================="
echo "Model storage location:"
ls -la /home/ollama-models/
echo ""
echo "Total size:"
du -sh /home/ollama-models/

echo ""
echo "=============================================="
echo "Step 5: Testing Fast Agent (qwen3:4b)"
echo "=============================================="
echo "Sending test prompt..."
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "Respond with only: Constitutional AIOps Fast Agent Ready!",
  "stream": false
}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','No response')[:100])" 2>/dev/null || echo "Test request sent"

echo ""
echo "=============================================="
echo "Step 6: Testing Reasoning Agent (qwen3:14b)"
echo "=============================================="
echo "Sending test prompt..."
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen3:14b",
  "prompt": "Respond with only: Constitutional AIOps Reasoning Agent Ready!",
  "stream": false
}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','No response')[:100])" 2>/dev/null || echo "Test request sent"

echo ""
echo "=============================================="
echo "SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "Models stored in /home/ollama-models (PERSISTS on pause/resume!)"
echo ""
echo "Next steps:"
echo ""
echo "1. Go to Jarvis Labs dashboard"
echo "2. Copy your API endpoint URL (looks like: https://xxxxx.notebooks.jarvislabs.net)"
echo "3. On your LOCAL machine, set in .env:"
echo "   JARVIS_OLLAMA_URL=https://xxxxx.notebooks.jarvislabs.net"
echo ""
echo "4. Start local services:"
echo "   docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d"
echo ""
echo "5. Open http://localhost:3000 in your browser"
echo ""
echo "=============================================="
echo "OPTIONAL: Benchmark Evaluation Setup"
echo "=============================================="
echo ""
echo "To run benchmarks with BERTScore + cosine similarity"
echo "metrics (GPU-accelerated on A5000), run:"
echo ""
echo "  bash scripts/setup-jarvis-benchmark.sh"
echo ""
echo "This installs sentence-transformers, bert-score, and"
echo "pre-downloads ML models (~2GB total)."
echo ""
echo "=============================================="
echo "COST REMINDER: Pause instance when not using!"
echo "A5000 costs \$0.49/hr - pause to stop billing"
echo "=============================================="
