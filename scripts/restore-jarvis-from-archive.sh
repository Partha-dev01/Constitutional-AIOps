#!/bin/bash
# Constitutional AIOps - Restore Jarvis Labs Environment from Archive
#
# Restores the development environment on a NEW Jarvis Labs instance
# using the jarvis_archive.zip created by the archival process.
#
# Prerequisites:
#   - New Jarvis Labs Ollama A5000 instance running
#   - jarvis_archive.zip uploaded to /home/ on the instance
#
# Usage:
#   # 1. Upload archive from local machine (Git Bash / PowerShell):
#   scp -i .ssh/jarvis_labs_key -P <PORT> \
#     jarvis_archive.zip root@<HOST>:/home/
#
#   # 2. SSH into the instance:
#   ssh -i .ssh/jarvis_labs_key -p <PORT> root@<HOST>
#
#   # 3. Run this script:
#   cd /home && unzip jarvis_archive.zip
#   bash constitutional-aiops/scripts/restore-jarvis-from-archive.sh
#
# What this script does:
#   Step 1: Verifies archive was extracted correctly
#   Step 2: Restores .bashrc environment variables
#   Step 3: Pulls Ollama models (qwen3:4b + qwen3:14b)
#   Step 4: Installs Python dependencies (exact versions from pip_freeze.txt)
#   Step 5: Installs benchmark ML dependencies (sentence-transformers, bert-score)
#   Step 6: Runs verification checks

set -e

ARCHIVE_DIR="/home"
META_DIR="/home/archive_meta"
PROJECT_DIR="/home/constitutional-aiops"

echo "=============================================="
echo "Constitutional AIOps - Restore from Archive"
echo "=============================================="
echo ""

# ─────────────────────────────────────────────────
# Step 1: Verify archive extraction
# ─────────────────────────────────────────────────
echo "Step 1: Verifying archive extraction..."
echo ""

MISSING=0
for f in \
    "$META_DIR/pip_freeze.txt" \
    "$META_DIR/system_info.txt" \
    "$META_DIR/ollama_models.txt" \
    "$META_DIR/ollama_show_4b.txt" \
    "$META_DIR/ollama_show_14b.txt" \
    "$META_DIR/bashrc_backup" \
    "$PROJECT_DIR/requirements.txt" \
    "$PROJECT_DIR/src/config.py" \
    "$PROJECT_DIR/benchmark/scripts/test_5plus5.py"; do
    if [ -f "$f" ]; then
        echo "  OK: $f"
    else
        echo "  MISSING: $f"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "WARNING: $MISSING expected files are missing."
    echo "Make sure you extracted jarvis_archive.zip in /home/:"
    echo "  cd /home && unzip jarvis_archive.zip"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# ─────────────────────────────────────────────────
# Step 2: Restore .bashrc environment variables
# ─────────────────────────────────────────────────
echo "Step 2: Restoring environment variables..."
echo ""

# Set OLLAMA_MODELS for persistent storage
export OLLAMA_MODELS=/home/ollama-models
mkdir -p /home/ollama-models

if ! grep -q "OLLAMA_MODELS" ~/.bashrc 2>/dev/null; then
    echo 'export OLLAMA_MODELS=/home/ollama-models' >> ~/.bashrc
    echo "  Added OLLAMA_MODELS=/home/ollama-models to ~/.bashrc"
fi

# Show what the original .bashrc had
if [ -f "$META_DIR/bashrc_backup" ]; then
    echo "  Original .bashrc exports:"
    grep "^export" "$META_DIR/bashrc_backup" 2>/dev/null | while read -r line; do
        echo "    $line"
    done
fi
echo ""

# ─────────────────────────────────────────────────
# Step 3: Pull Ollama models
# ─────────────────────────────────────────────────
echo "Step 3: Pulling Ollama models..."
echo ""

if ! command -v ollama &> /dev/null; then
    echo "ERROR: Ollama not found. Use the Ollama template on Jarvis Labs!"
    exit 1
fi

# Show original model details for reference
echo "  Original model details (from archive):"
if [ -f "$META_DIR/ollama_models.txt" ]; then
    head -5 "$META_DIR/ollama_models.txt" | while read -r line; do
        echo "    $line"
    done
fi
echo ""

# Restart Ollama with persistent storage
echo "  Restarting Ollama with persistent storage..."
pkill ollama 2>/dev/null || true
sleep 2
OLLAMA_MODELS=/home/ollama-models ollama serve &
sleep 5

echo ""
echo "  Pulling qwen3:4b (Fast Agent, ~2.5GB)..."
OLLAMA_MODELS=/home/ollama-models ollama pull qwen3:4b

echo ""
echo "  Pulling qwen3:14b (Reasoning Agent, ~9.3GB)..."
OLLAMA_MODELS=/home/ollama-models ollama pull qwen3:14b

