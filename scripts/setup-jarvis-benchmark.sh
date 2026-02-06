#!/bin/bash
# Constitutional AIOps - Jarvis Labs Benchmark Setup Script
#
# Installs Python ML dependencies for benchmark evaluation on Jarvis Labs.
# Run this AFTER setup-jarvis-ollama.sh to add BERTScore + cosine similarity support.
#
# Usage:
#   ssh -p [PORT] root@sshn.jarvislabs.ai 'bash -s' < scripts/setup-jarvis-benchmark.sh
#
# Or run directly on the Jarvis Labs instance after SSH-ing in.

set -e

echo "=============================================="
echo "Constitutional AIOps - Benchmark Setup"
echo "=============================================="
echo ""
echo "Installing ML dependencies for multi-metric evaluation:"
echo "  - sentence-transformers (all-MiniLM-L6-v2, 384-dim cosine similarity)"
echo "  - bert-score (microsoft/deberta-xlarge-mnli)"
echo ""

# Check if Python3 and pip are available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found!"
    exit 1
fi

if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    apt-get update -qq && apt-get install -y -qq python3-pip
fi

# Use pip3 if pip is not available
PIP_CMD=$(command -v pip3 || command -v pip)

echo ""
echo "=============================================="
echo "Step 1: Installing Python ML packages"
echo "=============================================="

# Core ML packages (torch should already be on Ollama template with CUDA)
$PIP_CMD install --quiet numpy httpx

# Sentence-transformers for cosine similarity (all-MiniLM-L6-v2)
echo "Installing sentence-transformers..."
$PIP_CMD install --quiet sentence-transformers

# BERTScore for semantic similarity (deberta-xlarge-mnli)
# Pin transformers<5.0 and tokenizers<0.22 for bert-score compatibility
# (tokenizers>=0.22 has OverflowError in bert_score's sent_encode)
echo "Installing bert-score (with compatible transformers)..."
$PIP_CMD install --quiet 'transformers>=4.40,<5.0' 'tokenizers>=0.19,<0.22' bert-score

# Other project dependencies needed for benchmark scripts
echo "Installing project dependencies..."
$PIP_CMD install --quiet fastapi pydantic pydantic-settings python-dotenv aiohttp orjson pyyaml

echo ""
echo "=============================================="
echo "Step 2: Pre-downloading ML models"
echo "=============================================="
echo "This avoids delays on the first benchmark run."
echo ""

# Pre-download sentence-transformers model (~90MB)
echo "Downloading all-MiniLM-L6-v2 (cosine similarity)..."
python3 -c "
from sentence_transformers import SentenceTransformer
import torch
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
device = 'CUDA' if torch.cuda.is_available() else 'CPU'
print(f'  Model loaded on {device}')
print(f'  Embedding dimensions: {model.get_sentence_embedding_dimension()}')
" 2>/dev/null

# Pre-download BERTScore model (~1.4GB)
echo "Downloading deberta-xlarge-mnli (BERTScore)..."
python3 -c "
from bert_score import score as bert_score
P, R, F1 = bert_score(
    ['Constitutional AIOps test'], ['Constitutional AIOps test'],
    model_type='microsoft/deberta-xlarge-mnli', lang='en', verbose=False
)
print(f'  BERTScore ready. Test F1={F1.mean().item():.4f}')
" 2>/dev/null

echo ""
echo "=============================================="
echo "Step 3: Verifying installation"
echo "=============================================="

python3 -c "
import torch
print(f'PyTorch: {torch.__version__} (CUDA: {torch.cuda.is_available()})')
if torch.cuda.is_available():
    print(f'  GPU: {torch.cuda.get_device_name(0)}')

from sentence_transformers import SentenceTransformer
print('sentence-transformers: OK')

from bert_score import score
print('bert-score: OK')

import httpx, numpy
print(f'httpx: {httpx.__version__}, numpy: {numpy.__version__}')
print()
print('All benchmark dependencies ready!')
"

echo ""
echo "=============================================="
echo "BENCHMARK SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "To run the benchmark from this Jarvis Labs instance:"
echo ""
echo "  # Clone/update the repo to /home (persists on pause/resume)"
echo "  cd /home && git clone <repo-url> constitutional-aiops"
echo "  cd constitutional-aiops"
echo "  pip install -r requirements.txt"
echo ""
echo "  # Quick test (5+5 samples)"
echo "  python benchmark/scripts/test_5plus5.py --ann=5 --rca=5"
echo ""
echo "  # Full benchmark (100 ann + 50 rca)"
echo "  python benchmark/scripts/test_5plus5.py"
echo ""
echo "  # Ablation study (all 4 configs)"
echo "  python benchmark/scripts/run_ablation.py --config all --ann 5 --rca 5"
echo ""
echo "  # Export paper tables"
echo "  python benchmark/scripts/export_metrics.py"
echo ""
echo "NOTE: Running ON Jarvis Labs uses localhost Ollama (0ms network latency)"
echo "      and GPU-accelerated BERTScore + cosine similarity."
echo "=============================================="
