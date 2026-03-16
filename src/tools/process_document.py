import os
import json
from pydantic import BaseModel, Field
from typing import Literal, Optional

from src.services import vision
from src.services.intelligence import CachedIntelligence
from src.services.batch_processor import BatchProcessor

class ProcessDocumentInput(BaseModel):
    """
    Input schema for the smart document processing tool (Traffic Controller).
    """
    document_path: str = Field(
        ...,
        description="The absolute file path to the PDF document or a folder of images."
    )
    mode: Literal["latex", "markdown", "both"] = Field(
        default="both",
        description="The desired textual output format."
    )
    threshold_pages: Optional[int] = Field(
        default=50,
        description="Optional page threshold to automatically switch to the async Batch API."
    )

def smart_process_document(input_data: ProcessDocumentInput) -> str:
    """
    The main Agent tool which acts as a Traffic Controller.
    If the document has > threshold_pages, it routes to Batch API.
    Otherwise, it processes synchronously using Context Caching.
    """
    doc_path = input_data.document_path
    mode = input_data.mode
    threshold = input_data.threshold_pages

    if not os.path.exists(doc_path):
        return json.dumps({"error": "FileNotFound", "details": f"Cannot find {doc_path}"})

    try:
        # Determine paths
        is_pdf = doc_path.lower().endswith(".pdf")
        
        # We need a staging folder where the images live. Use a generic cache folder if it's a single file.
        output_dir = os.path.dirname(doc_path)
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        work_dir = os.path.join(output_dir, base_name, "figures")
        
        os.makedirs(work_dir, exist_ok=True)
        
        image_paths = []
        if is_pdf:
            image_paths = vision.process_pdf(doc_path, work_dir)
        elif os.path.isdir(doc_path):
            image_paths = [os.path.join(doc_path, f) for f in os.listdir(doc_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        else:
            image_paths = [doc_path]

        num_images = len(image_paths)

        if num_images == 0:
            return json.dumps({"error": "NoImages", "details": "Found no valid images to parse."})

        # --- TRAFFIC CONTROLLER ---
        if num_images > threshold:
            # Route to Asynchronous Batch API
            processor = BatchProcessor()
            # Send the un-enhanced images (or optionally enhance them first, but batch is slow anyway)
            result = processor.process_directory_batch(image_paths, mode)
            return json.dumps(result, indent=2)

        else:
            # Route to Synchronous Cached API
            intel = CachedIntelligence()
            try:
                # Initialize Context Cache for the session
                intel.initialize_cache(mode)
                
                results_log = []
                for p in image_paths:
                    enhanced = vision.enhance_image(p)
                    content = intel.transcribe_image(enhanced, mode)
                    
                    if enhanced != p:
                        try: os.remove(enhanced)
                        except: pass
                        
                    results_log.append({
                        "file": os.path.basename(p),
                        "content": content
                    })
                    
                # Cleanup cache
                intel.cleanup()
                
                return json.dumps({"status": "success", "results": results_log}, indent=2)
                
            except Exception as e:
                intel.cleanup()
                raise e

    except Exception as e:
        return json.dumps({
            "error": "TrafficControllerException",
            "details": str(e)
        })
