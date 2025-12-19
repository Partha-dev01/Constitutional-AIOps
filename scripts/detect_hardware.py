#!/usr/bin/env python3
"""
Constitutional AIOps - Hardware Detection Script

Detects system hardware capabilities and recommends deployment mode.
Can be used standalone or imported as a module.

Usage:
    python scripts/detect_hardware.py
    python scripts/detect_hardware.py --json
"""

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class GPUInfo:
    """GPU information container."""
    available: bool = False
    name: str = ""
    memory_mb: int = 0
    driver_version: str = ""
    cuda_version: str = ""
    nvidia_toolkit: bool = False


@dataclass
class SystemInfo:
    """System information container."""
    os_name: str = ""
    os_version: str = ""
    architecture: str = ""
    cpu_cores: int = 0
    memory_gb: float = 0
    docker_version: str = ""
    docker_compose_version: str = ""


@dataclass
class HardwareReport:
    """Complete hardware detection report."""
    system: SystemInfo
    gpu: GPUInfo
    recommended_mode: str
    can_run_gpu_mode: bool
    can_run_local_mode: bool
    warnings: list
    requirements_met: bool


def run_command(cmd: list, timeout: int = 10) -> Optional[str]:
    """Run a command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None


def detect_system() -> SystemInfo:
    """Detect system information."""
    info = SystemInfo()

    # OS information
    info.os_name = platform.system()
    info.os_version = platform.release()
    info.architecture = platform.machine()

    # CPU cores
    try:
        info.cpu_cores = os.cpu_count() or 1
    except Exception:
        info.cpu_cores = 1

    # Memory
    if info.os_name == "Linux":
        mem_output = run_command(["free", "-b"])
        if mem_output:
            for line in mem_output.split("\n"):
                if line.startswith("Mem:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        info.memory_gb = int(parts[1]) / (1024 ** 3)
                        break
    elif info.os_name == "Darwin":  # macOS
        mem_output = run_command(["sysctl", "-n", "hw.memsize"])
        if mem_output:
            info.memory_gb = int(mem_output) / (1024 ** 3)
    elif info.os_name == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', c_ulonglong),
                    ('ullAvailPhys', c_ulonglong),
                    ('ullTotalPageFile', c_ulonglong),
                    ('ullAvailPageFile', c_ulonglong),
                    ('ullTotalVirtual', c_ulonglong),
                    ('ullAvailVirtual', c_ulonglong),
                    ('ullAvailExtendedVirtual', c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            info.memory_gb = stat.ullTotalPhys / (1024 ** 3)
        except Exception:
            info.memory_gb = 8  # Default assumption

    # Docker version
    docker_output = run_command(["docker", "--version"])
    if docker_output:
        # Parse "Docker version 24.0.7, build afdd53b"
        parts = docker_output.split()
        if len(parts) >= 3:
            info.docker_version = parts[2].rstrip(",")

    # Docker Compose version
    compose_output = run_command(["docker", "compose", "version", "--short"])
    if compose_output:
        info.docker_compose_version = compose_output
    else:
        # Try old docker-compose command
        compose_output = run_command(["docker-compose", "--version"])
        if compose_output:
            parts = compose_output.split()
            if len(parts) >= 3:
                info.docker_compose_version = parts[2].rstrip(",")

    return info


def detect_gpu() -> GPUInfo:
    """Detect NVIDIA GPU information."""
    info = GPUInfo()

    # Try nvidia-smi
    nvidia_output = run_command([
        "nvidia-smi",
        "--query-gpu=name,memory.total,driver_version",
        "--format=csv,noheader,nounits"
    ])

    if nvidia_output:
        info.available = True
        parts = nvidia_output.split(",")
        if len(parts) >= 3:
            info.name = parts[0].strip()
            info.memory_mb = int(float(parts[1].strip()))
            info.driver_version = parts[2].strip()

    # CUDA version
    cuda_output = run_command(["nvidia-smi", "--query-gpu=cuda_version", "--format=csv,noheader"])
    if cuda_output:
        info.cuda_version = cuda_output.strip()

    # Check for NVIDIA Container Toolkit
    docker_info = run_command(["docker", "info"])
    if docker_info and "nvidia" in docker_info.lower():
        info.nvidia_toolkit = True
    else:
        # Alternative check
        toolkit_check = run_command(["nvidia-ctk", "--version"])
        if toolkit_check:
            info.nvidia_toolkit = True

    return info


def generate_report() -> HardwareReport:
    """Generate complete hardware detection report."""
    system = detect_system()
    gpu = detect_gpu()
    warnings = []

    # Determine capabilities
    min_memory_gb = 8
    min_gpu_memory_mb = 20 * 1024  # 20GB

    can_run_local = True
    can_run_gpu = False

    # Check basic requirements
    if not system.docker_version:
        warnings.append("Docker not installed or not in PATH")
        can_run_local = False

    if not system.docker_compose_version:
        warnings.append("Docker Compose not installed or not in PATH")
        can_run_local = False

    if system.memory_gb < min_memory_gb:
        warnings.append(f"System memory ({system.memory_gb:.1f}GB) is below recommended ({min_memory_gb}GB)")

    # Check GPU requirements
    if gpu.available:
        if gpu.memory_mb >= min_gpu_memory_mb:
            if gpu.nvidia_toolkit:
                can_run_gpu = True
            else:
                warnings.append("NVIDIA Container Toolkit not detected - GPU mode unavailable")
        else:
            warnings.append(f"GPU memory ({gpu.memory_mb}MB) is below required ({min_gpu_memory_mb}MB) for GPU mode")

    # Determine recommended mode
    if can_run_gpu:
        recommended_mode = "gpu"
    elif can_run_local:
        recommended_mode = "local"
    else:
        recommended_mode = "none"

    requirements_met = can_run_local or can_run_gpu

    return HardwareReport(
        system=system,
        gpu=gpu,
        recommended_mode=recommended_mode,
        can_run_gpu_mode=can_run_gpu,
        can_run_local_mode=can_run_local,
        warnings=warnings,
        requirements_met=requirements_met
    )


def print_report(report: HardwareReport, as_json: bool = False):
    """Print the hardware report."""
    if as_json:
        print(json.dumps(asdict(report), indent=2))
        return

    print("\n" + "=" * 60)
    print("  Constitutional AIOps - Hardware Detection Report")
    print("=" * 60)

    # System Information
    print("\n📊 System Information")
    print("-" * 40)
    print(f"  OS:           {report.system.os_name} {report.system.os_version}")
    print(f"  Architecture: {report.system.architecture}")
    print(f"  CPU Cores:    {report.system.cpu_cores}")
    print(f"  Memory:       {report.system.memory_gb:.1f} GB")
    print(f"  Docker:       {report.system.docker_version or 'Not installed'}")
    print(f"  Compose:      {report.system.docker_compose_version or 'Not installed'}")

    # GPU Information
    print("\n🎮 GPU Information")
    print("-" * 40)
    if report.gpu.available:
        print(f"  GPU:          {report.gpu.name}")
        print(f"  VRAM:         {report.gpu.memory_mb} MB ({report.gpu.memory_mb / 1024:.1f} GB)")
        print(f"  Driver:       {report.gpu.driver_version}")
        print(f"  CUDA:         {report.gpu.cuda_version}")
        print(f"  Toolkit:      {'Installed' if report.gpu.nvidia_toolkit else 'Not detected'}")
    else:
        print("  No NVIDIA GPU detected")

    # Capabilities
    print("\n✅ Deployment Capabilities")
    print("-" * 40)
    print(f"  Local Mode:   {'Yes' if report.can_run_local_mode else 'No'}")
    print(f"  GPU Mode:     {'Yes' if report.can_run_gpu_mode else 'No'}")
    print(f"  Recommended:  {report.recommended_mode.upper()}")

    # Warnings
    if report.warnings:
        print("\n⚠️  Warnings")
        print("-" * 40)
        for warning in report.warnings:
            print(f"  • {warning}")

    # Summary
    print("\n" + "=" * 60)
    if report.requirements_met:
        print(f"  ✓ Ready to deploy in {report.recommended_mode.upper()} mode")
        print(f"  Run: ./scripts/install.sh --{report.recommended_mode}")
    else:
        print("  ✗ System requirements not met")
        print("  Please install Docker and Docker Compose to continue")
    print("=" * 60 + "\n")


def main():
    """Main entry point."""
    as_json = "--json" in sys.argv or "-j" in sys.argv

    report = generate_report()
    print_report(report, as_json=as_json)

    # Exit code based on requirements
    sys.exit(0 if report.requirements_met else 1)


if __name__ == "__main__":
    main()
