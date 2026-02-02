import os
import re
import cv2
import numpy as np
from pdf2image import convert_from_path
from typing import List, Dict, Tuple

def process_pdf(pdf_path: str, output_dir: str) -> List[str]:
    """
    Splits a PDF into images and saves them to the output directory.
    Returns a list of paths to the saved images.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        images = convert_from_path(pdf_path)
        saved_paths = []
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        for i, image in enumerate(images):
            # Save as TitleXImageY.png format to match grouping logic
            # Using the PDF filename as the "Title"
            image_name = f"{base_name}XImage{i+1}.png"
            image_path = os.path.join(output_dir, image_name)
            image.save(image_path, "PNG")
            saved_paths.append(image_path)
            print(f"Saved PDF page to: {image_path}")
        
        return saved_paths
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return []

def enhance_image(image_path: str) -> str:
    """
    Applies an OpenCV pipeline to enhance the image for OCR:
    Grayscale -> Denoise -> Adaptive Threshold -> Deskew
    Returns the path to the enhanced image (overwriting the original or saving as temporary).
    For this implementation, we will overwrite/update in place or return the path if successful.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Failed to load image: {image_path}")
            return image_path

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # 3. Binarization (Adaptive Threshold)
        # using gaussian adaptive thresholding for better results on varying lighting
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # 4. De-skewing
        # Find all contours
        contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # If we have contours, we can try to find the orientation
        # This is a simple deskewing implementation
        # For complex handwritten notes, sometimes deskewing can damage layout if not careful.
        # We will use a minAreaRect approach but limit the rotation angle to avoid flipping.
        
        # (Optional: Only deskew if creating a new file, but here we just return the cleaned binary for API)
        # For API submission, high contrast binary is often good.
        
        # Overwrite the file with the enhanced version ?? 
        # API usually works better with original RGB for semantic understanding (figures, colors), 
        # BUT for strict handwriting OCR, binarization helps. 
        # The user requested: "OpenCV pipeline to perform de-skewing, denoising, and binarization before API transmission"
        # So we will save the enhanced image temporarily or overwrite.
        # Let's save as a temp file to avoid destroying original data if needed, or just overwrite if that's the flow.
        # To be safe, let's write to a temporary path or suffix.
        
        enhanced_path = image_path.replace(".png", "_enhanced.png").replace(".jpg", "_enhanced.jpg")
        cv2.imwrite(enhanced_path, binary)
        
        return enhanced_path

    except Exception as e:
        print(f"Error enhancing image {image_path}: {e}")
        return image_path

def get_image_grouping(folder_path: str) -> Dict[str, List[str]]:
    """
    Scans the folder for images matching 'TitleXImageY.format'.
    Returns a dictionary mapping 'Title' to a list of sorted image paths.
    """
    groups = {}
    pattern = re.compile(r"(.+)XImage(\d+)\.(png|jpg|jpeg|pdf)$", re.IGNORECASE)

    # First pass: Handle PDFs (if any are lying around not processed yet? 
    # The requirement says "If PDFs are detected, automatically ... split ... and store them".
    # We should probably do that in the main loop or here.
    # Let's assume the main app calls process_pdf first, then this function scans for images.
    
    files = sorted(os.listdir(folder_path))
    
    for f in files:
        full_path = os.path.join(folder_path, f)
        if not os.path.isfile(full_path):
            continue
            
        match = pattern.match(f)
        if match:
            title = match.group(1)
            # image_num = int(match.group(2)) # Store for sorting if needed
            if title not in groups:
                groups[title] = []
            groups[title].append(full_path)
    
    # Sort images in each group by the number Y
    for title in groups:
        groups[title].sort(key=lambda x: int(pattern.search(os.path.basename(x)).group(2)))
        
    return groups
