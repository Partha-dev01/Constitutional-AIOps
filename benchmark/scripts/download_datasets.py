#!/usr/bin/env python3
"""
Constitutional AIOps - Dataset Downloader

Downloads REAL datasets from OpsEval, Loghub, and LEMMA-RCA for benchmarking.
NO synthetic data - only real logs and QA questions.

Datasets:
- OpsEval: QA dataset from NetManAIOps (~10MB)
- HDFS: Real labeled log data from Loghub (~2MB labels + samples)
- BGL: Real supercomputer logs from Loghub (~2000 lines sample)
- LEMMA-RCA: Cloud Computing RCA dataset from HuggingFace (~4.74GB)

Usage:
    python benchmark/scripts/download_datasets.py
    python benchmark/scripts/download_datasets.py --skip-lemma  # Skip large LEMMA-RCA download
"""

import os
import sys
import json
import shutil
import zipfile
import csv
import argparse
from pathlib import Path
from datetime import datetime
from urllib.request import urlretrieve, urlopen
from urllib.error import URLError

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BENCHMARK_DIR = PROJECT_ROOT / "benchmark"
RAW_DIR = BENCHMARK_DIR / "datasets" / "raw"


def download_file(url: str, dest_path: Path, description: str) -> bool:
    """Download a file with progress indication."""
    print(f"\n  Downloading: {description}")
    print(f"   URL: {url}")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, block_num * block_size * 100 / total_size)
                bar = "#" * int(percent / 2) + "-" * (50 - int(percent / 2))
                print(f"\r   [{bar}] {percent:.1f}%", end="", flush=True)

        urlretrieve(url, dest_path, reporthook=progress_hook)
        size_mb = dest_path.stat().st_size / 1024 / 1024
        print(f"\n   Downloaded: {size_mb:.2f} MB")
        return True

    except URLError as e:
        print(f"\n   Download failed: {e}")
        return False
    except Exception as e:
        print(f"\n   Error: {e}")
        return False


def download_raw_content(url: str, dest_path: Path, description: str) -> bool:
    """Download raw text/csv content."""
    print(f"\n  Downloading: {description}")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = urlopen(url, timeout=30)
        content = response.read()
        with open(dest_path, "wb") as f:
            f.write(content)
        size_kb = dest_path.stat().st_size / 1024
        print(f"   Downloaded: {size_kb:.1f} KB")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False


def download_opseval() -> bool:
    """Download OpsEval dataset from GitHub (~10MB)."""
    print("\n" + "=" * 50)
    print("OpsEval Dataset (REAL)")
    print("=" * 50)

    dest_dir = RAW_DIR / "opseval"
    dest_dir.mkdir(parents=True, exist_ok=True)

    archive_path = RAW_DIR / "opseval.zip"
    url = "https://github.com/NetManAIOps/OpsEval-Datasets/archive/refs/heads/main.zip"

    if not download_file(url, archive_path, "OpsEval QA Dataset (~10MB)"):
        return False

    # Extract
    print("   Extracting...")
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(dest_dir)

        # Move contents from nested directory
        nested = dest_dir / "OpsEval-Datasets-main"
        if nested.exists():
            for item in nested.iterdir():
                target = dest_dir / item.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(item), str(target))
            nested.rmdir()

        archive_path.unlink()
        print("   OpsEval ready")
        return True

    except Exception as e:
        print(f"   Extraction failed: {e}")
        return False


def download_hdfs_real() -> bool:
    """Download REAL HDFS data from Loghub."""
    print("\n" + "=" * 50)
    print("Loghub HDFS (REAL DATA)")
    print("=" * 50)

    dest_dir = RAW_DIR / "loghub" / "hdfs"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Download the actual labeled data files
    files = {
        "anomaly_label.csv": "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/anomaly_label.csv",
        "HDFS_templates.csv": "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_templates.csv",
    }

    success = True
    for filename, url in files.items():
        if not download_raw_content(url, dest_dir / filename, filename):
            success = False

    # Download the HDFS_2k.log sample file (real logs, 2000 lines)
    hdfs_sample_url = "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log"
    if not download_raw_content(hdfs_sample_url, dest_dir / "HDFS_2k.log", "HDFS_2k.log (real logs)"):
        # Fallback: try structured log file
        print("   Trying alternate source...")
        hdfs_struct_url = "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log_structured.csv"
        download_raw_content(hdfs_struct_url, dest_dir / "HDFS_2k.log_structured.csv", "HDFS_2k.log_structured.csv")

    return success