echo ""
echo "  Verifying models:"
OLLAMA_MODELS=/home/ollama-models ollama list
echo ""

# ─────────────────────────────────────────────────
# Step 4: Install Python dependencies
# ─────────────────────────────────────────────────
echo "Step 4: Installing Python dependencies..."
echo ""

PIP_CMD=$(command -v pip3 || command -v pip)

if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "  Installing from requirements.txt..."
    $PIP_CMD install --quiet -r "$PROJECT_DIR/requirements.txt"
    echo "  Done."
else
    echo "  WARNING: requirements.txt not found, using pip_freeze.txt..."
    if [ -f "$META_DIR/pip_freeze.txt" ]; then
        $PIP_CMD install --quiet -r "$META_DIR/pip_freeze.txt"
        echo "  Done."
    else
        echo "  ERROR: Neither requirements.txt nor pip_freeze.txt found!"
    fi
fi
echo ""

# ─────────────────────────────────────────────────
# Step 5: Install benchmark ML dependencies
# ─────────────────────────────────────────────────
echo "Step 5: Installing benchmark ML dependencies..."
echo ""

echo "  Installing sentence-transformers + bert-score..."
$PIP_CMD install --quiet sentence-transformers
$PIP_CMD install --quiet 'transformers>=4.40,<5.0' 'tokenizers>=0.19,<0.22' bert-score

echo "  Pre-downloading ML models..."
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(f'    all-MiniLM-L6-v2 loaded ({model.get_sentence_embedding_dimension()}-dim)')
" 2>/dev/null || echo "  WARNING: sentence-transformers model download failed"

python3 -c "
from bert_score import score as bert_score
P, R, F1 = bert_score(
    ['test'], ['test'],
    model_type='microsoft/deberta-xlarge-mnli', lang='en', verbose=False
)
print(f'    deberta-xlarge-mnli loaded (test F1={F1.mean().item():.4f})')
" 2>/dev/null || echo "  WARNING: BERTScore model download failed"
echo ""

# ─────────────────────────────────────────────────
# Step 6: Verification
# ─────────────────────────────────────────────────
echo "Step 6: Running verification..."
echo ""

echo "  Python:"
python3 --version

echo ""
echo "  PyTorch + CUDA:"
python3 -c "
import torch
print(f'    PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'    GPU: {torch.cuda.get_device_name(0)}')
" 2>/dev/null || echo "    PyTorch not available"

echo ""
echo "  Ollama models:"
OLLAMA_MODELS=/home/ollama-models ollama list 2>/dev/null || echo "    Ollama not responding"

echo ""
echo "  Project structure:"
if [ -d "$PROJECT_DIR/src" ] && [ -d "$PROJECT_DIR/benchmark" ]; then
    echo "    src/         OK"
    echo "    benchmark/   OK"
    echo "    docs/        $([ -d "$PROJECT_DIR/docs" ] && echo 'OK' || echo 'MISSING')"
    echo "    frontend/    $([ -d "$PROJECT_DIR/frontend" ] && echo 'OK' || echo 'MISSING')"
else
    echo "    WARNING: Project structure incomplete"
fi

echo ""
echo "  Quick Ollama test (qwen3:4b)..."
RESPONSE=$(curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "Respond with only: Ready",
  "stream": false
}' 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','')[:50])" 2>/dev/null)
if [ -n "$RESPONSE" ]; then
    echo "    qwen3:4b response: $RESPONSE"
else
    echo "    WARNING: qwen3:4b did not respond (may need warm-up)"
fi

echo ""
echo "=============================================="
echo "RESTORE COMPLETE!"
echo "=============================================="
echo ""
echo "Environment restored from archive. You can now:"
echo ""
echo "  # Quick benchmark test (5+5 samples)"
echo "  cd $PROJECT_DIR"
echo "  python benchmark/scripts/test_5plus5.py --ann=5 --rca=5"
echo ""
echo "  # Full benchmark (100 ann + 50 rca)"
echo "  python benchmark/scripts/test_5plus5.py"
echo ""
echo "  # Full ablation study (7 configs)"
echo "  python benchmark/scripts/run_ablation.py --config all"
echo ""
echo "Reference files from original environment:"
echo "  $META_DIR/pip_freeze.txt       - Exact package versions"
echo "  $META_DIR/system_info.txt      - Original OS/GPU/CUDA info"
echo "  $META_DIR/ollama_models.txt    - Original model list + hashes"
echo "  $META_DIR/env_vars.txt         - Original environment variables"
echo ""
echo "=============================================="
echo "COST REMINDER: Pause instance when not using!"
echo "A5000 costs \$0.49/hr"
echo "=============================================="
