import os
import sys
import vision
import memory
import intelligence
import latex
import markdown
import time

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 app.py /path/to/source_folder")
        sys.exit(1)

    source_dir = sys.argv[1]
    if not os.path.exists(source_dir):
        print(f"Error: Directory {source_dir} does not exist.")
        sys.exit(1)

    # Initialize Modules
    log_path = os.path.join(source_dir, "processed_log.json")
    mem = memory.Memory(log_path)
    
    try:
        intel = intelligence.Intelligence()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    print(f"Processing directory: {source_dir}")

    # 1. Pre-processing
    files = os.listdir(source_dir)
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    
    for pdf in pdf_files:
        pdf_path = os.path.join(source_dir, pdf)
        print(f"Found PDF: {pdf}. Converting to images...")
        vision.process_pdf(pdf_path, source_dir) # Placing directly in source_dir for simplicity of the pipeline

    # 2. Grouping
    groups = vision.get_image_grouping(source_dir)
    if not groups:
        print("No images found matching pattern 'TitleXImageY.format'.")

    # 3. Processing Loop
    for title, images in groups.items():
        print(f"\n--- Processing Group: {title} ({len(images)} images) ---")
        latex_list = []
        markdown_list = []

        for img_path in images:
            if mem.is_processed(img_path):
                print(f"Loading cached: {os.path.basename(img_path)}")
                content = mem.get_cached_content(img_path)
            else:
                print(f"Processing: {os.path.basename(img_path)}")
                
                # Enhance
                enhanced_path = vision.enhance_image(img_path)
                
                # Transcribe
                content = intel.transcribe_image(enhanced_path)
                
                # Cleanup enhanced temp file
                if enhanced_path != img_path and "_enhanced" in enhanced_path:
                    try:
                        os.remove(enhanced_path)
                    except:
                        pass
                
                # Save to Memory
                mem.mark_processed(img_path, content)
                
                # Rate limit to be nice to API
                time.sleep(1) 

            # Separate content
            if isinstance(content, dict):
                latex_list.append(content.get("latex", ""))
                markdown_list.append(content.get("markdown", ""))
            else:
                # Fallback for old cached strings
                latex_list.append(content)
                markdown_list.append("*(Markdown not generated for this cached page)*\n\n```latex\n" + content + "\n```")

        # 4. Generate Output
        tex_output_path = latex.generate_tex_file(title, latex_list, source_dir)
        if tex_output_path:
            print(f"Generated LaTeX: {tex_output_path}")
            
        md_output_path = markdown.generate_md_file(title, markdown_list, source_dir)
        if md_output_path:
            print(f"Generated Markdown: {md_output_path}")

    # 5. Final Report
    print("\n" + "="*30)
    print("Processing Complete.")
    print("Add the following packages to your main LaTeX document:")
    print(latex.get_packages_block())
    print("="*30)

if __name__ == "__main__":
    main()
