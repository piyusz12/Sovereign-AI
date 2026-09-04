import os
from pathlib import Path

def search_codebase(repo_path: str, query: str) -> list[dict]:
    """
    Search the codebase for a specific symbol or string.
    Returns a list of dicts with file path, line number, and match content.
    """
    repo = Path(repo_path)
    if not repo.exists():
        return []
        
    results = []
    # Using a simple substring search for the prototype.
    # In a full deployment, this integrates with Qdrant for semantic search.
    for root, dirs, filenames in os.walk(repo):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        rel_root = Path(root).relative_to(repo)
        
        for name in filenames:
            if not name.startswith('.') and name.endswith(('.py', '.md', '.txt')):
                full_path = Path(root) / name
                try:
                    lines = full_path.read_text(encoding='utf-8').splitlines()
                    for i, line in enumerate(lines):
                        if query.lower() in line.lower():
                            results.append({
                                "file": str(rel_root / name),
                                "line": i + 1,
                                "content": line.strip()
                            })
                except Exception:
                    pass
                    
    return results