def download_bgl_real() -> bool:
    """Download REAL BGL data from Loghub."""
    print("\n" + "=" * 50)
    print("Loghub BGL (REAL DATA)")
    print("=" * 50)

    dest_dir = RAW_DIR / "loghub" / "bgl"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Download the BGL_2k.log sample file (real logs, 2000 lines)
    bgl_sample_url = "https://raw.githubusercontent.com/logpai/loghub/master/BGL/BGL_2k.log"
    if not download_raw_content(bgl_sample_url, dest_dir / "BGL_2k.log", "BGL_2k.log (real logs)"):
        success = False
    else:
        success = True

    # Download structured version with labels
    bgl_struct_url = "https://raw.githubusercontent.com/logpai/loghub/master/BGL/BGL_2k.log_structured.csv"
    download_raw_content(bgl_struct_url, dest_dir / "BGL_2k.log_structured.csv", "BGL_2k.log_structured.csv")

    # Download templates
    bgl_templates_url = "https://raw.githubusercontent.com/logpai/loghub/master/BGL/BGL_2k.log_templates.csv"
    download_raw_content(bgl_templates_url, dest_dir / "BGL_2k.log_templates.csv", "BGL templates")

    return success


def download_lemma_rca() -> bool:
    """Download LEMMA-RCA Cloud Computing dataset from HuggingFace (~4.74GB).

    Source: https://lemma-rca.github.io/
    HuggingFace: Lemma-RCA-NEC/Cloud_Computing_Preprocessed
    License: CC-BY-NC-4.0 (Non-Commercial)

    Note: This dataset is stored as zip files, not standard HuggingFace format.
    We download the first log data zip and extract sample cases.
    """
    print("\n" + "=" * 50)
    print("LEMMA-RCA Cloud Computing (REAL DATA)")
    print("=" * 50)
    print("  Source: HuggingFace Lemma-RCA-NEC/Cloud_Computing_Preprocessed")
    print("  Size: ~4.74 GB total (downloading sample subset)")
    print("  License: CC-BY-NC-4.0 (Non-Commercial)")

    dest_dir = RAW_DIR / "lemma_rca"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    info_file = dest_dir / "dataset_info.json"
    if info_file.exists():
        print("\n  LEMMA-RCA already downloaded. Skipping...")
        print("  (Delete benchmark/datasets/raw/lemma_rca/ to re-download)")
        return True

    try:
        from huggingface_hub import hf_hub_download, list_repo_files

        print("\n  Fetching file list from HuggingFace...")

        # Get all files in the repo
        files = list(list_repo_files("Lemma-RCA-NEC/Cloud_Computing_Preprocessed", repo_type="dataset"))
        log_files = [f for f in files if f.startswith("Log Data/") and f.endswith(".zip")]
        metrics_files = [f for f in files if f.startswith("Metrics Data/") and f.endswith(".zip")]

        print(f"  Found {len(log_files)} log files, {len(metrics_files)} metrics files")

        # Download just one log file (smallest/first) for sample cases
        # Full download would be 4.74 GB which is excessive for benchmarking
        if log_files:
            log_file = log_files[0]  # First log file
            print(f"\n  Downloading sample: {log_file}")

            downloaded_path = hf_hub_download(
                repo_id="Lemma-RCA-NEC/Cloud_Computing_Preprocessed",
                filename=log_file,
                repo_type="dataset",
                local_dir=str(dest_dir),
            )
            print(f"  Downloaded to: {downloaded_path}")

            # Extract the zip
            zip_path = dest_dir / log_file
            if zip_path.exists():
                print("  Extracting zip file...")
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(dest_dir / "extracted")
                print("  Extraction complete")

        # Save dataset info
        info = {
            "source": "Lemma-RCA-NEC/Cloud_Computing_Preprocessed",
            "website": "https://lemma-rca.github.io/",
            "license": "CC-BY-NC-4.0",
            "downloaded": datetime.utcnow().isoformat(),
            "log_files": log_files,
            "metrics_files": metrics_files,
            "downloaded_sample": log_files[0] if log_files else None,
            "note": "Sample subset downloaded - full dataset is 4.74 GB",
        }
        with open(info_file, "w") as f:
            json.dump(info, f, indent=2)

        print("\n  LEMMA-RCA sample downloaded successfully!")
        return True

    except ImportError:
        print("\n  ERROR: 'huggingface-hub' library not installed.")
        print("  Run: pip install huggingface-hub>=0.17.0")
        print("  Skipping LEMMA-RCA download...")
        return False
    except Exception as e:
        print(f"\n  Download failed: {e}")
        print("  You can retry later or skip LEMMA-RCA with --skip-lemma flag")
        return False


