import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.models.data_models import DocumentPayload
from src.services.intelligence import ContextMerger

load_dotenv()

class BatchProcessor:
    """
    Manages the creation and submission of Gemini Batch API jobs for massive document directories.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = 'gemini-3.1-pro-preview'

    def process_directory_batch(self, image_paths: List[str], mode: str) -> Dict[str, Any]:
        """
        Takes a list of images, uploads them to Gemini Files, creates a JSONL buffer,
        and submits the batch job. Returns the Batch Job Metadata.
        """
        if not image_paths:
            return {"status": "error", "message": "No images provided for batching."}

        master_prompt = ContextMerger.get_master_prompt(mode)
        jsonl_lines = []
        
        print(f"Preparing batch job for {len(image_paths)} files...")
        
        # 1. Upload files securely for the batch
        uploaded_files = []
        for path in image_paths:
            try:
                # In production, check if file exists on Gemini first, but for now upload
                f_ref = self.client.files.upload(file=path)
                uploaded_files.append((path, f_ref))
                print(f"Uploaded {os.path.basename(path)} to staging.")
                time.sleep(1) # Be nice to the API rate limits during staging
            except Exception as e:
                print(f"Failed to stage {path}: {e}")

        if not uploaded_files:
            return {"status": "error", "message": "Failed to upload any files to staging."}

        # 2. Construct JSONL payload
        for local_path, file_ref in uploaded_files:
            # The custom ID allows us to map the async result back to the specific image
            request_id = os.path.basename(local_path)
            
            # The structure dictated by the Gemini Batch API
            request = {
                "custom_id": request_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": master_prompt},
                                {
                                    "type": "image_url", 
                                    "image_url": {"url": file_ref.uri} # Note: Check if Gemini supports file_ref.uri in OpenAI compat mode, if not fallback to generic Google url. Or standard Gemini batch format may just map this strictly.
                                }
                            ]
                        }
                    ],
                    "response_format": {"type": "json_object"}
                }
            }
            jsonl_lines.append(json.dumps(request))

        # 3. Create the JSONL file locally temporarily
        batch_input_path = "temp_batch_input.jsonl"
        with open(batch_input_path, "w") as f:
            f.write("\n".join(jsonl_lines))

        # 4. Upload the JSONL definition to Gemini
        try:
            batch_input_file = self.client.files.upload(
                file=batch_input_path,
                config={"mime_type": "application/jsonl"}
            )
            print(f"Uploaded JSONL definition. Triggering Job...")
            
            # 5. Execute Job
            batch_job = self.client.batches.create(
                model=self.model_name,
                src=batch_input_file.name
            )
            
            # Cleanup temp file locally
            if os.path.exists(batch_input_path):
                os.remove(batch_input_path)
            
            return {
                "status": "processing_background",
                "job_id": batch_job.name,
                "job_state": batch_job.state,
                "message": f"Successfully queued {len(uploaded_files)} pages. Job ID: {batch_job.name}. Please inform user and check status later."
            }
            
        except Exception as e:
            if os.path.exists(batch_input_path):
                os.remove(batch_input_path)
            return {"status": "error", "message": f"Batch API staging failed: {str(e)}"}

    def check_job_status(self, job_name: str) -> Dict[str, Any]:
        """Polls the API for the batch status."""
        try:
            job = self.client.batches.get(name=job_name)
            
            if job.state == "SUCCEEDED":
                # We can download the output file
                out_uri = job.output_uri
                # Typically we download the file associated with job.output_file... 
                # (Implementation depends on the exact syntax of the selected SDK version)
                return {
                    "status": "completed",
                    "output_uri": out_uri,
                    "message": "Job finished. Ready to parse results."
                }
            elif job.state == "FAILED":
                return {"status": "failed", "message": "The Background Batch Job Failed."}
            else:
                return {
                    "status": "processing", 
                    "state": job.state,
                    "message": f"Job is currently: {job.state}"
                }
                
        except Exception as e:
             return {"status": "error", "message": str(e)}
