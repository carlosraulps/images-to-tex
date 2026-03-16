import json
import os
from pydantic import BaseModel, Field
from src.services.batch_processor import BatchProcessor

class CheckBatchStatusInput(BaseModel):
    job_id: str = Field(..., description="The Batch Job ID returned by the process_document tool.")
    output_format: str = Field(default="both", description="The desired extracted format: 'latex', 'markdown', or 'both'.")
    output_dir: str = Field(default="/Users/apple/Research/thesis/notes/latex", description="Where to save the extracted files.")

def check_batch_job(input_data: CheckBatchStatusInput) -> str:
    try:
        job_id = input_data.job_id
        
        if job_id.startswith("local-"):
            state_file = f"/Users/apple/Research/docs-to-code/{job_id}.json"
            if not os.path.exists(state_file):
                return json.dumps({"status": "processing_background", "message": "Background task is starting..."}, indent=2)
                
            with open(state_file, "r") as f:
                state = json.load(f)
                
            if state.get("status") in ["extracting_images", "uploading_images"]:
                status_msg = state.get("status")
                return json.dumps({"status": "processing_background", "message": f"Background task is currently: {status_msg}..."}, indent=2)
                
            if state.get("status") in ["failed", "error"]:
                return json.dumps(state, indent=2)
                
            real_job_id = state.get("job_id")
            if not real_job_id:
                return json.dumps({"status": "processing_background", "message": "Waiting for Gemini Batch API Job ID..."}, indent=2)
                
            job_id = real_job_id
            
        processor = BatchProcessor()
        result_meta = processor.check_job_status(job_id)
        status = result_meta.get("status")
        
        if status == "completed":
            os.makedirs(input_data.output_dir, exist_ok=True)
            extraction_result = processor.download_and_extract_results(
                job_id, 
                input_data.output_format, 
                input_data.output_dir
            )
            return json.dumps({
                "status": "success",
                "message": extraction_result
            }, indent=2)
            
        elif status == "processing":
            return json.dumps({
                "status": "processing",
                "message": result_meta.get("message")
            }, indent=2)
            
        else:
             return json.dumps(result_meta, indent=2)

    except Exception as e:
        return json.dumps({
            "error": "BatchCheckException",
            "details": str(e)
        }, indent=2)
