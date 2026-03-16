import sys
from pathlib import Path
from src.services import vision
from src.utils import memory
from src.services import intelligence
from src.utils import latex
from src.utils import markdown
import time

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m src.interfaces.cli /path/to/source_folder")
        sys.exit(1)

    source_dir = Path(sys.argv[1]).resolve()
    
    while True:
        mode = input("What would you like to generate? (latex/markdown/both) [both]: ").strip().lower()
        if not mode:
            mode = "both"
            break
        if mode in ["latex", "markdown", "both"]:
            break
        print("Invalid input. Please enter 'latex', 'markdown', or 'both'.")

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"Error: Directory {source_dir} does not exist.")
        sys.exit(1)

    # Initialize Modules
    log_path = source_dir / "processed_log.json"
    mem = memory.Memory(str(log_path))
    
    try:
        intel = intelligence.Intelligence()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    print(f"Processing directory: {source_dir}")

    # 1. Pre-processing
    pdf_files = list(source_dir.glob('*.pdf'))
    
    for pdf in pdf_files:
        print(f"Found PDF: {pdf.name}. Converting to images...")
        vision.process_pdf(str(pdf), str(source_dir))

    # 2. Grouping
    groups = vision.get_image_grouping(str(source_dir))
    if not groups:
        print("No images found matching pattern 'TitleXImageY.format'.")

    # 3. Processing Loop
    for title, images in groups.items():
        print(f"\n--- Processing Group: {title} ({len(images)} images) ---")
        latex_list = []
        markdown_list = []
        
        # Setup Output Directories
        doc_dir = source_dir / title
        fig_dir = doc_dir / "figures"
        latex_dir = doc_dir / "latex"
        md_dir = doc_dir / "markdown"
        
        fig_dir.mkdir(parents=True, exist_ok=True)
        latex_dir.mkdir(parents=True, exist_ok=True)
        md_dir.mkdir(parents=True, exist_ok=True)

        for img_path_str in images:
            img_path = Path(img_path_str)
            # Move image to its structured figures folder to keep root clean
            new_img_path = fig_dir / img_path.name
            if img_path.exists() and img_path != new_img_path:
                img_path.rename(new_img_path)
            
            structured_img_path = str(new_img_path)
            img_basename = new_img_path.name

            if mem.is_processed(structured_img_path):
                print(f"Loading cached: {img_basename}")
                content = mem.get_cached_content(structured_img_path)
            else:
                print(f"Processing: {img_basename}")
                
                # Enhance
                enhanced_path = vision.enhance_image(structured_img_path)
                
                # Transcribe
                content = intel.transcribe_image(enhanced_path, mode=mode)
                
                # Cleanup enhanced temp file
                if enhanced_path != structured_img_path and "_enhanced" in enhanced_path:
                    try:
                        Path(enhanced_path).unlink()
                    except:
                        pass
                
                # Save to Memory
                mem.mark_processed(structured_img_path, content)
                
                # Rate limit to be nice to API
                time.sleep(1) 

            # Separate content
            if isinstance(content, dict):
                base_info = content.get("base_latex_md", {})
                annotations = content.get("annotations_metadata", [])
                
                # Save annotations to a separate markdown file
                if annotations:
                    anno_path = md_dir / f"{title}_annotations.md"
                    with open(anno_path, "a") as f:
                        f.write(f"\n## Annotations for {img_basename}\n")
                        for anno in annotations:
                            f.write(f"- **{anno.get('category')}**: {anno.get('content')} ({anno.get('context')})\n")
                
                if mode in ["latex", "both"]:
                    latex_list.append(base_info.get("latex", ""))
                if mode in ["markdown", "both"]:
                    markdown_list.append(base_info.get("markdown", ""))
            else:
                # Fallback for old cached strings
                if mode in ["latex", "both"]:
                    latex_list.append(content)
                if mode in ["markdown", "both"]:
                    markdown_list.append("*(Markdown not generated for this cached page)*\n\n```latex\n" + str(content) + "\n```")

        # 4. Generate Output
        if mode in ["latex", "both"]:
            tex_output_path = latex.generate_tex_file(title, latex_list, str(latex_dir))
            if tex_output_path:
                print(f"Generated LaTeX: {tex_output_path}")
            
        if mode in ["markdown", "both"]:
            md_output_path = markdown.generate_md_file(title, markdown_list, str(md_dir))
            if md_output_path:
                print(f"Generated Markdown: {md_output_path}")

    # 5. Final Report
    print("\n" + "="*30)
    print("Processing Complete.")
    if mode in ["latex", "both"]:
        print("Add the following packages to your main LaTeX document:")
        print(latex.get_packages_block())
    print("="*30)

if __name__ == "__main__":
    main()
