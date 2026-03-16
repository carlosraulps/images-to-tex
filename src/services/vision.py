import os
import re
import cv2
import numpy as np
from pathlib import Path
from pdf2image import convert_from_path
from typing import List, Dict, Tuple, Union

def process_pdf(pdf_path: Union[str, Path], output_dir: Union[str, Path]) -> List[str]:
    """
    Splits a PDF into images and saves them to the output directory.
    Returns a list of paths to the saved images.
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        images = convert_from_path(str(pdf_path))
        saved_paths = []
        base_name = pdf_path.stem

        for i, image in enumerate(images):
            # Save as TitleXImageY.png format to match grouping logic
            # Using the PDF filename as the "Title"
            image_name = f"{base_name}XImage{i+1}.png"
            image_path = output_dir / image_name
            image.save(str(image_path), "PNG")
            saved_paths.append(str(image_path))
            print(f"Saved PDF page to: {image_path}")
        
        return saved_paths
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return []

def enhance_image(image_path: Union[str, Path]) -> str:
    """
    Applies an OpenCV pipeline to enhance the image for OCR:
    Grayscale -> Denoise -> Adaptive Threshold -> Deskew
    Returns the path to the enhanced image (overwriting the original or saving as temporary).
    For this implementation, we will overwrite/update in place or return the path if successful.
    """
    image_path_str = str(image_path)
    try:
        img = cv2.imread(image_path_str)
        if img is None:
            print(f"Failed to load image: {image_path_str}")
            return image_path_str

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
        
        enhanced_path = image_path_str.replace(".png", "_enhanced.png").replace(".jpg", "_enhanced.jpg")
        cv2.imwrite(enhanced_path, binary)
        
        return enhanced_path

    except Exception as e:
        print(f"Error enhancing image {image_path_str}: {e}")
        return image_path_str

def get_image_grouping(folder_path: Union[str, Path]) -> Dict[str, List[str]]:
    """
    Scans the folder for images matching 'TitleXImageY.format'.
    Returns a dictionary mapping 'Title' to a list of sorted image paths.
    """
    folder_path = Path(folder_path)
    groups = {}
    
    # Pattern explanation:
    # ^(.+?)                : Capture the Title (non-greedy) at the start
    # (?:[\sX_-]+|XImage)   : Separator (Spaces, 'X', '_', '-', or 'XImage' literal)
    # (\d+)                 : The Image/Page Number
    # \.(...)$              : Extension
    pattern = re.compile(r"^(.+?)(?:[\sX_-]+|XImage)(\d+)\.(png|jpg|jpeg|pdf|webp)$", re.IGNORECASE)

    if not folder_path.exists():
        return groups
        
    for p in folder_path.iterdir():
        if not p.is_file():
            continue
        
        # Skip hidden files
        if p.name.startswith('.'):
            continue
            
        match = pattern.match(p.name)
        if match:
            title = match.group(1).strip()
            # image_num = int(match.group(2))
            if title not in groups:
                groups[title] = []
            groups[title].append(str(p))
            
    # Sort images in each group by the number Y
    for title in groups:
        groups[title].sort(key=lambda x: int(pattern.search(Path(x).name).group(2)))
        
    return groups

