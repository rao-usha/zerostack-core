#!/usr/bin/env python3
"""
Minimal GPU test script.

This script verifies:
1. GPU is accessible
2. CUDA is working
3. PyTorch can use GPU
4. Basic tensor operations work

Run with: python gpu_test.py
"""
import sys
import json
import subprocess
from datetime import datetime


def check_nvidia_smi():
    """Check GPU via nvidia-smi."""
    print("=" * 60)
    print("1. NVIDIA-SMI CHECK")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            gpu_info = result.stdout.strip()
            print(f"✅ GPU Found: {gpu_info}")
            return {"status": "ok", "gpu_info": gpu_info}
        else:
            print(f"❌ nvidia-smi failed: {result.stderr}")
            return {"status": "error", "error": result.stderr}
    except FileNotFoundError:
        print("❌ nvidia-smi not found")
        return {"status": "error", "error": "nvidia-smi not found"}


def check_cuda():
    """Check CUDA availability."""
    print("\n" + "=" * 60)
    print("2. CUDA CHECK")
    print("=" * 60)
    
    try:
        import torch
        
        cuda_available = torch.cuda.is_available()
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {cuda_available}")
        
        if cuda_available:
            cuda_version = torch.version.cuda
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            
            print(f"CUDA version: {cuda_version}")
            print(f"Device count: {device_count}")
            print(f"Device name: {device_name}")
            print("✅ CUDA is working!")
            
            return {
                "status": "ok",
                "pytorch_version": torch.__version__,
                "cuda_version": cuda_version,
                "device_count": device_count,
                "device_name": device_name
            }
        else:
            print("❌ CUDA not available")
            return {"status": "error", "error": "CUDA not available"}
            
    except ImportError:
        print("❌ PyTorch not installed")
        return {"status": "error", "error": "PyTorch not installed"}


def check_tensor_ops():
    """Run basic tensor operations on GPU."""
    print("\n" + "=" * 60)
    print("3. GPU TENSOR OPERATIONS")
    print("=" * 60)
    
    try:
        import torch
        import time
        
        if not torch.cuda.is_available():
            print("❌ CUDA not available, skipping tensor ops")
            return {"status": "skipped"}
        
        # Create tensors on GPU
        device = torch.device("cuda:0")
        
        print("Creating 1000x1000 random tensors on GPU...")
        a = torch.randn(1000, 1000, device=device)
        b = torch.randn(1000, 1000, device=device)
        
        # Matrix multiplication benchmark
        print("Running matrix multiplication benchmark...")
        torch.cuda.synchronize()
        start = time.time()
        
        for _ in range(100):
            c = torch.matmul(a, b)
        
        torch.cuda.synchronize()
        elapsed = time.time() - start
        
        ops_per_sec = 100 / elapsed
        print(f"✅ 100 matrix multiplications in {elapsed:.3f}s ({ops_per_sec:.1f} ops/sec)")
        
        # Memory check
        allocated = torch.cuda.memory_allocated(0) / 1024**2
        reserved = torch.cuda.memory_reserved(0) / 1024**2
        print(f"GPU Memory: {allocated:.1f}MB allocated, {reserved:.1f}MB reserved")
        
        return {
            "status": "ok",
            "benchmark_time": elapsed,
            "ops_per_sec": ops_per_sec,
            "memory_allocated_mb": allocated,
            "memory_reserved_mb": reserved
        }
        
    except Exception as e:
        print(f"❌ Tensor ops failed: {e}")
        return {"status": "error", "error": str(e)}


def check_lightgbm():
    """Check if LightGBM is available (for forecasting)."""
    print("\n" + "=" * 60)
    print("4. LIGHTGBM CHECK")
    print("=" * 60)
    
    try:
        import lightgbm as lgb
        print(f"LightGBM version: {lgb.__version__}")
        print("✅ LightGBM is available!")
        return {"status": "ok", "version": lgb.__version__}
    except ImportError:
        print("⚠️ LightGBM not installed (will need to install for forecasting)")
        return {"status": "not_installed"}


def main():
    """Run all checks and output results."""
    print("\n" + "=" * 60)
    print("NEX GPU TEST - " + datetime.now().isoformat())
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "nvidia_smi": check_nvidia_smi(),
        "cuda": check_cuda(),
        "tensor_ops": check_tensor_ops(),
        "lightgbm": check_lightgbm()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_ok = all(
        r.get("status") == "ok" 
        for r in [results["nvidia_smi"], results["cuda"], results["tensor_ops"]]
    )
    
    if all_ok:
        print("✅ ALL GPU TESTS PASSED!")
        results["overall"] = "success"
    else:
        print("❌ SOME TESTS FAILED - check above for details")
        results["overall"] = "partial_failure"
    
    # Output JSON for parsing
    print("\n--- JSON OUTPUT ---")
    print(json.dumps(results, indent=2))
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
