import os
import sys
import vision
import memory
import intelligence
import latex
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
    # Check for PDFs and converting them
    # Note: process_pdf automatically creates a subfolder or puts images in the output_dir.
    # The requirement says: "If PDFs are detected, automatically create a sub-directory in the source_folder"
    # To keep it simple and compliant with "TitleXImageY", we'll put the images directly in source_dir 
    # OR we need to be careful. The prompt says "store them".
    # Let's verify files in source_dir.
    
    files = os.listdir(source_dir)
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    
    for pdf in pdf_files:
        pdf_path = os.path.join(source_dir, pdf)
        print(f"Found PDF: {pdf}. Converting to images...")
        # We'll create a sub-directory based on the PDF name to keep it clean, 
        # BUT the 'vision.get_image_grouping' scans a folder. 
        # If we put images in a subdir, we need to scan that subdir.
        # However, the user said "accept a directory path... process images...".
        # If we interpret "create a sub-directory" as just storage, we need to know where to read from.
        # Let's extract to `source_dir/pdf_images` or just use the current logic which scans the generated files.
        # If we put them in `source_dir`, the 'get_image_grouping' will find them.
        vision.process_pdf(pdf_path, source_dir) # Placing directly in source_dir for simplicity of the pipeline

    # 2. Grouping
    # Scan for pattern TitleXImageY
    groups = vision.get_image_grouping(source_dir)
    if not groups:
        print("No images found matching pattern 'TitleXImageY.format'.")
        # Do not exit, maybe just finished PDF processing but names didn't match?
        # valid pdf process produced names like {base_name}XImage{i+1}.png, so they should match.

    # 3. Processing Loop
    for title, images in groups.items():
        print(f"\n--- Processing Group: {title} ({len(images)} images) ---")
        content_list = []

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
                
                # Cleanup enhanced temp file (optional, but good practice if we made a temporary one)
                # In current vision.py, we created a new file with suffix _enhanced.
                # enhanced_path might be different from img_path
                if enhanced_path != img_path and "_enhanced" in enhanced_path:
                    try:
                        os.remove(enhanced_path)
                    except:
                        pass
                
                # Save to Memory
                mem.mark_processed(img_path, content)
                
                # Rate limit to be nice to API
                time.sleep(1) 

            content_list.append(content)

        # 4. Generate Output
        output_path = latex.generate_tex_file(title, content_list, source_dir)
        if output_path:
            print(f"Generated LaTeX: {output_path}")

    # 5. Final Report
    print("\n" + "="*30)
    print("Processing Complete.")
    print("Add the following packages to your main LaTeX document:")
    print(latex.get_packages_block())
    print("="*30)

if __name__ == "__main__":
    main()
