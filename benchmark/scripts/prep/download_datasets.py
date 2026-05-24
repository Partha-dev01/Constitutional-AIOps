#!/usr/bin/env python3
"""
Constitutional AIOps - Dataset Downloader (v2.0)

Downloads REAL datasets from multiple sources for benchmarking.
NO synthetic data - only real logs and QA questions.

Datasets:
- OpsEval: QA dataset from NetManAIOps (~10MB)
- HDFS: Real labeled log data from Loghub (~2MB labels + samples)
- BGL: Real supercomputer logs from Loghub (~2000 lines sample)
- Apache/Linux/OpenSSH: Additional Loghub log datasets (~2MB each)
- LEMMA-RCA: Cloud Computing RCA dataset from HuggingFace (~4.74GB)
- LogEval: Log analysis benchmark from GitHub (~50MB)
- AnoMod: Multimodal microservice anomaly dataset from Zenodo

Usage:
    python benchmark/scripts/prep/download_datasets.py              # Core datasets only
    python benchmark/scripts/prep/download_datasets.py --all        # ALL datasets
    python benchmark/scripts/prep/download_datasets.py --skip-lemma # Skip large LEMMA-RCA
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
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BENCHMARK_DIR = PROJECT_ROOT / "benchmark"
RAW_DIR = BENCHMARK_DIR / "raw"


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


def download_additional_loghub() -> bool:
    """Download additional Loghub datasets: Apache, Linux, OpenSSH.

    Each dataset contains 2,000 real log lines with structured CSV labels.
    URL pattern: https://raw.githubusercontent.com/logpai/loghub/master/{Dataset}/{Dataset}_2k.log
    """
    print("\n" + "=" * 50)
    print("Additional Loghub Datasets (Apache, Linux, OpenSSH)")
    print("=" * 50)

    datasets = {
        "apache": {
            "name": "Apache",
            "files": [
                "Apache_2k.log",
                "Apache_2k.log_structured.csv",
                "Apache_2k.log_templates.csv",
            ],
        },
        "linux": {
            "name": "Linux",
            "files": [
                "Linux_2k.log",
                "Linux_2k.log_structured.csv",
                "Linux_2k.log_templates.csv",
            ],
        },
        "openssh": {
            "name": "OpenSSH",
            "files": [
                "OpenSSH_2k.log",
                "OpenSSH_2k.log_structured.csv",
                "OpenSSH_2k.log_templates.csv",
            ],
        },
    }

    all_success = True
    for key, info in datasets.items():
        dest_dir = RAW_DIR / "loghub" / key
        dest_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  --- {info['name']} ---")
        for filename in info["files"]:
            url = f"https://raw.githubusercontent.com/logpai/loghub/master/{info['name']}/{filename}"
            if not download_raw_content(url, dest_dir / filename, filename):
                # Only fail if the primary log file fails
                if filename.endswith("_2k.log"):
                    all_success = False

    return all_success


def download_lemma_rca(full: bool = False) -> bool:
    """Download LEMMA-RCA Cloud Computing dataset from HuggingFace.

    Source: https://lemma-rca.github.io/
    HuggingFace: Lemma-RCA-NEC/Cloud_Computing_Preprocessed
    License: CC-BY-NC-4.0 (Non-Commercial)

    Args:
        full: If True, download ALL zip files (~4.74GB). If False, just the first one.
    """
    print("\n" + "=" * 50)
    print("LEMMA-RCA Cloud Computing (REAL DATA)")
    print("=" * 50)
    print("  Source: HuggingFace Lemma-RCA-NEC/Cloud_Computing_Preprocessed")
    print(f"  Mode: {'FULL (all zip files)' if full else 'SAMPLE (first zip only)'}")
    print("  License: CC-BY-NC-4.0 (Non-Commercial)")

    dest_dir = RAW_DIR / "lemma_rca"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded (skip if sample exists and not requesting full)
    info_file = dest_dir / "dataset_info.json"
    if info_file.exists() and not full:
        print("\n  LEMMA-RCA already downloaded. Skipping...")
        print("  (Delete benchmark/raw/lemma_rca/ to re-download)")
        return True

    try:
        from huggingface_hub import hf_hub_download, list_repo_files

        print("\n  Fetching file list from HuggingFace...")

        # Get all files in the repo
        files = list(list_repo_files("Lemma-RCA-NEC/Cloud_Computing_Preprocessed", repo_type="dataset"))
        log_files = [f for f in files if f.startswith("Log Data/") and f.endswith(".zip")]
        metrics_files = [f for f in files if f.startswith("Metrics Data/") and f.endswith(".zip")]

        print(f"  Found {len(log_files)} log files, {len(metrics_files)} metrics files")

        # Determine which files to download
        files_to_download = log_files if full else log_files[:1]

        downloaded = 0
        for log_file in files_to_download:
            zip_name = Path(log_file).name
            extract_marker = dest_dir / "extracted" / f".{zip_name}.done"

            # Skip if already extracted
            if extract_marker.exists():
                print(f"  Already extracted: {zip_name}")
                downloaded += 1
                continue

            print(f"\n  Downloading: {log_file}")
            try:
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
                    # Mark as extracted
                    extract_marker.parent.mkdir(parents=True, exist_ok=True)
                    extract_marker.touch()
                    print("  Extraction complete")
                    downloaded += 1

            except Exception as e:
                print(f"  Failed to download {zip_name}: {e}")
                continue

        # Save dataset info
        info = {
            "source": "Lemma-RCA-NEC/Cloud_Computing_Preprocessed",
            "website": "https://lemma-rca.github.io/",
            "license": "CC-BY-NC-4.0",
            "downloaded": datetime.utcnow().isoformat(),
            "log_files": log_files,
            "metrics_files": metrics_files,
            "downloaded_count": downloaded,
            "total_count": len(log_files),
            "full_download": full and downloaded == len(log_files),
            "note": f"{'Full' if full else 'Sample'} download - {downloaded}/{len(files_to_download)} zip files",
        }
        with open(info_file, "w") as f:
            json.dump(info, f, indent=2)

        print(f"\n  LEMMA-RCA: {downloaded}/{len(files_to_download)} zip files downloaded")
        return downloaded > 0

    except ImportError:
        print("\n  ERROR: 'huggingface-hub' library not installed.")
        print("  Run: pip install huggingface-hub>=0.17.0")
        print("  Skipping LEMMA-RCA download...")
        return False
    except Exception as e:
        print(f"\n  Download failed: {e}")
        print("  You can retry later or skip LEMMA-RCA with --skip-lemma flag")
        return False


def download_logeval() -> bool:
    """Download LogEval dataset from GitHub.

    Source: github.com/LinDuoming/LogEval
    Contains: 4,000 log entries across 4 tasks:
      - Log parsing, anomaly detection, fault diagnosis, log summarization
    """
    print("\n" + "=" * 50)
    print("LogEval Dataset (REAL DATA)")
    print("=" * 50)

    dest_dir = RAW_DIR / "logeval"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if (dest_dir / "data").exists() or (dest_dir / "LogEval-main").exists():
        print("  LogEval already downloaded. Skipping...")
        return True

    archive_path = RAW_DIR / "logeval.zip"
    url = "https://github.com/LinDuoming/LogEval/archive/refs/heads/main.zip"

    if not download_file(url, archive_path, "LogEval Dataset"):
        return False

    # Extract
    print("  Extracting...")
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(dest_dir)

        # Move contents from nested directory
        nested = dest_dir / "LogEval-main"
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
        print("  LogEval ready")
        return True

    except Exception as e:
        print(f"  Extraction failed: {e}")
        return False


def download_anomod() -> bool:
    """Download AnoMod dataset from Zenodo.

    Source: DOI 10.5281/zenodo.18342898
    Contains: Multimodal microservice anomaly data (logs, metrics, traces,
              API responses, code coverage) from SocialNetwork + TrainTicket.
    4 anomaly categories: performance, service, database, code-level.
    """
    print("\n" + "=" * 50)
    print("AnoMod Dataset (REAL DATA)")
    print("=" * 50)

    dest_dir = RAW_DIR / "anomod"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if (dest_dir / "dataset_info.json").exists():
        print("  AnoMod already downloaded. Skipping...")
        return True

    try:
        # Fetch metadata from Zenodo API
        record_id = "18342898"
        api_url = f"https://zenodo.org/api/records/{record_id}"
        print(f"  Fetching metadata from Zenodo record {record_id}...")

        response = urlopen(api_url, timeout=60)
        metadata = json.loads(response.read().decode("utf-8"))

        files = metadata.get("files", [])
        if not files:
            print("  WARNING: No files found in Zenodo record")
            # Save info even on failure so we know we tried
            with open(dest_dir / "dataset_info.json", "w") as f:
                json.dump({"error": "no_files", "record_id": record_id}, f)
            return False

        print(f"  Found {len(files)} files in Zenodo record:")
        for fi in files:
            size_mb = fi.get("size", 0) / 1024 / 1024
            print(f"    - {fi.get('key', '?')} ({size_mb:.1f} MB)")

        # Download files (skip anything > 2GB)
        downloaded = []
        max_size = 2 * 1024 * 1024 * 1024  # 2GB limit

        for file_info in files:
            filename = file_info.get("key", "")
            size = file_info.get("size", 0)
            download_url = file_info.get("links", {}).get("self", "")

            if size > max_size:
                print(f"  Skipping {filename} ({size / 1024 / 1024 / 1024:.1f} GB - too large)")
                continue

            if download_url:
                dest_path = dest_dir / filename
                size_str = f"{size / 1024 / 1024:.1f} MB"
                if download_file(download_url, dest_path, f"{filename} ({size_str})"):
                    downloaded.append(filename)

                    # Extract if zip
                    if filename.endswith(".zip"):
                        try:
                            extract_to = dest_dir / filename.replace(".zip", "")
                            with zipfile.ZipFile(dest_path, 'r') as zf:
                                zf.extractall(extract_to)
                            print(f"  Extracted: {filename}")
                        except Exception as e:
                            print(f"  Extract warning: {e}")

        # Save dataset info
        info = {
            "source": f"zenodo:{record_id}",
            "doi": "10.5281/zenodo.18342898",
            "downloaded": datetime.utcnow().isoformat(),
            "all_files": [f.get("key", "") for f in files],
            "downloaded_files": downloaded,
            "total_files": len(files),
        }
        with open(dest_dir / "dataset_info.json", "w") as f:
            json.dump(info, f, indent=2)

        print(f"\n  AnoMod: {len(downloaded)}/{len(files)} files downloaded")
        return len(downloaded) > 0

    except Exception as e:
        print(f"  Download failed: {e}")
        print("  AnoMod may not be available or DOI may have changed")
        # Save failure info
        try:
            with open(dest_dir / "dataset_info.json", "w") as f:
                json.dump({"error": str(e), "doi": "10.5281/zenodo.18342898"}, f)
        except Exception:
            pass
        return False


def verify_downloads(include_lemma: bool = True, include_extended: bool = False) -> dict:
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

    if include_extended:
        status.update({
            "apache": False,
            "linux": False,
            "openssh": False,
            "logeval": False,
            "anomod": False,
        })

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
    if hdfs_log.exists() or (hdfs_dir / "HDFS_2k.log_structured.csv").exists():
        status["hdfs"] = True
        print("   HDFS: Real log file found")
    else:
        print("   HDFS: MISSING log file")

    # Check BGL
    bgl_dir = RAW_DIR / "loghub" / "bgl"
    bgl_log = bgl_dir / "BGL_2k.log"
    if bgl_log.exists():
        status["bgl"] = True
        print("   BGL: Real log file found")
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
            dl_count = info.get("downloaded_count", "?")
            total = info.get("total_count", "?")
            print(f"   LEMMA-RCA: Downloaded ({dl_count}/{total} zips)")
        else:
            print("   LEMMA-RCA: NOT DOWNLOADED")
    else:
        status["lemma_rca"] = True
        print("   LEMMA-RCA: SKIPPED")

    # Check extended datasets
    if include_extended:
        # Apache
        apache_log = RAW_DIR / "loghub" / "apache" / "Apache_2k.log"
        if apache_log.exists():
            status["apache"] = True
            print("   Apache: Real log file found")
        else:
            print("   Apache: MISSING")

        # Linux
        linux_log = RAW_DIR / "loghub" / "linux" / "Linux_2k.log"
        if linux_log.exists():
            status["linux"] = True
            print("   Linux: Real log file found")
        else:
            print("   Linux: MISSING")

        # OpenSSH
        openssh_log = RAW_DIR / "loghub" / "openssh" / "OpenSSH_2k.log"
        if openssh_log.exists():
            status["openssh"] = True
            print("   OpenSSH: Real log file found")
        else:
            print("   OpenSSH: MISSING")

        # LogEval
        logeval_dir = RAW_DIR / "logeval"
        if logeval_dir.exists() and any(logeval_dir.iterdir()):
            status["logeval"] = True
            print("   LogEval: Dataset found")
        else:
            print("   LogEval: MISSING")

        # AnoMod
        anomod_info = RAW_DIR / "anomod" / "dataset_info.json"
        if anomod_info.exists():
            with open(anomod_info, "r") as f:
                info = json.load(f)
            if "error" not in info or info.get("downloaded_files"):
                status["anomod"] = True
                dl = len(info.get("downloaded_files", []))
                print(f"   AnoMod: {dl} files downloaded")
            else:
                print(f"   AnoMod: DOWNLOAD FAILED ({info.get('error', '?')})")
        else:
            print("   AnoMod: MISSING")

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
        help="Only download LEMMA-RCA (skip other datasets)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download ALL datasets (core + extended: Apache, Linux, OpenSSH, LogEval, AnoMod, full LEMMA-RCA)",
    )
    parser.add_argument(
        "--full-lemma",
        action="store_true",
        help="Download ALL LEMMA-RCA zip files (not just first sample)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Constitutional AIOps - Dataset Downloader v2.0")
    print("=" * 60)
    print("\nDownloading REAL datasets (no synthetic data):")
    print("  Core:")
    print("    - OpsEval: QA dataset from NetManAIOps (~10MB)")
    print("    - HDFS: Real labeled log data from Loghub (~2MB)")
    print("    - BGL: Real supercomputer logs from Loghub (~2MB)")
    if not args.skip_lemma:
        lemma_mode = "FULL" if (args.full_lemma or args.all) else "SAMPLE"
        print(f"    - LEMMA-RCA: Cloud Computing RCA dataset ({lemma_mode})")
    else:
        print("    - LEMMA-RCA: SKIPPED")

    if args.all:
        print("  Extended:")
        print("    - Apache: Web server logs from Loghub (~2MB)")
        print("    - Linux: System logs from Loghub (~2MB)")
        print("    - OpenSSH: SSH server logs from Loghub (~2MB)")
        print("    - LogEval: Log analysis benchmark (~50MB)")
        print("    - AnoMod: Multimodal microservice anomalies (Zenodo)")
    print("")

    # Create directories
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    results = {}

    if args.lemma_only:
        # Only download LEMMA-RCA
        results["lemma_rca"] = download_lemma_rca(full=args.full_lemma or args.all)
    else:
        # Download core datasets
        results["opseval"] = download_opseval()
        results["hdfs"] = download_hdfs_real()
        results["bgl"] = download_bgl_real()

        # Download LEMMA-RCA unless skipped
        if not args.skip_lemma:
            results["lemma_rca"] = download_lemma_rca(full=args.full_lemma or args.all)
        else:
            results["lemma_rca"] = True  # Mark as OK if skipping

        # Download extended datasets if --all
        if args.all:
            results["additional_loghub"] = download_additional_loghub()
            results["logeval"] = download_logeval()
            results["anomod"] = download_anomod()

    # Verify downloads
    status = verify_downloads(
        include_lemma=not args.skip_lemma,
        include_extended=args.all,
    )

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
                "extended_downloaded": args.all,
            }, f, indent=2)

        print("\n[OK] Datasets downloaded successfully!")
        print("  Run 'python benchmark/scripts/prep/prepare_datasets.py' next.")
        return 0
    else:
        print("\n[FAILED] Some downloads failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
