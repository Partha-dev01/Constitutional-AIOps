#!/bin/bash
# Constitutional AIOps - Jarvis Labs Ollama Setup Script
#
# Run this ON the Jarvis Labs instance via SSH:
#   ssh root@[jarvis-ssh-address] 'bash -s' < scripts/setup-jarvis-ollama.sh
#
# Or copy and paste commands manually after SSH-ing in.

set -e

echo "=============================================="
echo "Constitutional AIOps - Jarvis Labs Ollama Setup"
echo "=============================================="
echo ""

# Check if Ollama is running
if ! command -v ollama &> /dev/null; then
    echo "ERROR: Ollama not found. Make sure you're using the Ollama template!"
    exit 1
fi

echo "Ollama detected. Checking server status..."
ollama list 2>/dev/null || echo "Ollama server starting..."
sleep 2

echo ""
echo "=============================================="
echo "Step 1: Pulling Qwen 2.5 3B (Fast Agent)"
echo "=============================================="
echo "This model is used for quick telemetry annotation and classification."
echo "Size: ~2GB, Time: ~1-2 minutes"
echo ""
ollama pull qwen2.5:3b

echo ""
echo "=============================================="
echo "Step 2: Pulling Qwen 2.5 14B (Reasoning Agent)"
echo "=============================================="
echo "This model is used for RCA, remediation planning, and chat."
echo "Size: ~9GB, Time: ~5-8 minutes"
echo ""
ollama pull qwen2.5:14b

echo ""
echo "=============================================="
echo "Step 3: Verifying Installed Models"
echo "=============================================="
ollama list

echo ""
echo "=============================================="
echo "Step 4: Testing Fast Agent (qwen2.5:3b)"
echo "=============================================="
echo "Sending test prompt..."
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:3b",
  "prompt": "Respond with only: Hello from Constitutional AIOps!",
  "stream": false
}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','No response')[:100])" 2>/dev/null || echo "Test request sent"

echo ""
echo "=============================================="
echo "Step 5: Testing Reasoning Agent (qwen2.5:14b)"
echo "=============================================="
echo "Sending test prompt..."
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:14b",
  "prompt": "Respond with only: Reasoning agent ready!",
  "stream": false
}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','No response')[:100])" 2>/dev/null || echo "Test request sent"

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Your models are ready. Now:"
echo ""
echo "1. Go to Jarvis Labs dashboard"
echo "2. Copy your API endpoint URL (looks like: https://xxxxx.jarvislabs.net)"
echo "3. On your LOCAL machine, set in .env:"
echo "   JARVIS_OLLAMA_URL=https://xxxxx.jarvislabs.net"
echo ""
echo "4. Start local services:"
echo "   docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d"
echo ""
echo "5. Open http://localhost:3000 in your browser"
echo ""
echo "=============================================="
echo "Cost Reminder: Pause instance when not using!"
echo "=============================================="
