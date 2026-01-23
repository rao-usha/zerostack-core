#!/usr/bin/env python3
"""
Pod Setup Script - Installs ML dependencies on a RunPod pod.

Run this once on a new pod to set up the environment.
Usage: python setup_pod.py
"""
import subprocess
import sys
import os


def run_cmd(cmd, desc):
    """Run a command and print status."""
    print(f"\n{'='*60}")
    print(f"📦 {desc}")
    print(f"{'='*60}")
    print(f"$ {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"✅ {desc} - SUCCESS")
    else:
        print(f"❌ {desc} - FAILED (exit code {result.returncode})")
    
    return result.returncode == 0


def main():
    print("\n" + "="*60)
    print("🚀 NEX ML Environment Setup")
    print("="*60)
    
    # Upgrade pip
    run_cmd("pip install --upgrade pip", "Upgrading pip")
    
    # Install core ML packages
    packages = [
        "lightgbm==4.3.0",
        "scikit-learn==1.3.2",
        "pandas==2.1.3",
        "numpy==1.26.2",
        "pyarrow==15.0.0",
        "boto3==1.34.0",
        "tqdm==4.66.1",
        "joblib==1.3.2",
    ]
    
    run_cmd(f"pip install {' '.join(packages)}", "Installing ML packages")
    
    # Create working directory
    run_cmd("mkdir -p /root/nex_ml/{data,models,outputs}", "Creating directories")
    
    # Verify installations
    print("\n" + "="*60)
    print("🔍 Verifying installations...")
    print("="*60)
    
    verify_script = '''
import sys
packages = ["lightgbm", "sklearn", "pandas", "numpy", "pyarrow", "boto3"]
for pkg in packages:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "?")
        print(f"✅ {pkg}: {ver}")
    except ImportError as e:
        print(f"❌ {pkg}: NOT INSTALLED - {e}")
        sys.exit(1)
print("\\n✅ All packages installed successfully!")
'''
    
    result = subprocess.run([sys.executable, "-c", verify_script])
    
    if result.returncode == 0:
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETE!")
        print("="*60)
        print("\nYour pod is ready for ML workloads.")
        print("Directory structure:")
        print("  /root/nex_ml/data/    - Input data")
        print("  /root/nex_ml/models/  - Trained models")
        print("  /root/nex_ml/outputs/ - Results & predictions")
        return 0
    else:
        print("\n❌ Setup failed - check errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
