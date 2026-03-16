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
        processor = BatchProcessor()
        result_meta = processor.check_job_status(input_data.job_id)
        status = result_meta.get("status")
        
        if status == "completed":
            os.makedirs(input_data.output_dir, exist_ok=True)
            extraction_result = processor.download_and_extract_results(
                input_data.job_id, 
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
