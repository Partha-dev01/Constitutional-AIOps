#!/usr/bin/env python3
"""
Post-processing script: compute BERTScore + cosine similarity on existing results.

Usage:
    python benchmark/scripts/compute_semantic_metrics.py \
        --input benchmark/results_aws/run_stackA_main431/results_merged.json \
        --output benchmark/results_aws/run_stackA_main431/results_merged_with_metrics.json

Requires: pip install sentence-transformers bert-score torch
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BERTSCORE_MODEL = "microsoft/deberta-xlarge-mnli"


def load_results(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("results", [])


def normalize_text(text: str, task_type: str, role: str) -> str:
    """Strip JSON wrapper from annotation expected outputs for fair comparison."""
    if not text:
        return ""
    text = text.strip()
    if role == "expected" and task_type == "annotation":
        try:
            obj = json.loads(text)
            parts = []
            if obj.get("anomaly_detected"):
                parts.append("anomaly detected")
            if "severity" in obj:
                parts.append(f"severity {obj['severity']}")
            if "category" in obj:
                parts.append(f"category {obj['category']}")
            if parts:
                return " ".join(parts)
        except (json.JSONDecodeError, AttributeError):
            pass
    return text


def compute_cosine(candidates: list[str], references: list[str]) -> list[float]:
    from sentence_transformers import SentenceTransformer
    import torch
    import torch.nn.functional as F

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading embedding model on {device}: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)

    all_texts = candidates + references
    logger.info(f"Encoding {len(all_texts)} texts for cosine similarity...")
    embeddings = model.encode(all_texts, batch_size=64, show_progress_bar=True,
                               convert_to_tensor=True, device=device)
    n = len(candidates)
    cand_emb = embeddings[:n]
    ref_emb = embeddings[n:]
    sims = F.cosine_similarity(cand_emb, ref_emb, dim=1)
    return [round(float(s), 4) for s in sims]


def compute_bert(candidates: list[str], references: list[str]) -> list[float]:
    from bert_score import score as bert_score_fn
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Computing BERTScore on {device} for {len(candidates)} pairs...")
    valid_pairs = [(c, r) for c, r in zip(candidates, references) if c.strip() and r.strip()]
    if not valid_pairs:
        return [0.0] * len(candidates)
    valid_c = [p[0] for p in valid_pairs]
    valid_r = [p[1] for p in valid_pairs]
    P, R, F1 = bert_score_fn(valid_c, valid_r, model_type=BERTSCORE_MODEL,
                              lang="en", verbose=True,
                              device=device, batch_size=16)
    scores = [round(float(f), 4) for f in F1.tolist()]
    # Fill back zeros for empty pairs
    result = []
    vi = 0
    for c, r in zip(candidates, references):
        if c.strip() and r.strip():
            result.append(scores[vi])
            vi += 1
        else:
            result.append(0.0)
    return result


def term_overlap(cand: str, ref: str) -> float:
    if not ref.strip():
        return 0.0
    ref_terms = set(ref.lower().split())
    cand_terms = set(cand.lower().split())
    if not ref_terms:
        return 0.0
    return round(len(ref_terms & cand_terms) / len(ref_terms), 4)


def print_summary(results: list[dict]) -> None:
    ann = [r for r in results if r.get("task_type") == "annotation"]
    rca = [r for r in results if r.get("task_type") == "rca"]

    def avg(lst, key):
        vals = [v for r in lst if (v := r.get(key, 0)) > 0]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    total = len(results)
    correct = sum(1 for r in results if r.get("correct"))
    logger.info("=" * 60)
    logger.info(f"SUMMARY — {correct}/{total} = {100*correct/total:.1f}% accuracy")
    logger.info(f"Annotation ({len(ann)}): bert_f1={avg(ann,'bert_f1')} cosine={avg(ann,'cosine_similarity')} overlap={avg(ann,'term_overlap')}")
    logger.info(f"RCA ({len(rca)}):        bert_f1={avg(rca,'bert_f1')} cosine={avg(rca,'cosine_similarity')} overlap={avg(rca,'term_overlap')}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--skip-bert", action="store_true", help="Skip BERTScore (faster)")
    args = parser.parse_args()

    results = load_results(args.input)
    logger.info(f"Loaded {len(results)} results from {args.input}")

    candidates = [normalize_text(r.get("actual_output", ""), r.get("task_type", ""), "actual") for r in results]
    references = [normalize_text(r.get("expected_output", ""), r.get("task_type", ""), "expected") for r in results]

    # Term overlap (no GPU needed)
    logger.info("Computing term overlap...")
    for i, (c, r) in enumerate(zip(candidates, references)):
        results[i]["term_overlap"] = term_overlap(c, r)

    # Cosine similarity
    try:
        cosine_scores = compute_cosine(candidates, references)
        for i, score in enumerate(cosine_scores):
            results[i]["cosine_similarity"] = score
        logger.info(f"Cosine similarity computed. Mean={sum(cosine_scores)/len(cosine_scores):.4f}")
    except Exception as e:
        logger.error(f"Cosine similarity failed: {e}")
        sys.exit(1)

    # BERTScore
    if not args.skip_bert:
        try:
            bert_scores = compute_bert(candidates, references)
            for i, score in enumerate(bert_scores):
                results[i]["bert_f1"] = score
            logger.info(f"BERTScore computed. Mean={sum(bert_scores)/len(bert_scores):.4f}")
        except Exception as e:
            logger.error(f"BERTScore failed: {e}")
            logger.warning("Saving without BERTScore. Re-run without --skip-bert once GPU memory issue resolved.")

    print_summary(results)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved enriched results to {args.output}")


if __name__ == "__main__":
    main()
