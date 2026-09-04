import os
from pathlib import Path

def apply_patch(repo_path: str, file_path: str, search_text: str, replace_text: str) -> str:
    """
    Finds exactly `search_text` inside `file_path` and replaces it with `replace_text`.
    Returns success message or error.
    """
    full_path = Path(repo_path) / file_path
    if not full_path.exists():
        # If it doesn't exist, and search_text is empty, create it.
        if search_text == "":
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(replace_text, encoding="utf-8")
            return f"Successfully created {file_path}"
        return f"Error: File {file_path} does not exist."

    content = full_path.read_text(encoding="utf-8")
    
    if search_text not in content:
        # Try a more forgiving search (strip leading/trailing whitespace from block)
        if search_text.strip() not in content:
            return f"Error: Could not find the exact search_text block in {file_path}."
        else:
            # Re-align search text if it matches exactly stripped
            search_text = search_text.strip()
    
    # Replace exactly the first occurrence
    new_content = content.replace(search_text, replace_text, 1)
    
    if new_content == content:
        return f"Error: Replacement resulted in no changes to {file_path}."
        
    full_path.write_text(new_content, encoding="utf-8")
    return f"Successfully updated {file_path}"
