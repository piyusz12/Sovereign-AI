import os
from pathlib import Path

def list_files(repo_path: str, max_depth: int = 3) -> list[str]:
    """List interesting files in the repository (skipping .git, __pycache__, etc)"""
    repo = Path(repo_path)
    if not repo.exists():
        return []
    
    files = []
    for root, dirs, filenames in os.walk(repo):
        # Skip hidden and system folders
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        rel_root = Path(root).relative_to(repo)
        
        if len(rel_root.parts) >= max_depth:
            continue
            
        for name in filenames:
            if not name.startswith('.'):
                files.append(str(rel_root / name))
    return files

def read_file(repo_path: str, file_path: str) -> str:
    """Read the contents of a specific file in the repo"""
    full_path = Path(repo_path) / file_path
    if not full_path.exists() or not full_path.is_file():
        return f"Error: File {file_path} not found."
    try:
        return full_path.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"