def verify_downloads(include_lemma: bool = True) -> dict:
    """Verify all downloaded files and report status."""
    print("\n" + "=" * 50)
    print("Verifying Downloads")
    print("=" * 50)

    status = {
        "opseval": False,
        "hdfs": False,
        "bgl": False,
        "lemma_rca": False,
    }

    # Check OpsEval
    opseval_dir = RAW_DIR / "opseval"
    opseval_files = list(opseval_dir.glob("*.json")) if opseval_dir.exists() else []
    if opseval_files:
        status["opseval"] = True
        print(f"   OpsEval: {len(opseval_files)} JSON files found")
    else:
        print("   OpsEval: MISSING")

    # Check HDFS
    hdfs_dir = RAW_DIR / "loghub" / "hdfs"
    hdfs_log = hdfs_dir / "HDFS_2k.log"
    hdfs_labels = hdfs_dir / "anomaly_label.csv"
    if hdfs_log.exists() or (hdfs_dir / "HDFS_2k.log_structured.csv").exists():
        status["hdfs"] = True
        print(f"   HDFS: Real log file found")
    else:
        print("   HDFS: MISSING log file")

    # Check BGL
    bgl_dir = RAW_DIR / "loghub" / "bgl"
    bgl_log = bgl_dir / "BGL_2k.log"
    if bgl_log.exists():
        status["bgl"] = True
        print(f"   BGL: Real log file found")
    else:
        print("   BGL: MISSING log file")

    # Check LEMMA-RCA
    if include_lemma:
        lemma_dir = RAW_DIR / "lemma_rca"
        lemma_info = lemma_dir / "dataset_info.json"
        if lemma_info.exists():
            with open(lemma_info, "r") as f:
                info = json.load(f)
            status["lemma_rca"] = True
            print(f"   LEMMA-RCA: Downloaded ({info.get('downloaded', 'unknown')})")
        else:
            print("   LEMMA-RCA: NOT DOWNLOADED (use --skip-lemma to skip)")
    else:
        status["lemma_rca"] = True  # Mark as OK if skipping
        print("   LEMMA-RCA: SKIPPED")

    return status


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Download benchmark datasets")
    parser.add_argument(
        "--skip-lemma",
        action="store_true",
        help="Skip LEMMA-RCA download (4.74 GB)",
    )
    parser.add_argument(
        "--lemma-only",
        action="store_true",
        help="Only download LEMMA-RCA (skip OpsEval, HDFS, BGL)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Constitutional AIOps - Dataset Downloader")
    print("=" * 60)
    print("\nDownloading REAL datasets (no synthetic data):")
    print("  - OpsEval: QA dataset from NetManAIOps (~10MB)")
    print("  - HDFS: Real labeled log data from Loghub (~2MB)")
    print("  - BGL: Real supercomputer logs from Loghub (~2MB)")
    if not args.skip_lemma:
        print("  - LEMMA-RCA: Cloud Computing RCA dataset (~4.74GB)")
    else:
        print("  - LEMMA-RCA: SKIPPED (use without --skip-lemma to download)")
    print("")

    # Create directories
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    results = {}

    if args.lemma_only:
        # Only download LEMMA-RCA
        results["lemma_rca"] = download_lemma_rca()
    else:
        # Download all datasets
        results["opseval"] = download_opseval()
        results["hdfs"] = download_hdfs_real()
        results["bgl"] = download_bgl_real()

        # Download LEMMA-RCA unless skipped
        if not args.skip_lemma:
            results["lemma_rca"] = download_lemma_rca()
        else:
            results["lemma_rca"] = True  # Mark as OK if skipping

    # Verify downloads
    status = verify_downloads(include_lemma=not args.skip_lemma)

    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)
    for name, success in results.items():
        result = "SUCCESS" if success else "FAILED"
        if name == "lemma_rca" and args.skip_lemma:
            result = "SKIPPED"
        print(f"  {name}: {result}")

    # Create progress marker
    core_datasets = ["opseval", "hdfs", "bgl"]
    core_success = all(results.get(k, False) for k in core_datasets if k in results)

    if core_success:
        (BENCHMARK_DIR / ".benchmark_step1_complete").touch()

        # If LEMMA-RCA also succeeded
        if results.get("lemma_rca", False):
            (BENCHMARK_DIR / ".benchmark_step1b_complete").touch()

        progress_file = BENCHMARK_DIR / ".progress.json"
        with open(progress_file, "w") as f:
            json.dump({
                "step": 1,
                "step_name": "datasets_downloaded",
                "datasets": list(results.keys()),
                "status": status,
                "lemma_rca_downloaded": results.get("lemma_rca", False) and not args.skip_lemma,
            }, f, indent=2)

        print("\n[OK] Datasets downloaded successfully!")
        print("  Run 'python benchmark/scripts/prepare_datasets.py' next.")
        return 0
    else:
        print("\n[FAILED] Some downloads failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
