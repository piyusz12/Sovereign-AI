"""
Sovereign AI Workbench — Offline Packager (Phase 26)

Bundles the backend, frontend, models, and Python wheels into an
offline-installable archive for air-gapped deployment.
"""

import os
import shutil
import tarfile
import subprocess
from pathlib import Path

def package():
    base_dir = Path(__file__).parent.parent
    offline_dir = base_dir / "offline_bundle"
    
    if offline_dir.exists():
        shutil.rmtree(offline_dir)
    offline_dir.mkdir()
    
    print("Packaging Sovereign AI Workbench for Offline Deployment...")
    
    # 1. Copy Application Code
    print("Copying backend...")
    shutil.copytree(base_dir / "backend", offline_dir / "backend", dirs_exist_ok=True)
    shutil.copytree(base_dir / "config", offline_dir / "config", dirs_exist_ok=True)
    
    # 2. Download Python Wheels (requires internet during packaging, none during deploy)
    print("Downloading Python wheels...")
    wheels_dir = offline_dir / "wheels"
    wheels_dir.mkdir()
    subprocess.run(["pip", "download", "-r", str(base_dir / "requirements.txt"), "-d", str(wheels_dir)], check=True)
    
    # 3. Copy deployment scripts
    print("Copying deployment scripts...")
    shutil.copytree(base_dir / "deployment", offline_dir / "deployment", dirs_exist_ok=True)
    
    # 4. Create an install script
    install_script = offline_dir / "install.sh"
    install_script.write_text("#!/bin/bash\n"
                              "echo 'Installing Sovereign AI Workbench (Offline)...'\n"
                              "pip install --no-index --find-links ./wheels -r ../requirements.txt\n"
                              "echo 'Ready to start!'\n")
                              
    # 5. Compress
    print("Compressing archive...")
    archive_path = base_dir / "sovereign_workbench_offline.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(offline_dir, arcname="offline_bundle")
        
    print(f"Done! Offline package created at: {archive_path}")

if __name__ == "__main__":
    package()
