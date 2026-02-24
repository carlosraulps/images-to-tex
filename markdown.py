import os
from typing import List

def generate_md_file(title: str, content_list: List[str], output_dir: str) -> str:
    """
    Generates a .md file for the given title and content.
    The content_list contains Markdown strings (one per image/page).
    Returns the path to the generated file.
    """
    filename = f"{title}.md"
    output_path = os.path.join(output_dir, filename)

    try:
        with open(output_path, 'w') as f:
            f.write(f"# Auto-generated Markdown for {title}\n\n")
            
            for i, content in enumerate(content_list):
                f.write(f"<!-- --- Page {i+1} --- -->\n")
                f.write(content)
                f.write("\n\n---\n\n")
        
        return output_path
    except Exception as e:
        print(f"Error writing Markdown file {output_path}: {e}")
        return ""
